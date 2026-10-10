import json
import re
import time
from typing import Literal, Set
from langchain_core.messages import SystemMessage, HumanMessage, RemoveMessage, AIMessage, ToolMessage
from langchain_core.runnables import RunnableConfig
from langgraph.types import Command
from .graph_state import State, AgentState
from .schemas import IntentClassification, QueryAnalysis
from .prompts import *
from utils import estimate_context_tokens
from core.execution_logger import log_error
from core.trace import collector_from_config
from .tools import get_shared_reranker, rerank_top1_for
from config import BASE_TOKEN_THRESHOLD, CHILD_CHUNK_SEPARATOR, CONTEXT_POOL_CONVERGENCE_ENABLED, CONTEXT_POOL_TOP_K, DEFAULT_RETRIEVAL_K, ENABLE_CRITIQUE, MAIN_HISTORY_MESSAGES_TO_KEEP, SKIPPED_TOOL_MESSAGE, TOKEN_GROWTH_FACTOR

if MAIN_HISTORY_MESSAGES_TO_KEEP < 2:
    raise ValueError("MAIN_HISTORY_MESSAGES_TO_KEEP must be at least 2.")

PRE_ANSWER_HISTORY_MESSAGES_TO_KEEP = max(MAIN_HISTORY_MESSAGES_TO_KEEP - 1, 0)

def _is_plain_conversation_message(msg) -> bool:
    return (
        isinstance(msg, (HumanMessage, AIMessage))
        and not getattr(msg, "tool_calls", None)
        and not getattr(msg, "name", None)
    )

def _name_internal_message(message, name):
    """Tag a subgraph-only message so it is not treated as chat history."""
    return message.model_copy(update={"name": name})

def _retrieval_contexts(messages) -> list[str]:
    contexts = []
    ignored_prefixes = (
        "NO_RELEVANT_CHUNKS",
        "NO_PARENT_DOCUMENT",
        "RETRIEVAL_ERROR:",
        "PARENT_RETRIEVAL_ERROR:",
        SKIPPED_TOOL_MESSAGE,
    )
    for message in messages:
        if not isinstance(message, ToolMessage):
            continue
        content = str(message.content).strip()
        if content and not content.startswith(ignored_prefixes):
            parts = content.split(CHILD_CHUNK_SEPARATOR) if message.name == "search_child_chunks" else [content]
            contexts.extend(part for part in parts if part)
    return list(dict.fromkeys(contexts))

def _format_conversation(messages) -> str:
    lines = []
    for msg in messages:
        role = "User" if isinstance(msg, HumanMessage) else "Assistant"
        lines.append(f"{role}: {msg.content}")
    return "\n".join(lines)

def _remove_messages_not_in(messages, keep_ids):
    removals = []
    for msg in messages:
        msg_id = getattr(msg, "id", None)
        if isinstance(msg, SystemMessage) or not msg_id:
            continue
        if msg_id not in keep_ids:
            removals.append(RemoveMessage(id=msg_id))
    return removals

def _recent_conversation(messages, pending_query="") -> list:
    """Return recent context before the current user message.

    During clarification, exclude the unresolved query and the assistant's
    clarification request because they are represented explicitly.
    """
    plain_messages = [msg for msg in messages if _is_plain_conversation_message(msg)]
    recent_messages = plain_messages[:-1]

    if pending_query:
        for index in range(len(recent_messages) - 1, -1, -1):
            msg = recent_messages[index]
            if isinstance(msg, HumanMessage) and str(msg.content).strip() == pending_query:
                return recent_messages[:index]

    return recent_messages

def summarize_history(state: State, llm, config: RunnableConfig = None):
    messages = state.get("messages", [])
    updates = {"agent_answers": [{"__reset__": True}]}

    if not messages:
        return updates

    plain_messages = [msg for msg in messages if _is_plain_conversation_message(msg)]
    keep_count = PRE_ANSWER_HISTORY_MESSAGES_TO_KEEP
    messages_to_summarize = plain_messages[:-keep_count] if len(plain_messages) > keep_count else []
    keep_ids = {getattr(msg, "id", None) for msg in plain_messages[-keep_count:]}
    keep_ids.discard(None)

    removals = _remove_messages_not_in(messages, keep_ids)
    if removals:
        updates["messages"] = removals

    if not messages_to_summarize:
        return updates

    existing_summary = state.get("conversation_summary", "").strip()
    conversation = "Existing summary:\n"
    conversation += f"{existing_summary or '(none)'}\n\n"
    conversation += "New messages to merge into the summary:\n"
    conversation += _format_conversation(messages_to_summarize)

    summary_response = llm.invoke([
        SystemMessage(content=get_conversation_summary_prompt()),
        HumanMessage(content=conversation),
    ])
    updates["conversation_summary"] = summary_response.content.strip()
    return updates

def rewrite_query(state: State, llm, config: RunnableConfig = None):
    last_message = state["messages"][-1]
    current_query = str(last_message.content).strip()
    conversation_summary = state.get("conversation_summary", "").strip()
    pending_query = state.get("pendingQuery", "").strip()
    pending_clarifications = state.get("pendingClarifications", [])
    recent_messages = _recent_conversation(state["messages"], pending_query)

    context_parts = []
    if conversation_summary:
        context_parts.append(f"Conversation Summary:\n{conversation_summary}")
    if recent_messages:
        context_parts.append(f"Recent Conversation:\n{_format_conversation(recent_messages)}")

    if pending_query:
        clarifications = [*pending_clarifications, current_query]
        clarification_text = "\n".join(
            f"{index}. {value}" for index, value in enumerate(clarifications, start=1)
        )
        context_parts.append(
            f"Unresolved User Query:\n{pending_query}\n\n"
            f"User Clarifications:\n{clarification_text}"
        )
        original_query = f"{pending_query}\nClarifications:\n{clarification_text}"
    else:
        clarifications = []
        context_parts.append(f"User Query:\n{current_query}")
        original_query = current_query

    context_section = "\n\n".join(context_parts)
    collector = collector_from_config(config)
    llm_with_structure = llm.with_structured_output(QueryAnalysis)
    response = llm_with_structure.invoke([SystemMessage(content=get_rewrite_query_prompt()), HumanMessage(content=context_section)])
    if collector:
        collector.emit("rewrite", "rewritten", {
            "original": original_query,
            "rewritten": response.questions or [],
            "is_clear": bool(response.is_clear),
        })
    clarification_message_update = (
        [_name_internal_message(last_message, "clarification_response")]
        if pending_query else []
    )

    if response.questions and response.is_clear:
        return {
            "questionIsClear": True,
            "originalQuery": original_query,
            "pendingQuery": "",
            "pendingClarifications": [],
            "rewrittenQuestions": response.questions,
            "messages": clarification_message_update,
        }

    clarification = response.clarification_needed if response.clarification_needed and len(response.clarification_needed.strip()) > 10 else "I need more information to understand your question."
    return {
        "questionIsClear": False,
        "originalQuery": "",
        "pendingQuery": pending_query or current_query,
        "pendingClarifications": clarifications,
        "rewrittenQuestions": [],
        "messages": clarification_message_update + [
            AIMessage(content=clarification, name="clarification")
        ],
    }

def request_clarification(state: State, config: RunnableConfig = None):
    return {}

# --- Agent Nodes ---
def orchestrator(state: AgentState, llm_with_tools, config: RunnableConfig = None):
    context_summary = state.get("context_summary", "").strip()
    sys_msg = SystemMessage(content=get_orchestrator_prompt())
    summary_injection = (
        [HumanMessage(content=f"[COMPRESSED CONTEXT FROM PRIOR RESEARCH]\n\n{context_summary}")]
        if context_summary else []
    )
    if not state.get("messages"):
        human_msg = HumanMessage(content=state["question"], name="agent_question")
        force_search = HumanMessage(content="YOU MUST CALL 'search_child_chunks' AS THE FIRST STEP TO ANSWER THIS QUESTION.")
        _t = time.time()
        print(f"[{time.strftime('%H:%M:%S')}] orchestrator llm.invoke start (first turn)")
        response = llm_with_tools.invoke([sys_msg] + summary_injection + [human_msg, force_search])
        print(f"[{time.strftime('%H:%M:%S')}] orchestrator llm.invoke done ({time.time() - _t:.1f}s)")
        response = _name_internal_message(response, "agent_response")
        return {"messages": [human_msg, response], "tool_call_count": len(response.tool_calls or []), "iteration_count": 1}

    _t = time.time()
    print(f"[{time.strftime('%H:%M:%S')}] orchestrator llm.invoke start")
    response = llm_with_tools.invoke([sys_msg] + summary_injection + state["messages"])
    print(f"[{time.strftime('%H:%M:%S')}] orchestrator llm.invoke done ({time.time() - _t:.1f}s)")
    response = _name_internal_message(response, "agent_response")
    tool_calls = response.tool_calls if hasattr(response, "tool_calls") else []
    return {"messages": [response], "tool_call_count": len(tool_calls) if tool_calls else 0, "iteration_count": 1}

def fallback_response(state: AgentState, llm, config: RunnableConfig = None):
    # The budget-exceeded route arrives with unanswered tool_calls still
    # pending on the last AIMessage. Answer them with synthetic ToolMessages
    # so the history written back to state stays valid for the API when
    # critique later replays this conversation through the orchestrator.
    skipped_tools = []
    for tool_call in (getattr(state["messages"][-1], "tool_calls", None) or []):
        skipped_tools.append(ToolMessage(
            content=SKIPPED_TOOL_MESSAGE,
            tool_call_id=tool_call["id"],
            name=tool_call["name"],
        ))

    seen = set()
    unique_contents = []
    for m in state["messages"]:
        if isinstance(m, ToolMessage) and m.content not in seen:
            unique_contents.append(m.content)
            seen.add(m.content)

    context_summary = state.get("context_summary", "").strip()

    context_parts = []
    if context_summary:
        context_parts.append(f"## Compressed Research Context (from prior iterations)\n\n{context_summary}")
    if unique_contents:
        context_parts.append(
            "## Retrieved Data (current iteration)\n\n" +
            "\n\n".join(f"--- DATA SOURCE {i} ---\n{content}" for i, content in enumerate(unique_contents, 1))
        )

    context_text = "\n\n".join(context_parts) if context_parts else "No data was retrieved from the documents."

    prompt_content = (
        f"USER QUERY: {state.get('question')}\n\n"
        f"{context_text}\n\n"
        f"INSTRUCTION:\nProvide the best possible answer using only the data above."
    )
    response = llm.invoke([SystemMessage(content=get_fallback_response_prompt()), HumanMessage(content=prompt_content)])
    response = _name_internal_message(response, "agent_response")
    return {"messages": skipped_tools + [response]}

def should_compress_context(state: AgentState, config: RunnableConfig = None) -> Command[Literal["compress_context", "orchestrator"]]:
    messages = state["messages"]

    new_ids: Set[str] = set()
    for msg in reversed(messages):
        if isinstance(msg, AIMessage) and getattr(msg, "tool_calls", None):
            for tc in msg.tool_calls:
                if tc["name"] == "retrieve_parent_chunks":
                    raw = tc["args"].get("parent_id") or tc["args"].get("id") or tc["args"].get("ids") or []
                    if isinstance(raw, str):
                        new_ids.add(f"parent::{raw}")
                    else:
                        new_ids.update(f"parent::{r}" for r in raw)

                elif tc["name"] == "search_child_chunks":
                    query = tc["args"].get("query", "")
                    if query:
                        new_ids.add(f"search::{query}")
            break

    updated_ids = state.get("retrieval_keys", set()) | new_ids

    current_token_messages = estimate_context_tokens(messages)
    current_token_summary = estimate_context_tokens([HumanMessage(content=state.get("context_summary", ""))])
    current_tokens = current_token_messages + current_token_summary

    max_allowed = BASE_TOKEN_THRESHOLD + int(current_token_summary * TOKEN_GROWTH_FACTOR)

    goto = "compress_context" if current_tokens > max_allowed else "orchestrator"
    return Command(
        update={
            "retrieval_keys": updated_ids,
            "retrieved_contexts": _retrieval_contexts(messages),
        },
        goto=goto,
    )

def compress_context(state: AgentState, llm, config: RunnableConfig = None):
    messages = state["messages"]
    existing_summary = state.get("context_summary", "").strip()

    if not messages:
        return {}

    conversation_text = f"USER QUESTION:\n{state.get('question')}\n\nConversation to compress:\n\n"
    if existing_summary:
        conversation_text += f"[PRIOR COMPRESSED CONTEXT]\n{existing_summary}\n\n"

    for msg in messages[1:]:
        if isinstance(msg, AIMessage):
            tool_calls_info = ""
            if getattr(msg, "tool_calls", None):
                calls = ", ".join(f"{tc['name']}({tc['args']})" for tc in msg.tool_calls)
                tool_calls_info = f" | Tool calls: {calls}"
            conversation_text += f"[ASSISTANT{tool_calls_info}]\n{msg.content or '(tool call only)'}\n\n"
        elif isinstance(msg, ToolMessage):
            tool_name = getattr(msg, "name", "tool")
            conversation_text += f"[TOOL RESULT — {tool_name}]\n{msg.content}\n\n"

    summary_response = llm.invoke([SystemMessage(content=get_context_compression_prompt()), HumanMessage(content=conversation_text)])
    new_summary = summary_response.content

    retrieved_ids: Set[str] = state.get("retrieval_keys", set())
    if retrieved_ids:
        parent_ids = sorted(r for r in retrieved_ids if r.startswith("parent::"))
        search_queries = sorted(r.replace("search::", "") for r in retrieved_ids if r.startswith("search::"))

        block = "\n\n---\n**Already executed (do NOT repeat):**\n"
        if parent_ids:
            block += "Parent chunks retrieved:\n" + "\n".join(f"- {p.replace('parent::', '')}" for p in parent_ids) + "\n"
        if search_queries:
            block += "Search queries already run:\n" + "\n".join(f"- {q}" for q in search_queries) + "\n"
        new_summary += block

    return {"context_summary": new_summary, "messages": [RemoveMessage(id=m.id) for m in messages[1:]]}

_CTX_PARSE_RE = re.compile(r"Parent ID:\s*(.+?)\nFile Name:\s*(.+?)\nContent:\s*(.*)", re.DOTALL)


def _converge_context_pool(contexts, question, collector=None):
    """对累计 contexts 池做二次精排：rerank 重打分 → Parent 去重(每 parent 最高分 1 个) → top-k。

    返回收敛后的 context 文本列表（保持原始 "Parent ID/File Name/Content" 格式）。
    reranker 不可用或池为空时原样返回。
    """
    if not contexts:
        return contexts
    entries, seen = [], set()
    for c in contexts:
        m = _CTX_PARSE_RE.match(c)
        pid = m.group(1).strip() if m else ""
        content = m.group(3).strip() if m else c
        key = (pid, content)
        if key in seen:
            continue
        seen.add(key)
        entries.append({"parent_id": pid, "content": content, "raw": c})
    dropped_duplicate = len(contexts) - len(entries)

    reranker = get_shared_reranker()
    if reranker and question and entries:
        try:
            scores = reranker.compute_score([(question, e["content"]) for e in entries], batch_size=8)
            if not isinstance(scores, list):
                scores = [scores]
            for e, s in zip(entries, scores):
                e["score"] = float(s)
            entries.sort(key=lambda e: e["score"], reverse=True)
        except Exception as e:
            log_error("pool_convergence/rerank", e)

    seen_parents, kept = set(), []
    for e in entries:
        pid = e["parent_id"]
        if pid and pid in seen_parents:
            continue
        if pid:
            seen_parents.add(pid)
        kept.append(e)
    dropped_parent = len(entries) - len(kept)
    truncated = max(0, len(kept) - CONTEXT_POOL_TOP_K)
    kept = kept[:CONTEXT_POOL_TOP_K]

    if collector:
        collector.emit("retrieval", "pool_convergence", {
            "before": len(contexts), "after": len(kept),
            "dropped_duplicate": dropped_duplicate, "dropped_parent": dropped_parent,
            "truncated": truncated,
        })
    return [e["raw"] for e in kept]


def collect_answer(state: AgentState, config: RunnableConfig = None):
    last_message = state["messages"][-1]
    is_valid = isinstance(last_message, AIMessage) and last_message.content and not last_message.tool_calls
    answer = last_message.content if is_valid else "Unable to generate an answer."
    return {
        "final_answer": answer,
        "agent_answers": [{
            "index": state["question_index"],
            "question": state["question"],
            "answer": answer,
            "contexts": _converge_context_pool(
                state.get("retrieved_contexts", []),
                state.get("question", ""),
                collector_from_config(config)) if CONTEXT_POOL_CONVERGENCE_ENABLED
                else state.get("retrieved_contexts", []),
        }]
    }

def _extract_json(text):
    match = re.search(r"\{.*\}", text, re.DOTALL)
    if not match:
        return None
    try:
        return json.loads(match.group())
    except Exception:
        return None

def critique_node(state: AgentState, llm, config: RunnableConfig = None):
    """Generation-layer self-reflection over the drafted answer.

    Runs two LLM checks: IsSup (every factual claim is supported by the
    retrieved contexts) and IsUse (the answer actually addresses the question).
    On a failed check with retry budget left, injects a feedback message for
    the orchestrator; route_after_critique decides between retry and accept.
    Any critic-side failure (LLM error, unparsable JSON) passes the answer
    through unchanged so a broken critic never discards a valid answer.
    """
    if not ENABLE_CRITIQUE:
        return {"critique_result": {"is_sup": True, "is_use": True, "reason": "disabled",
                                    "unsupported_claims": []},
                "critique_retry_count": 0}
    answer = state.get("final_answer", "")
    question = state.get("question", "")
    contexts = state.get("retrieved_contexts", [])
    retry_count = state.get("critique_retry_count", 0)
    print(f"[{time.strftime('%H:%M:%S')}] critique retry_count: {retry_count} -> {retry_count + 1}")
    collector = collector_from_config(config)

    # Budget-exhausted fallback path: the skipped-tool ToolMessage immediately
    # before the fallback answer marks a turn with no retrieval budget left,
    # so a failed critique would have nothing to retry with. Pass it through
    # without running the two LLM checks.
    messages = state.get("messages", [])
    if (
        len(messages) >= 2
        and isinstance(messages[-1], AIMessage)
        and getattr(messages[-1], "name", None) == "agent_response"
        and isinstance(messages[-2], ToolMessage)
        and messages[-2].content.startswith(SKIPPED_TOOL_MESSAGE)
    ):
        if collector:
            collector.emit("critique", "verdict", {
                "is_sup": True, "is_use": True, "retry_count": retry_count + 1,
                "unsupported_claims": [], "reason": "skipped after fallback",
                "action": "skipped_after_fallback",
            })
        return {
            "critique_result": {
                "is_sup": True,
                "is_use": True,
                "unsupported_claims": [],
                "reason": "skipped after fallback",
            },
            "critique_retry_count": retry_count + 1,
        }

    # 优化 1：短答案 + 高检索置信度 → 跳过 critique（边际价值低、token 成本高）
    top1 = rerank_top1_for(config)
    if len(answer) < 200 and top1 is not None and top1 > 0.7:
        if collector:
            collector.emit("critique", "verdict", {
                "is_sup": True, "is_use": True, "retry_count": retry_count + 1,
                "unsupported_claims": [], "reason": "skipped_low_risk",
                "action": "skipped_low_risk",
            })
        return {
            "critique_result": {"is_sup": True, "is_use": True, "unsupported_claims": [],
                                "reason": "skipped_low_risk"},
            "critique_retry_count": retry_count + 1,
        }

    critique_result = {"is_sup": True, "is_use": True, "unsupported_claims": [], "reason": ""}
    try:
        contexts_text = "\n\n".join(
            f"--- CONTEXT {i} ---\n{context}" for i, context in enumerate(contexts, start=1)
        ) or "(no retrieved contexts)"

        sup_response = llm.invoke([
            SystemMessage(content=get_critique_sup_prompt()),
            HumanMessage(content=f"USER QUESTION:\n{question}\n\nDRAFTED ANSWER:\n{answer}\n\nRETRIEVED CONTEXTS:\n{contexts_text}"),
        ])
        sup_data = _extract_json(sup_response.content) or {}
        claims = sup_data.get("unsupported_claims", [])
        critique_result["is_sup"] = bool(sup_data.get("is_sup", True))
        critique_result["unsupported_claims"] = [str(claim) for claim in claims] if isinstance(claims, list) else []
        sup_reason = str(sup_data.get("reason", "") or "")

        use_response = llm.invoke([
            SystemMessage(content=get_critique_use_prompt()),
            HumanMessage(content=f"USER QUESTION:\n{question}\n\nDRAFTED ANSWER:\n{answer}"),
        ])
        use_data = _extract_json(use_response.content) or {}
        critique_result["is_use"] = bool(use_data.get("is_use", True))
        use_reason = str(use_data.get("reason", "") or "")
    except Exception:
        return {
            "critique_result": critique_result,
            "critique_retry_count": retry_count + 1,
        }

    critique_result["reason"] = "\n".join(reason for reason in (sup_reason, use_reason) if reason.strip())

    updates = {
        "critique_result": critique_result,
        "critique_retry_count": retry_count + 1,
    }
    will_retry = (len(critique_result["unsupported_claims"]) >= 2
                  or critique_result["is_sup"] is False) and retry_count < 1
    if will_retry:
        reason_text = critique_result["reason"] or "answer quality check failed"
        updates["messages"] = [HumanMessage(
            content=f"[CRITIQUE FEEDBACK] 你的答案存在以下问题：{reason_text}。请基于已有的 retrieved_contexts 补充检索或修正答案。",
            name="critique_feedback",
        )]
    if collector:
        collector.emit("critique", "verdict", {
            "is_sup": critique_result["is_sup"],
            "is_use": critique_result["is_use"],
            "retry_count": retry_count + 1,
            "unsupported_claims": critique_result["unsupported_claims"],
            "reason": critique_result["reason"],
            "action": "retry_injected" if will_retry else "accepted",
        })
    return updates
# --- End of Agent Nodes---

# --- Main Graph: Intent Routing ---

VALID_INTENTS = {"simple_faq", "single_hop", "multi_hop"}
DEFAULT_INTENT = "single_hop"

def intent_router(state: State, llm, config: RunnableConfig = None):
    """Turn-level intent classification before query understanding.

    Clarification follow-ups bypass classification: a short reply like
    "5.2.3" would be misclassified as a research question, so the previous
    turn's intent is kept until the clarification resolves.
    """
    last_message = state["messages"][-1]
    current_query = str(last_message.content).strip()

    if state.get("pendingQuery", "").strip():
        return {"intent": state.get("intent") or DEFAULT_INTENT}

    context_parts = []
    summary = state.get("conversation_summary", "").strip()
    if summary:
        context_parts.append(f"Conversation Summary:\n{summary}")
    recent_messages = _recent_conversation(state["messages"])
    if recent_messages:
        context_parts.append(f"Recent Conversation:\n{_format_conversation(recent_messages)}")
    context_parts.append(f"User Message:\n{current_query}")

    collector = collector_from_config(config)
    t0 = time.perf_counter()
    response = llm.with_structured_output(IntentClassification).invoke([
        SystemMessage(content=get_intent_router_prompt()),
        HumanMessage(content="\n\n".join(context_parts)),
    ])
    intent = response.intent if response and response.intent in VALID_INTENTS else DEFAULT_INTENT
    print(f"[INTENT] {intent}")
    if collector:
        collector.intent_classified(intent, (time.perf_counter() - t0) * 1000)
    return {"intent": intent}

def faq_answer(state: State, llm, dense_collection, config: RunnableConfig = None):
    """One-shot dense-only retrieval for simple FAQ intents: no BM25 and no
    reranker by construction. Rewriting is skipped (the raw question is
    specific enough by definition), and the result joins aggregate_answers
    like every other path."""
    if dense_collection is None:
        log_error("faq_answer", RuntimeError("dense collection view is not configured"))
        return {"messages": [AIMessage(content="The FAQ fast path is not configured in this deployment.")]}

    question = str(state["messages"][-1].content).strip()
    scored = dense_collection.similarity_search_with_score(question, k=DEFAULT_RETRIEVAL_K)
    if collector := collector_from_config(config):
        collector.emit("retrieval", "candidates", {
            "query": question, "mode": "dense", "count": len(scored),
            "candidates": [{"rank": i, "point_id": d.metadata.get("_id") or f"noid_{i}",
                            "parent_id": d.metadata.get("parent_id", ""),
                            "source": d.metadata.get("source", ""),
                            "fused_score": round(float(s), 4),
                            "preview": str(d.page_content)[:250]}
                           for i, (d, s) in enumerate(scored)]})
    contexts = [d.page_content for d, _ in scored]
    if not contexts:
        answer = "I couldn't find any information to answer your question in the available sources."
    else:
        context_text = "\n\n".join(
            f"--- CONTEXT {i} ---\nParent ID: {d.metadata.get('parent_id', '')}\nContent: {d.page_content}"
            for i, (d, _) in enumerate(scored, start=1)
        )
        response = llm.invoke([
            SystemMessage(content=get_faq_answer_prompt()),
            HumanMessage(content=f"USER QUERY:\n{question}\n\nRETRIEVED CONTEXTS:\n{context_text}"),
        ])
        answer = response.content
    return {
        "agent_answers": [{"index": 0, "question": question, "answer": answer, "contexts": contexts}],
        "messages": [AIMessage(content=answer)],
    }

_CITATION_RE = re.compile(r"\[[A-Za-z0-9\.\-]+_p\d+\]")


def _citation_coverage(answer: str):
    """事实性句子的引用覆盖率。返回 (coverage, covered, total)。

    排除 Sources 段与短句，按句号/换行切分，>=15 字符的句子计为事实性句子。
    """
    main = re.split(r"(?i)\n\s*Sources:", answer)[0]
    # 英文标点后必须跟空白才切分——否则 "2401.18059" 里的点号会切开引用标记
    sentences = [s.strip() for s in re.split(r"(?<=[。！？])\s*|(?<=[.!?])\s+|\n+", main) if len(s.strip()) >= 15]
    if not sentences:
        return 1.0, 0, 0
    covered = sum(1 for s in sentences if _CITATION_RE.search(s))
    return covered / len(sentences), covered, len(sentences)


def aggregate_answers(state: State, llm, config: RunnableConfig = None):
    collector = collector_from_config(config)
    messages = state.get("messages", [])
    plain_messages = [msg for msg in messages if _is_plain_conversation_message(msg)]
    keep_ids = {getattr(msg, "id", None) for msg in plain_messages[-PRE_ANSWER_HISTORY_MESSAGES_TO_KEEP:]}
    keep_ids.discard(None)
    removals = _remove_messages_not_in(messages, keep_ids)

    if not state.get("agent_answers"):
        return {"messages": removals + [AIMessage(content="No answers were generated.")]}

    # Critique retries make collect_answer emit one entry per attempt for the
    # same index; keep only the newest entry per index before synthesis.
    grouped_answers = {}
    for ans in state["agent_answers"]:
        grouped_answers[ans["index"]] = ans
    sorted_answers = [grouped_answers[idx] for idx in sorted(grouped_answers)]

    formatted_answers = ""
    for i, ans in enumerate(sorted_answers, start=1):
        formatted_answers += (f"\nRetrieved response {i}:\n"f"{ans['answer']}\n")

    user_message = HumanMessage(content=f"""Original user question: {state.get("originalQuery", "")}\nRetrieved answers:{formatted_answers}""")
    synthesis_response = llm.invoke([SystemMessage(content=get_aggregation_prompt()), user_message])
    answer = synthesis_response.content

    # 优化 1：引用覆盖率后处理——>30% 事实句无 [chunk_id] 时重试一次，仍不达标加标注
    _refusal = any(h in answer.lower() for h in
                   ("couldn't find", "could not find", "no information", "no relevant",
                    "未找到", "没有找到", "无法找到", "未收录", "不包含", "未发现"))
    coverage, covered, total = (1.0, 0, 0) if _refusal else _citation_coverage(answer)
    citation_retried = False
    if total > 0 and coverage < 0.7:
        citation_retried = True
        retry_resp = llm.invoke([
            SystemMessage(content=get_aggregation_prompt()),
            HumanMessage(content=(
                f"Original user question: {state.get('originalQuery', '')}\n"
                f"Retrieved answers:\n{formatted_answers}\n\n"
                f"Your previous attempt had {total - covered}/{total} factual sentences without "
                f"a [chunk_id] citation marker. Regenerate the answer. Every factual statement "
                f"must carry a [chunk_id] citation (the chunk's Parent ID, e.g., [2401.18059_p11]); "
                f"delete any statement you cannot attribute to a chunk. "
                f"Previous attempt:\n{answer}")),
        ])
        answer = retry_resp.content
        coverage, covered, total = _citation_coverage(answer)
        if total > 0 and coverage < 0.7:
            answer = answer.rstrip() + "\n\n（部分内容未找到直接证据）"

    if collector:
        cited_sources, in_sources = [], False
        for line in answer.splitlines():
            stripped = line.strip()
            if stripped.lower() == "sources:":
                in_sources = True
                continue
            if in_sources:
                if stripped.startswith("- "):
                    cited_sources.append(stripped[2:].strip())
                elif stripped:
                    in_sources = False
        collector.emit("answer", "final_answer", {
            "answer": answer, "cited_sources": cited_sources,
            "citation_coverage": round(coverage, 3), "citation_retried": citation_retried,
        })
    return {"messages": removals + [AIMessage(content=answer)]}
