# Golden Dataset 审核清单（草稿）

生成时间: 2026-10-06T20:09:46 | 正式集 100 条 | 备选 27 条
逐条核对: 问题 / 证据 / 答案 三点对读

## spf-001 [single_paper_factual] intent=simple_faq verify=✗ The evidence states the two causes (struggle with factual errors and inability to secure accuracy from parametric knowledge alone), but it does not contain the illustrative example about a low-quality retriever introducing irrelevant information, so that part of the ground truth is unsupported.
- **Q**: According to the passage, why do large language models inevitably manifest hallucinations?
- **证据1**: Nevertheless, LLMs inevitably manifest hallucinations (Ji et al., 2023) due to their struggle with factual errors (Mallen et al., 2023; Min et al., 2023) and inability to secure the accuracy of generated texts solely by the parametric knowledge they encapsulate (Zhang et al., 2023b; Muhlgay et al., 2023).
- **GT**: LLMs inevitably manifest hallucinations due to their struggle with factual errors and their inability to secure the accuracy of generated texts solely by the parametric knowledge they encapsulate. This is illustrated by examples where a low-quality retriever introduces irrelevant information that impedes generators from acquiring accurate knowledge.
- 来源: 2401.15884 | 备注: 

## spf-002 [single_paper_factual] intent=single_hop verify=✓
- **Q**: Atlas 在 Natural Questions 上仅用 64 个示例达到了多少准确率？
- **证据1**: Notably, Atlas reaches over 42% accuracy on Natural Questions using only 64 examples, outperforming a 540B parameters model by 3% despite having 50x fewer parameters.
- **GT**: Atlas 在 Natural Questions 上仅用 64 个示例就达到了超过 42% 的准确率。它比一个 540B 参数的模型高出 3%，尽管其参数量少了 50 倍。
- 来源: 2208.03299 | 备注: 

## spf-003 [single_paper_factual] intent=simple_faq verify=✓
- **Q**: E5 是什么？它是如何训练的？
- **证据1**: This paper presents E5<sup>1</sup> , a family of state-of-the-art text embeddings that transfer well to a wide range of tasks. The model is trained in a contrastive manner with weak supervision signals from our curated large-scale text pair dataset (called CCPairs). E5 can be readily used as a general-purpose embedding model for any tasks requiring a single-vector representation of texts such as r
- **GT**: E5 是一个在广泛任务上迁移效果良好的最先进文本嵌入模型家族。它采用对比学习方式训练，弱监督信号来自作者整理的大规模文本对数据集 CCPairs。E5 可直接作为通用嵌入模型用于检索、聚类和分类等需要文本单向量表示的任务。
- 来源: 2212.03533 | 备注: 

## spf-004 [single_paper_factual] intent=single_hop verify=✓
- **Q**: LightRAG 通过什么方式提升信息检索的效率与理解能力？
- **证据1**: This work introduces an advancement in Retrieval-Augmented Generation (RAG) through the integration of a graph-based indexing approach that enhances both efficiency and comprehension in information retrieval. LightRAG utilizes a comprehensive knowledge graph to facilitate rapid and relevant document retrieval, enabling a deeper understanding of complex queries. Its dual-level retrieval paradigm al
- **GT**: LightRAG 通过整合基于图的索引方法来提升信息检索的效率与理解能力。它利用一个全面的知识图谱来促进快速且相关的文档检索，从而能够更深入地理解复杂查询。其双层检索范式可以同时提取具体信息和抽象信息，以满足多样化的用户需求。
- 来源: 2410.05779 | 备注: 

## spf-005 [single_paper_factual] intent=single_hop verify=✗ 证据仅支持"超过100种工作语言的语义检索统一支持"，未提及稠密检索、多向量检索和稀疏检索三种功能，故ground truth部分内容无证据支撑。
- **Q**: M3-Embedding 支持多少种工作语言的语义检索？
- **证据1**: It provides a uniform support for the semantic retrieval of more than 100 working languages.
- **GT**: M3-Embedding 为超过 100 种工作语言的语义检索提供统一支持。它同时还能完成稠密检索、多向量检索和稀疏检索三种常见检索功能。
- 来源: 2402.03216 | 备注: 

## spf-006 [single_paper_factual] intent=simple_faq verify=✗ 证据仅说明 RAPTOR 是树基检索系统、通过递归聚类和摘要构建层次树，但未提及“在查询阶段利用该树结构进行更有效的检索”这一事实。
- **Q**: RAPTOR 是什么？它如何构建层次化的树结构？
- **证据1**: In this paper, we have presented RAPTOR, a novel tree-based retrieval system that augments the parametric knowledge of large language models with contextual information at various levels of abstraction. By employing recursive clustering and summarization techniques, RAPTOR creates a hierarchical tree structure that is capable of synthesizing information across various sections of the retrieval cor
- **GT**: RAPTOR 是一种新颖的基于树的检索系统，它用不同抽象层级的上下文信息来增强大语言模型的参数化知识。它通过递归的聚类和摘要技术，构建出一个能够跨检索语料库各个部分综合信息的层次化树结构。在查询阶段，RAPTOR 利用该树结构进行更有效的检索。
- 来源: 2401.18059 | 备注: 

## spf-007 [single_paper_factual] intent=simple_faq verify=✓
- **Q**: REALM 如何增强语言模型预训练？
- **证据1**: REALM augments language model pre-training with a neural knowledge retriever that retrieves knowledge from a textual knowledge corpus, Z (e.g., all of Wikipedia). Signal from the language modeling objective backpropagates all the way through the retriever, which must consider millions of documents in Z—a significant computational challenge that we address.
- **GT**: REALM 用一个神经知识检索器来增强语言模型预训练，该检索器从文本知识语料库 Z（例如整个 Wikipedia）中检索知识。语言建模目标的信号会一直反向传播穿过检索器，而检索器必须考虑 Z 中的数百万篇文档，这是一个显著的计算挑战。
- 来源: 2002.08909 | 备注: 

## spf-008 [single_paper_factual] intent=simple_faq verify=✗ 证据仅描述了 ReAct 的交错推理-动作范式及其作用，未提及该方法在语言理解和交互式决策任务上优于单纯推理或单纯行动基线的实验结果，故该部分事实缺乏证据支持。
- **Q**: ReAct 这篇论文的核心思想是什么？
- **证据1**: We explore the use of large language models (LLMs) to generate both reasoning traces and task-specific actions in an interleaved manner, allowing for greater synergy between the two: reasoning traces help the model induce, track, and update action plans as well as handle exceptions, while actions allow it to interface with external sources, such as knowledge bases or environments, to gather additi
- **GT**: ReAct 提出了一种让语言模型在交错进行的推理轨迹与任务特定动作之间协同工作的通用范式。在该范式中，推理轨迹帮助模型归纳、追踪和更新行动计划，并处理异常情况；而动作则使模型能够与外部环境（如知识库或环境）交互并收集额外信息。该方法在语言理解和交互式决策任务上都取得了优于单纯推理或单纯行动基线的效果。
- 来源: 2210.03629 | 备注: 

## spf-009 [single_paper_factual] intent=simple_faq verify=✗ 证据仅提到 SELF-RAG 通过检索和自我反思提升质量与事实性，未提及反思令牌、自适应按需检索或自我批判等具体机制。
- **Q**: SELF-RAG 通过什么方式提升大语言模型的事实准确性？
- **证据1**: We introduce Self-Reflective Retrieval-Augmented Generation (SELF-RAG) that enhances an LM's quality and factuality through retrieval and self-reflection.
- **GT**: SELF-RAG 是一个通过自我反思来学习检索、生成和批判的框架。它通过反思令牌（reflection tokens）提升大语言模型的事实准确性，这些令牌使模型能够自适应地按需检索，并对其自身生成内容进行自我批判。
- 来源: 2310.11511 | 备注: 

## spf-010 [single_paper_factual] intent=simple_faq verify=✓
- **Q**: SELF-REFINE 是什么？它的主要思想是什么？
- **证据1**: Motivated by how humans refine their written text, we introduce SELF-REFINE, an approach for improving initial outputs from LLMs through iterative feedback and refinement. The main idea is to generate an initial output using an LLM; then, the same LLM provides _feedback_ for its output and uses it to _refine_ itself, iteratively. SELF-REFINE does not require any supervised training data, additiona
- **GT**: SELF-REFINE 是一种通过迭代反馈与改进来提升大语言模型初始输出的方法。其核心思想是先用 LLM 生成一个初始输出，然后由同一个 LLM 为其输出提供反馈，并据此迭代地改进自身。它不需要任何监督训练数据、额外训练或强化学习，而是使用单个 LLM 同时充当生成器、改进器和反馈提供者。
- 来源: 2303.17651 | 备注: 

## spf-011 [single_paper_factual] intent=simple_faq verify=✓
- **Q**: Toolformer 是什么？它是如何训练的？
- **证据1**: We introduce _Toolformer_ , a model trained to decide which APIs to call, when to call them, what arguments to pass, and how to best incorporate the results into future token prediction. This is done in a self-supervised way, requiring nothing more than a handful of demonstrations for each API.
- **GT**: Toolformer 是一个被训练来决定调用哪些 API、何时调用、传递什么参数，以及如何最好地将结果纳入未来 token 预测的模型。它的训练以自监督方式进行，每个 API 只需要少量演示。
- 来源: 2302.04761 | 备注: 

## spf-012 [single_paper_factual] intent=simple_faq verify=✗ The evidence only states the first sentence of the ground truth; the additional claim about expanding LLM utility and serving as intermediaries between users and applications is not present in the evidence.
- **Q**: What does tool learning aim to do according to the paper's introduction?
- **证据1**: Tool learning (Qin et al., 2023b) aims to unleash the power of large language models (LLMs) to effectively interact with various tools (APIs) to accomplish complex tasks.
- **GT**: Tool learning aims to unleash the power of large language models (LLMs) to effectively interact with various tools (APIs) to accomplish complex tasks. By integrating LLMs with APIs, their utility can be greatly expanded, empowering them to serve as efficient intermediaries between users and the vast ecosystem of applications.
- 来源: 2307.16789 | 备注: 

## spf-013 [single_paper_factual] intent=simple_faq verify=✓
- **Q**: What is RAG-Fusion and how does it work?
- **证据1**: RAG-Fusion combines RAG and reciprocal rank fusion (RRF) by generating multiple queries, reranking them with reciprocal scores and fusing the documents and scores.
- **GT**: RAG-Fusion is a method that combines RAG and reciprocal rank fusion (RRF). It works by generating multiple queries, reranking them with reciprocal scores, and fusing the documents and scores.
- 来源: 2402.03367 | 备注: 

## spf-014 [single_paper_factual] intent=simple_faq verify=✓
- **Q**: What is dense retrieval, and what methods have been proposed to improve the effectiveness of supervised dense retrieval models?
- **证据1**: Dense retrieval (Lee et al., 2019; Karpukhin et al., 2020), the method of retrieving documents using semantic embedding similarities, has been shown successful across tasks like web search, question answering, and fact verification. A variety of methods such as negative mining (Xiong et al., 2021; Qu et al., 2021), distillation (Qu et al., 2021; Lin et al., 2021b; Hofstätter et al., 2021) and task
- **GT**: Dense retrieval is the method of retrieving documents using semantic embedding similarities, and it has been shown successful across tasks like web search, question answering, and fact verification. To improve the effectiveness of supervised dense retrieval models, a variety of methods have been proposed, such as negative mining, distillation, and task-specific pre-training.
- 来源: 2212.10496 | 备注: 

## spf-015 [single_paper_factual] intent=simple_faq verify=✗ 证据仅说明了 query2doc 的定义与生成伪文档扩展查询的机制，未包含关于 MSMARCO/TREC DL 数据集上 BM25 性能提升 3% 到 15% 且无需微调的实验结果，故该部分事实无证据支撑。
- **Q**: query2doc 是什么？它是如何提升检索系统性能的？
- **证据1**: This paper introduces a simple yet effective query expansion approach, denoted as _query2doc_ , to improve both sparse and dense retrieval systems. The proposed method first generates pseudo-documents by few-shot prompting large language models (LLMs), and then expands the query with generated pseudodocuments.
- **GT**: query2doc 是一种简单而有效的查询扩展方法，用于改进稀疏和稠密检索系统。它首先通过少样本提示大语言模型（LLMs）生成伪文档，然后用生成的伪文档扩展查询。实验结果表明，query2doc 在 MSMARCO 和 TREC DL 等 ad-hoc IR 数据集上无需任何模型微调即可将 BM25 的性能提升 3% 到 15%。
- 来源: 2303.07678 | 备注: 

## spf-016 [single_paper_factual] intent=simple_faq verify=✓
- **Q**: 开放域问答（Open-domain QA）的两阶段框架由哪两个部分组成？
- **证据1**: a much simplified two-stage framework: (1) a context _retriever_ first selects a small subset of passages where some of them contain the answer to the question, and then (2) a machine _reader_ can thoroughly examine the retrieved contexts and identify the correct answer
- **GT**: 开放域问答采用简化的两阶段框架：第一阶段是上下文检索器（retriever），它先选出少量可能包含答案的段落；第二阶段是机器阅读器（reader），它仔细检查检索到的上下文并找出正确答案。
- 来源: 2004.04906 | 备注: 

## spf-017 [single_paper_factual] intent=simple_faq verify=✗ 证据仅支持“现代Agent = LLM + 上下文 + 工具”，未包含“LLM是大脑、上下文是眼睛、工具是手脚”等比喻性说明。
- **Q**: 根据本书目录，现代 Agent 由哪几部分组成？
- **证据1**: 1.1 现代Agent = LLM + 上下文+ 工具
- **GT**: 根据本书第1章的目录，现代Agent = LLM + 上下文 + 工具。其中 LLM 是 Agent 的大脑，上下文是 Agent 的眼睛，工具是 Agent 的手脚。
- 来源: AI-Agents-in-Depth-zh-CN | 备注: 

## spf-018 [single_paper_factual] intent=single_hop verify=✓
- **Q**: 论文中关于潜在负面社会影响的讨论是如何回应的？
- **证据1**: (c) Did you discuss any potential negative societal impacts of your work? [N/A] Our work does not have any additional negative societal impact on top of the existing impact of representation learning. However, a study on the trade-off between representation size and the tendency to encode biases is an interesting future direction along the lines of existing literature [36, 37]. A part of this is a
- **GT**: 作者表示其工作不会在表征学习现有影响之外产生额外的负面社会影响，因此该项标记为 [N/A]。不过作者指出，研究表征大小与编码偏见倾向之间的权衡是一个有趣的未来方向，并说明其中一部分已在第 5 节中呈现。
- 来源: 2205.13147 | 备注: 

## spf-019 [single_paper_factual] intent=single_hop verify=✗ 证据仅提及综述涵盖 Naive RAG、Advanced RAG 和 Modular RAG 三种范式，未提及“检索、生成与增强技术”这一三方基础，故 ground truth 中该部分无证据支撑。
- **Q**: 这篇综述论文考察了哪些 RAG 范式？
- **证据1**: This comprehensive review paper offers a detailed examination of the progression of RAG paradigms, encompassing the Naive RAG, the Advanced RAG, and the Modular RAG.
- **GT**: 这篇综述论文详细考察了 RAG 范式的发展进程，涵盖 Naive RAG、Advanced RAG 和 Modular RAG 三种范式。此外，论文还细致审视了 RAG 框架的三方基础，即检索、生成与增强技术。
- 来源: 2312.10997 | 备注: 

## spf-020 [single_paper_factual] intent=single_hop verify=✗ 证据仅说明所有作者来自 DeepMind 并存在同等贡献/同等资深作者标注，但未列出具体作者姓名，无法支撑 ground truth 中关于 Sebastian Borgeaud、Arthur Mensch、Jordan Hoffmann、Laurent Sifre、Jack W. Rae、Erich Elsen 的具体标注信息。
- **Q**: 这篇论文《Improving language models by retrieving from trillions of tokens》的作者来自哪个机构？
- **证据1**: All authors from DeepMind,<sup>†</sup> Equal contributions,<sup>‡</sup> Equal senior authorship
- **GT**: 这篇论文的所有作者均来自 DeepMind。其中 Sebastian Borgeaud、Arthur Mensch、Jordan Hoffmann 和 Laurent Sifre 标注了同等贡献，Jack W. Rae、Erich Elsen 和 Laurent Sifre 标注了同等资深作者身份。
- 来源: 2112.04426 | 备注: 

## spf-021 [single_paper_factual] intent=simple_faq verify=✓
- **Q**: 这篇论文提出了什么方法，用于解决什么问题？
- **证据1**: From Local to Global: A GraphRAG Approach to Query-Focused Summarization
- **GT**: 这篇论文提出了 GraphRAG 方法，即一种从局部到全局的图检索增强生成方法，用于查询聚焦的摘要任务。论文标题为《From Local to Global: A GraphRAG Approach to Query-Focused Summarization》。
- 来源: 2404.16130 | 备注: 

## spf-022 [single_paper_factual] intent=simple_faq verify=✗ 证据仅给出论文标题，未提及序列到序列模型、稠密向量索引或外部知识等具体方法细节，无法支撑该ground truth。
- **Q**: 这篇论文提出了什么方法？
- **证据1**: Retrieval-Augmented Generation for Knowledge-Intensive NLP Tasks
- **GT**: 这篇论文提出了检索增强生成（Retrieval-Augmented Generation，RAG）方法，用于知识密集型自然语言处理任务。该方法将预训练的序列到序列模型与稠密向量索引相结合，使模型能够访问和利用外部知识。
- 来源: 2005.11401 | 备注: 

## spf-023 [single_paper_factual] intent=single_hop verify=✓
- **Q**: 这篇论文的引言中提到了哪些神经排序模型？
- **证据1**: Over the past few years, the Information Retrieval (IR) community has witnessed the introduction of a host of neural ranking models, including DRMM [7], KNRM [4, 36], and Duet [20, 22].
- **GT**: 论文引言中提到，过去几年信息检索（IR）领域涌现了大量神经排序模型，包括 DRMM、KNRM 和 Duet。
- 来源: 2004.12832 | 备注: 

## spf-024 [single_paper_factual] intent=simple_faq verify=✓
- **Q**: 这篇论文的摘要是什么？
- **证据1**: # **ABSTRACT**
- **GT**: 所提供的段落中仅包含"ABSTRACT"这一标题，并未给出摘要的具体内容，因此无法从该段落中获取论文摘要的正文信息。
- 来源: 2501.09136 | 备注: 

## spf-025 [single_paper_factual] intent=simple_faq verify=✓
- **Q**: 这篇论文的标题是什么？
- **证据1**: 1 Introduction (2303.11366)
- **GT**: 无法从给定原文中确定。原文仅提供了论文的章节标题“1 Introduction”和标识“(2303.11366)”，并未给出论文的正式标题。
- 来源: 2303.11366 | 备注: 

## cpc-001 [cross_paper_comparison] intent=multi_hop verify=✓
- **Q**: Both GraphRAG and RAPTOR aim to improve retrieval-augmented generation beyond flat chunk retrieval. How do their underlying indexing structures and retrieval mechanisms differ, and what different kinds of queries does each target?
- **证据1**: GraphRAG uses a large language model (LLM) to build a graph index in two stages: first, an LLM derives an entity knowledge graph from the source documents; second, pre-generated community summaries are used to answer questions. Community detection partitions the graph into a hierarchy of communities, and community summaries are generated for each. Given a question, each community summary is used t
- **证据2**: RAPTOR recursively clusters and summarizes text chunks to build a tree, where nodes closer to the root contain more abstract summaries and nodes closer to the leaves contain more detailed text. Retrieval can then traverse this tree, allowing the model to access information at different levels of abstraction. RAPTOR constructs the tree by clustering the embeddings of text chunks, summarizing each c
- **GT**: GraphRAG builds an explicit knowledge graph from the source documents, extracting entities and relationships and then partitioning the graph into hierarchical communities, each summarized into community reports; at query time it uses these pre-generated community summaries (with a map-reduce style aggregation) to answer global, query-focused summarization questions about an entire corpus. RAPTOR instead constructs a recursive tree of clusters: it embeds and clusters text chunks, then recursively summarizes and re-embeds those clusters to build higher-level nodes, so retrieval can traverse the tree at multiple abstraction levels. Thus GraphRAG's structure is graph- and community-based, oriented toward sensemaking over a whole corpus, whereas RAPTOR's structure is a hierarchical clustering tree oriented toward retrieving context at the right granularity for a query. The key contrast is that GraphRAG emphasizes global, corpus-level summarization via community summaries, while RAPTOR emphasizes multi-scale retrieval by recursively abstracting clusters of text.
- 来源: 2404.16130, 2401.18059 | 备注: 

## cpc-002 [cross_paper_comparison] intent=multi_hop verify=✗ The evidence only contains a ReAct excerpt and a ToolLLaMA-related sentence about open-source LLMs lacking tool-use sophistication due to instruction tuning focusing on basic tasks; it provides no support for the claimed ReAct prompting details (interleaved reasoning/action traces) or ToolLLaMA's full pipeline (API collection, instruction generation, annotation, retriever, SFT, ToolEval), so the ground truth is not fully supported.
- **Q**: Both ReAct and ToolLLaMA aim to make LLMs better at using external tools/APIs, but they address the problem from different angles. How do the two works differ in their core approach and in what they identify as the key limitation of existing LLMs?
- **证据1**: REACT: SYNERGIZING REASONING AND ACTING IN LANGUAGE MODELS
- **证据2**: Although open-source LLMs, e.g., LLaMA (Touvron et al., 2023a), have achieved versatile capabilities through instruction tuning (Taori et al., 2023; Chiang et al., 2023), they still lack the sophistication in performing higher-level tasks, such as appropriately interacting with tools (APIs) to fulfill complex human instruction. This deficiency is because current instruction tuning largely focuses 
- **GT**: ReAct takes a prompting-based approach: it synergizes reasoning and acting in language models by letting the model generate interleaved reasoning traces and task-specific actions, so that reasoning guides action and actions gather observations for further reasoning. ToolLLaMA, by contrast, frames the problem as tool learning and builds a full data-construction-and-training pipeline (API collection, instruction generation, solution-path annotation, an API retriever, SFT, and ToolEval) to teach LLMs to interact with real APIs. Their diagnoses of the limitation also differ: ReAct targets the gap between pure reasoning and pure acting, whereas ToolLLaMA argues that open-source LLMs lack tool-use sophistication because current instruction tuning focuses on basic language tasks and relatively neglects the tool-use domain. Thus ReAct improves tool use through inference-time prompting, while ToolLLaMA improves it through curated tool-use data and supervised fine-tuning.
- 来源: 2210.03629, 2307.16789 | 备注: 

## cpc-003 [cross_paper_comparison] intent=multi_hop verify=✗ The evidence mentions reflection tokens and adaptive retrieval generally, but does not name specific tokens like "Retrieve" and "Critique", nor does it mention citation accuracy, open-domain QA, long-form generation, hallucination reduction, or specific benchmarks claimed by either approach.
- **Q**: Both SELF-RAG and ReAct interleave reasoning with retrieval/acting, but how do their mechanisms for deciding when to retrieve or act differ, and what distinct capabilities does each approach claim as a result?
- **证据1**: We introduce Self-RAG, a framework to enhance an LM's generation quality and factuality through retrieval and self-reflection. Self-RAG trains an arbitrary LM to adaptively retrieve passages on-demand and generate and reflect on retrieved passages and its own generations using special tokens, called reflection tokens. Generating reflection tokens makes the LM controllable during the inference phas
- **证据2**: We explore the use of LLMs to synergize reasoning and acting in an interleaved manner to solve diverse language reasoning and decision making tasks. ReAct prompts LLMs to generate both verbal reasoning traces and actions pertaining to a task in an interleaved manner, which allows the model to perform dynamic reasoning to create, maintain, and adjust high-level plans for acting (reason to act), whi
- **GT**: SELF-RAG trains an LM to adaptively retrieve passages on demand and to generate self-reflection tokens that critique its own output, using special tokens such as "Retrieve" and "Critique" to control retrieval and assess relevance, support, and usefulness. ReAct instead prompts an LLM to interleave verbal reasoning traces with task-specific actions in an alternating manner, where the reasoning traces help the model induce, track, and update action plans while handling exceptions. Thus SELF-RAG's control is learned and internalized through training with reflection tokens, whereas ReAct's is elicited through prompting that produces thought-action-observation trajectories. As a result, SELF-RAG claims improved factuality and citation accuracy on tasks like open-domain QA and long-form generation, while ReAct claims improved synergies between reasoning and acting that reduce hallucination and error propagation on knowledge-intensive and interactive decision-making benchmarks.
- 来源: 2310.11511, 2210.03629 | 备注: 

## cpc-004 [cross_paper_comparison] intent=multi_hop verify=✗ The evidence only states SELF-REFINE is training-free and gives SELF-RAG's title, but does not confirm SELF-RAG actually trains the model or that it incorporates retrieval/learned self-critique, nor does it mention iterative refinement across dialog and math reasoning tasks.
- **Q**: Both SELF-REFINE and SELF-RAG use self-generated signals to improve LLM outputs, but how do their mechanisms and training requirements differ?
- **证据1**: SELF-REFINE does not require any supervised training data, additional training, or reinforcement learning, and instead uses a single LLM as the generator, refiner and the feedback provider.
- **证据2**: SELF-RAG: LEARNING TO RETRIEVE, GENERATE, AND CRITIQUE THROUGH SELF-REFLECTION
- **GT**: SELF-REFINE improves an LLM's initial output by having the same LLM generate feedback on its own output and then refine itself iteratively, requiring no supervised training data, additional training, or reinforcement learning—a single LLM acts as generator, refiner, and feedback provider. SELF-RAG, by contrast, is framed as a learning-based approach that trains the model to retrieve, generate, and critique through self-reflection, meaning it does rely on training rather than being a purely test-time, standalone method. Thus while SELF-REFINE is a training-free iterative refinement loop applied at test time across tasks like dialog and math reasoning, SELF-RAG incorporates retrieval and learned self-critique into the model itself. Both share the core idea of using self-feedback/self-reflection, but SELF-REFINE operates without any training while SELF-RAG is explicitly about learning to do so.
- 来源: 2303.17651, 2310.11511 | 备注: 

## cpc-005 [cross_paper_comparison] intent=multi_hop verify=✗ 证据仅描述了 Reflexion 与 Agentic RAG 的机制，未包含论文编号（2303.11366、2501.09136）、"verbal reinforcement learning"、"learning from failures across trials"、"contextual grounding and generation quality" 等具体表述，故部分事实无证据支撑。
- **Q**: Both papers address the limitations of large language models, but they propose different mechanisms for improvement. What is the core mechanism proposed in each paper, and how do their approaches to enhancing LLM performance differ?
- **证据1**: Reflexion is a framework that equips agents with dynamic memory and self-reflection capabilities to enhance their future reasoning and decision-making. It allows agents to verbally reflect on task feedback signals, maintain reflective text in an episodic memory buffer, and induce better decision-making in subsequent trials.
- **证据2**: Agentic Retrieval-Augmented Generation (Agentic RAG) is a paradigm that incorporates autonomous agents into the RAG pipeline, enabling them to dynamically manage retrieval strategies, iteratively refine contextual understanding, and adapt workflows through reflection or planning.
- **GT**: Paper A (2303.11366) proposes "Reflexion," a framework that equips agents with dynamic memory and self-reflection capabilities, allowing them to verbally reflect on task feedback signals and maintain reflective text in an episodic memory buffer to induce better decision-making in subsequent trials. Paper B (2501.09136) proposes "Agentic Retrieval-Augmented Generation" (Agentic RAG), a paradigm that incorporates autonomous agents into the RAG pipeline, enabling them to dynamically manage retrieval strategies, iteratively refine contextual understanding, and adapt workflows through reflection or planning. While Paper A focuses on self-reflection as a mechanism for learning from failures across trials to improve reasoning and decision-making, Paper B focuses on agent-driven retrieval orchestration to enhance contextual grounding and generation quality. Both approaches leverage agentic capabilities, but Paper A emphasizes verbal reinforcement learning through self-reflection, whereas Paper B emphasizes autonomous retrieval management and adaptive workflow orchestration.
- 来源: 2303.11366, 2501.09136 | 备注: 

## cpc-006 [cross_paper_comparison] intent=multi_hop verify=✓
- **Q**: Both papers address the limitations of large language models, but they propose different mechanisms to overcome them. What is the key difference between the approach in Paper A (2303.11366) and the approach in Paper B (2410.05779)?
- **证据1**: Reflexion is a new paradigm for language agents that dynamically reinforces an agent's behavior through verbal self-reflection. It converts feedback into verbal self-reflections and stores them in an episodic memory buffer to induce better decision-making in subsequent trials, without updating the model's weights.
- **证据2**: Large language models (LLMs) have demonstrated remarkable capabilities, yet they still struggle with long-context understanding, where they fail to effectively utilize information in long inputs. In this work, we propose a method to enhance the long-context understanding ability of LLMs.
- **GT**: Paper A (2303.11366) proposes Reflexion, which equips an agent with dynamic memory and self-reflection to verbally reinforce its own behavior after failures, converting feedback into verbal self-reflections stored in an episodic memory buffer to improve subsequent attempts without updating model weights. Paper B (2410.05779) instead focuses on the limitations of LLMs in long-context scenarios, where models struggle to effectively utilize information in long inputs, and proposes a method to enhance long-context understanding. Thus, while Paper A addresses agent learning through iterative verbal self-reflection and memory, Paper B targets the fundamental capability of processing and reasoning over long contexts, representing a contrast between an agent-level learning framework and a long-context capability enhancement method.
- 来源: 2303.11366, 2410.05779 | 备注: 

## cpc-007 [cross_paper_comparison] intent=multi_hop verify=✓
- **Q**: Both papers aim to improve large language model outputs beyond a single forward pass, but they differ in mechanism and in what resources they rely on. How does RETRO's retrieval-based approach differ from SELF-REFINE's iterative refinement approach in terms of the mechanism used to improve outputs and the external resources required?
- **证据1**: Improving language models by retrieving from trillions of tokens
- **证据2**: The main idea is to generate an initial output using an LLM; then, the same LLM provides _feedback_ for its output and uses it to _refine_ itself, iteratively. SELF-REFINE does not require any supervised training data, additional training, or reinforcement learning, and instead uses a single LLM as the generator, refiner and the feedback provider.
- **GT**: RETRO improves language models by retrieving from trillions of tokens, i.e., it augments the model with a large-scale external retrieval corpus, so improvements come from conditioning on retrieved evidence rather than from the model alone. SELF-REFINE instead improves outputs at test-time through iterative feedback and refinement, where the same LLM acts as generator, feedback provider, and refiner, requiring no supervised training data, additional training, or reinforcement learning. Thus RETRO's mechanism is retrieval-augmented conditioning on an external datastore, while SELF-REFINE's mechanism is self-generated feedback and iterative self-refinement using a single LLM. Both avoid conventional one-step generation, but RETRO depends on an external retrieval source whereas SELF-REFINE depends only on the LLM's own feedback loop.
- 来源: 2112.04426, 2303.17651 | 备注: 

## cpc-008 [cross_paper_comparison] intent=multi_hop verify=✗ The evidence supports Query2doc's query-side pseudo-document expansion and BM25 gains without fine-tuning, and M3-Embedding's multi-functionality and self-knowledge distillation, but it does not mention query disambiguation, helping state-of-the-art dense retrievers, 100+ languages, 8,192 tokens, optimized batching, or SOTA multilingual/cross-lingual/long-document results.
- **Q**: Both papers aim to improve retrieval effectiveness, but they intervene at different stages of the retrieval pipeline. How does Query2doc's approach to boosting retrieval differ from M3-Embedding's, in terms of what is modified and what training is required?
- **证据1**: The proposed method first generates pseudo-documents by few-shot prompting large language models (LLMs), and then expands the query with generated pseudodocuments. ... Experimental results demonstrate that query2doc boosts the performance of BM25 by 3% to 15% on ad-hoc IR datasets, such as MSMARCO and TREC DL, without any model fine-tuning.
- **证据2**: It can simultaneously accomplish the three common retrieval functionalities: dense retrieval, multi-vector retrieval, and sparse retrieval. ... Notably, we propose a novel self-knowledge distillation approach, where the relevance scores from different retrieval functionalities can be integrated as the teacher signal to enhance the training quality.
- **GT**: Query2doc intervenes at the query side: it uses few-shot prompting of LLMs to generate pseudo-documents and then expands the original query with those pseudo-documents, which aids query disambiguation and guides retrievers, boosting BM25 by 3%–15% on ad-hoc IR datasets such as MSMARCO and TREC DL without any model fine-tuning, and also helping state-of-the-art dense retrievers. M3-Embedding instead intervenes at the model/training side, introducing a new embedding model that uniformly supports over 100 languages and simultaneously performs dense, multi-vector, and sparse retrieval for inputs from short sentences up to 8,192 tokens. Its training relies on technical contributions such as a self-knowledge distillation approach that integrates relevance scores from different retrieval functionalities as teacher signals, plus an optimized batching strategy for large batch sizes and high throughput. Thus Query2doc is a training-free, query-expansion wrapper applicable to existing sparse and dense retrievers, whereas M3-Embedding is a newly trained, versatile embedding model that sets state-of-the-art results on multilingual, cross-lingual, and long-document retrieval benchmarks.
- 来源: 2303.07678, 2402.03216 | 备注: 

## cpc-009 [cross_paper_comparison] intent=multi_hop verify=✗ The evidence describes the two-stage retriever-reader framework and Query2doc's query expansion with 3%–15% BM25 gains, but it never mentions DPR, dense dual-encoder training, the SQuAD v1.1 exact-match drop from >80% to <40%, or Query2doc's benefits to dense retrievers in/out-of-domain, so key facts in the ground truth are unsupported.
- **Q**: Both papers aim to improve retrieval for downstream tasks, but they intervene at different points in the retrieval pipeline. What is the core mechanism each proposes, and how do their reported gains differ in nature?
- **证据1**: the advances of reading comprehension models suggest a much simplified two-stage framework: (1) a context _retriever_ first selects a small subset of passages where some of them contain the answer to the question, and then (2) a machine _reader_ can thoroughly examine the retrieved contexts and identify the correct answer (Chen et al., 2017). Although reducing open-domain QA to machine reading is 
- **证据2**: This paper introduces a simple yet effective query expansion approach, denoted as _query2doc_ , to improve both sparse and dense retrieval systems. The proposed method first generates pseudo-documents by few-shot prompting large language models (LLMs), and then expands the query with generated pseudodocuments. LLMs are trained on web-scale text corpora and are adept at knowledge memorization. The 
- **GT**: DPR addresses retrieval by training a dense dual-encoder retriever so that a small set of answer-containing passages can be selected before a machine reader examines them, motivated by the observation that open-domain QA performance collapses when reading comprehension models are applied to retrieved contexts (e.g., SQuAD v1.1 exact match dropping from above 80% to less than 40%). Query2doc instead leaves the retriever's architecture untouched and intervenes at the query side: it generates pseudo-documents via few-shot prompting of LLMs and expands the original query with them, since LLMs' web-scale training makes the pseudo-documents rich in relevant information that aids disambiguation. Thus DPR's contribution is a learned dense retrieval model, whereas Query2doc is a model-agnostic expansion technique that boosts BM25 by 3%–15% on ad-hoc IR datasets like MSMARCO and TREC DL without any fine-tuning, and also benefits state-of-the-art dense retrievers in-domain and out-of-domain.
- 来源: 2004.04906, 2303.07678 | 备注: 

## cpc-010 [cross_paper_comparison] intent=multi_hop verify=✗ The evidence supports Atlas's retrieval augmentation and few-shot results and ToolLLaMA's tool-use motivation, but it does not mention that Atlas's index can be easily updated, that ToolLLaMA acts as an intermediary between users and applications, or that ToolLLaMA retrieves APIs and generates solution paths.
- **Q**: How do Atlas and ToolLLaMA differ in the way they augment a language model with external resources, and what problem does each approach aim to solve?
- **证据1**: Retrieval augmented models are known to excel at knowledge intensive tasks without the need for as many parameters, but it is unclear whether they work in few-shot settings. In this work we present Atlas, a carefully designed and pre-trained retrieval augmented language model able to learn knowledge intensive tasks with very few training examples. ... Notably, Atlas reaches over 42% accuracy on Na
- **证据2**: Tool learning (Qin et al., 2023b) aims to unleash the power of large language models (LLMs) to effectively interact with various tools (APIs) to accomplish complex tasks. ... Although open-source LLMs, e.g., LLaMA (Touvron et al., 2023a), have achieved versatile capabilities through instruction tuning (Taori et al., 2023; Chiang et al., 2023), they still lack the sophistication in performing highe
- **GT**: Atlas augments a language model with a retrieval component over a document index, aiming to handle knowledge-intensive tasks such as question answering and fact checking in few-shot settings without needing massive parameter counts; its index can be easily updated, and it reaches over 42% accuracy on Natural Questions with only 64 examples, beating a 540B-parameter model by 3% despite having 50x fewer parameters. ToolLLaMA instead augments an LLM with tools/APIs, aiming to let the model act as an intermediary between users and applications by interacting with APIs to accomplish complex tasks. The motivation differs: Atlas addresses the need for large parameter counts to store knowledge, whereas ToolLLaMA addresses the deficiency of open-source LLMs in tool-use, since current instruction tuning focuses on basic language tasks and neglects the tool-use domain. Thus Atlas retrieves documents to supply knowledge, while ToolLLaMA retrieves APIs and generates solution paths to supply actions.
- 来源: 2208.03299, 2307.16789 | 备注: 

## cpc-011 [cross_paper_comparison] intent=multi_hop verify=✗ The evidence only contains a figure caption about low-quality retrievers and the Self-RAG paper title; it lacks any description of CRAG's corrective retrieval step or Self-RAG's internal critique mechanism, so the comparative claims in the ground truth are not supported.
- **Q**: How do CRAG and Self-RAG differ in the way they address the problem of low-quality or irrelevant retrieved documents in retrieval-augmented generation?
- **证据1**: Figure 1: The examples show that a low-quality retriever is prone to introducing a substantial amount of irrelevant information, impeding the generators from acquiring accurate knowledge and potentially misleading them.
- **证据2**: SELF-RAG: LEARNING TO RETRIEVE, GENERATE, AND CRITIQUE THROUGH SELF-REFLECTION
- **GT**: Both papers target the same weakness of retrieval-augmented generation: a low-quality retriever can inject irrelevant information that misleads the generator. CRAG frames this as a retrieval-quality problem, noting that a poor retriever is "prone to introducing a substantial amount of irrelevant information," and therefore applies a corrective step to the retrieved documents before generation. Self-RAG instead places the critique inside the model itself, training the LLM to retrieve, generate, and critique through self-reflection, so that it decides when and what to retrieve and evaluates its own output. Thus CRAG corrects retrieval externally, whereas Self-RAG internalizes retrieval and critique decisions in the generator. Both ultimately aim to keep the generator from being misled by inaccurate documents, but they intervene at different stages of the pipeline.
- 来源: 2401.15884, 2310.11511 | 备注: 

## cpc-012 [cross_paper_comparison] intent=multi_hop verify=✗ The evidence supports E5's contrastive training on CCPairs and being first to beat BM25 on BEIR, and HyDE's statement that no models were trained, but it does not mention HyDE generating a hypothetical document whose embedding is used for retrieval, nor that HyDE leaves the retriever frozen and improves zero-shot retrieval at inference time.
- **Q**: How do E5 and HyDE differ in the way they achieve strong zero-shot retrieval performance without relevance labels?
- **证据1**: The model is trained in a contrastive manner with weak supervision signals from our curated large-scale text pair dataset (called CCPairs). E5 can be readily used as a general-purpose embedding model for any tasks requiring a single-vector representation of texts such as retrieval, clustering, and classification, achieving strong performance in both zero-shot and fine-tuned settings. ... For zero-
- **证据2**: Dense retrieval (Lee et al., 2019; Karpukhin et al., 2020), the method of retrieving documents using semantic embedding similarities, has been shown successful across tasks like web search, question answering, and fact verification. A variety of methods such as negative mining (Xiong et al., 2021; Qu et al., 2021), distillation (Qu et al., 2021; Lin et al., 2021b; Hofstätter et al., 2021) and task
- **GT**: E5 attains zero-shot retrieval ability by training a dense embedding model contrastively on a large-scale curated text pair dataset (CCPairs) using weak supervision signals, and it is the first model to outperform the BM25 baseline on BEIR without any labeled data. HyDE, by contrast, trains no models at all, as the authors explicitly state that no models were trained or fine-tuned in producing their work. Instead of learning better embeddings, HyDE builds on existing supervised dense retrieval methods—which are typically improved via negative mining, distillation, and task-specific pre-training—and generates a hypothetical document whose embedding is used for retrieval. Thus E5 improves the embedding model itself through weakly-supervised contrastive pre-training, whereas HyDE leaves the retriever frozen and improves zero-shot retrieval at inference time.
- 来源: 2212.03533, 2212.10496 | 备注: 

## cpc-013 [cross_paper_comparison] intent=multi_hop verify=✗ The evidence supports E5's contrastive weak-supervision training on CCPairs and its general-purpose single-vector use, and M3-Embedding's self-knowledge distillation and optimized batching, but it does not mention E5's evaluation on 56 BEIR/MTEB datasets, being first to beat BM25 on BEIR zero-shot, nor M3-Embedding's 100+ languages, dense/multi-vector/sparse retrieval, or 8,192-token inputs.
- **Q**: How do E5 and M3-Embedding differ in their training signals and the scope of retrieval capabilities they target?
- **证据1**: The model is trained in a contrastive manner with weak supervision signals from our curated large-scale text pair dataset (called CCPairs). E5 can be readily used as a general-purpose embedding model for any tasks requiring a single-vector representation of texts such as retrieval, clustering, and classification, achieving strong performance in both zero-shot and fine-tuned settings.
- **证据2**: Notably, we propose a novel self-knowledge distillation approach, where the relevance scores from different retrieval functionalities can be integrated as the teacher signal to enhance the training quality. We also optimize the batching strategy, which enables a large batch size and high training throughput to improve the discriminativeness of embeddings.
- **GT**: E5 is trained contrastively using weak supervision signals derived from a curated large-scale text pair dataset called CCPairs, and it is designed as a general-purpose single-vector embedding model for tasks such as retrieval, clustering, and classification. M3-Embedding instead relies on a novel self-knowledge distillation approach, where relevance scores from different retrieval functionalities are integrated as a teacher signal to improve training quality, combined with an optimized batching strategy for large batch sizes. In terms of scope, E5 produces a single-vector representation and is evaluated on 56 datasets from BEIR and MTEB, being the first model to beat BM25 on BEIR in a zero-shot setting. M3-Embedding is distinguished by multi-linguality, multi-functionality, and multi-granularity: it supports over 100 working languages, simultaneously performs dense, multi-vector, and sparse retrieval, and handles inputs from short sentences to 8,192-token documents. Thus, E5 emphasizes weakly-supervised general-purpose single-vector embeddings, whereas M3-Embedding emphasizes versatile multi-functional retrieval via self-knowledge distillation.
- 来源: 2212.03533, 2402.03216 | 备注: 

## cpc-014 [cross_paper_comparison] intent=multi_hop verify=✗ The evidence supports HyDE being training-free and M3-Embedding's self-knowledge distillation and batching strategy, but it does not mention that M3-Embedding unifies dense, multi-vector, and sparse retrieval across over 100 languages or supports granularities up to 8,192 tokens.
- **Q**: How do HyDE and M3-Embedding differ in their fundamental strategy for improving retrieval effectiveness, particularly regarding whether model training is required?
- **证据1**: 1No models were trained or fine-tuned in making this preprint. Our open source code is available at https://github. com/texttron/hyde.
- **证据2**: Notably, we propose a novel self-knowledge distillation approach, where the relevance scores from different retrieval functionalities can be integrated as the teacher signal to enhance the training quality. We also optimize the batching strategy, which enables a large batch size and high training throughput to improve the discriminativeness of embeddings.
- **GT**: HyDE takes a training-free approach: it performs precise zero-shot dense retrieval without relevance labels, and the authors explicitly state that no models were trained or fine-tuned in producing their work. In contrast, M3-Embedding is a trained embedding model whose effectiveness comes from a series of technical contributions, most notably a novel self-knowledge distillation approach in which relevance scores from different retrieval functionalities serve as the teacher signal to enhance training quality. M3-Embedding also optimizes the batching strategy to enable large batch sizes and high training throughput, improving embedding discriminativeness. Thus, while HyDE improves dense retrieval by avoiding supervision entirely, M3-Embedding improves it by training a versatile model that unifies dense, multi-vector, and sparse retrieval across over 100 languages and granularities up to 8,192 tokens.
- 来源: 2212.10496, 2402.03216 | 备注: 

## cpc-015 [cross_paper_comparison] intent=multi_hop verify=✗ The evidence supports Paper A's framing and survey scope, but it does not mention Paper A introducing an evaluation framework/benchmark, nor does it mention Paper B proposing CRAG or a corrective approach, so key parts of the ground truth are unsupported.
- **Q**: How do Paper A and Paper B differ in their framing of the problem that retrieval augmentation is meant to solve, and in the type of contribution each makes?
- **证据1**: Large Language Models (LLMs) showcase impressive capabilities but encounter challenges like hallucination, outdated knowledge, and non-transparent, untraceable reasoning processes. Retrieval-Augmented Generation (RAG) has emerged as a promising solution by incorporating knowledge from external databases. This enhances the accuracy and credibility of the generation, particularly for knowledge-inten
- **证据2**: Nevertheless, LLMs inevitably manifest hallucinations (Ji et al., 2023) due to their struggle with factual errors (Mallen et al., 2023; Min et al., 2023) and inability to secure the accuracy of generated texts solely by the parametric knowledge they encapsulate (Zhang et al., 2023b; Muhlgay et al., 2023). Figure 1: The examples show that a low-quality retriever is prone to introducing a substantia
- **GT**: Paper A frames RAG as a broad solution to LLM limitations such as hallucination, outdated knowledge, and non-transparent, untraceable reasoning, emphasizing that RAG merges LLMs' intrinsic knowledge with vast, dynamic external databases to improve accuracy and credibility, especially for knowledge-intensive tasks. It is a comprehensive survey that reviews the progression of RAG paradigms (Naive, Advanced, and Modular RAG), scrutinizes the tripartite foundation of retrieval, generation, and augmentation, and introduces an up-to-date evaluation framework and benchmark. Paper B, by contrast, focuses on a specific failure mode: LLMs inevitably manifest hallucinations due to factual errors and their inability to secure accuracy from parametric knowledge alone, and a low-quality retriever can introduce substantial irrelevant information that misleads the generator. Thus while Paper A offers a panoramic taxonomy and evaluation overview of RAG, Paper B diagnoses the retriever-quality problem and proposes a corrective approach (CRAG) to address it.
- 来源: 2312.10997, 2401.15884 | 备注: 

## cpc-016 [cross_paper_comparison] intent=multi_hop verify=✓
- **Q**: How do RAG and Atlas differ in their target setting and the way they combine retrieval with generation, and what does each report about performance relative to large parametric models?
- **证据1**: Retrieval-Augmented Generation (RAG) models combine parametric and non-parametric memory for language generation: a parametric seq2seq model acts as the generator and a dense vector index of Wikipedia, accessed by a neural retriever, provides non-parametric memory. We fine-tune and evaluate our models on a wide range of knowledge-intensive NLP tasks and set the state of the art on three open domai
- **证据2**: Retrieval augmented models are known to excel at knowledge intensive tasks without the need for as many parameters, but it is unclear whether they work in few-shot settings. In this work we present Atlas, a carefully designed and pre-trained retrieval augmented language model able to learn knowledge intensive tasks with very few training examples. We perform evaluations on a wide range of tasks, i
- **GT**: Both papers address knowledge-intensive NLP tasks by augmenting a language model with a retrieval component, but they target different regimes and emphasize different mechanisms. RAG (Paper A) is presented as a general-purpose approach for knowledge-intensive tasks, pairing a parametric seq2seq generator with a non-parametric dense index accessed via a retriever, so that knowledge can be updated by swapping the index rather than the parameters. Atlas (Paper B) instead focuses explicitly on the few-shot setting, arguing that retrieval-augmented models can excel at knowledge-intensive tasks without needing massive parameter counts to store knowledge, and it is carefully designed and pre-trained for learning such tasks from very few examples. Atlas also studies the impact of the content of the document index, showing it can easily be updated, echoing RAG's non-parametric knowledge idea. In terms of results, Atlas reaches over 42% accuracy on Natural Questions with only 64 examples, outperforming a 540B-parameter model by 3% despite having 50x fewer parameters, which directly supports the claim that retrieval augmentation substitutes for parameter-heavy knowledge storage.
- 来源: 2005.11401, 2208.03299 | 备注: 

## cpc-017 [cross_paper_comparison] intent=multi_hop verify=✗ The evidence supports REALM's trainable retriever and computational challenge and CRAG's low-quality retriever failure mode, but it does not mention REALM's stated motivation about BERT/RoBERTa/T5 storing world knowledge, nor CRAG's observation that LLMs inevitably hallucinate due to factual errors and parametric knowledge limits.
- **Q**: How do REALM and Corrective Retrieval Augmented Generation (CRAG) differ in their treatment of the retriever within a retrieval-augmented generation pipeline, and what problem does each paper identify as the central motivation for its approach?
- **证据1**: REALM augments language model pre-training with a neural knowledge retriever that retrieves knowledge from a textual knowledge corpus, Z (e.g., all of Wikipedia). Signal from the language modeling objective backpropagates all the way through the retriever, which must consider millions of documents in Z—a significant computational challenge that we address.
- **证据2**: The examples show that a low-quality retriever is prone to introducing a substantial amount of irrelevant information, impeding the generators from acquiring accurate knowledge and potentially misleading them.
- **GT**: REALM treats the retriever as a trainable component of language model pre-training: it augments pre-training with a neural knowledge retriever over a textual corpus such as Wikipedia, and the language modeling objective's signal is backpropagated all the way through the retriever, which must consider millions of documents—a computational challenge the paper explicitly addresses. Its motivation is that pre-trained models like BERT, RoBERTa and T5 already store a surprising amount of world knowledge, so retrieval can be learned jointly rather than bolted on. CRAG, by contrast, starts from the observation that LLMs inevitably manifest hallucinations because they struggle with factual errors and cannot secure accuracy from parametric knowledge alone. It focuses on the failure mode of a low-quality retriever, which is prone to introducing substantial irrelevant information, impeding generators from acquiring accurate knowledge and potentially misleading them. Thus REALM optimizes the retriever end-to-end during pre-training, whereas CRAG diagnoses and corrects retrieval quality at generation time.
- 来源: 2002.08909, 2401.15884 | 备注: 

## cpc-018 [cross_paper_comparison] intent=multi_hop verify=✗ The evidence only provides REALM details and RAPTOR's title; it contains no information about RAPTOR's recursive abstractive processing, tree-organized retrieval structure, or how it organizes knowledge, so the ground truth's RAPTOR claims are unsupported.
- **Q**: How do REALM and RAPTOR differ in the way they obtain and organize the knowledge that supports a language model's predictions?
- **证据1**: REALM augments language model pre-training with a neural knowledge retriever that retrieves knowledge from a textual knowledge corpus, Z (e.g., all of Wikipedia). Signal from the language modeling objective backpropagates all the way through the retriever, which must consider millions of documents in Z—a significant computational challenge that we address.
- **证据2**: RAPTOR: RECURSIVE ABSTRACTIVE PROCESSING FOR TREE-ORGANIZED RETRIEVAL
- **GT**: REALM augments language model pre-training with a neural knowledge retriever that pulls knowledge from a textual knowledge corpus such as all of Wikipedia, and the language modeling objective's signal backpropagates all the way through the retriever, forcing it to consider millions of documents. RAPTOR, by contrast, is a recursive abstractive processing method that builds a tree-organized retrieval structure rather than relying on a flat document corpus. Thus, while REALM's key challenge is making retrieval over millions of documents computationally tractable during pre-training, RAPTOR's contribution lies in recursively summarizing and organizing content into a hierarchy for retrieval. Both approaches aim to supply external knowledge to a language model, but REALM learns retrieval end-to-end via pre-training gradients, whereas RAPTOR structures knowledge through recursive abstraction into a tree.
- 来源: 2002.08909, 2401.18059 | 备注: 

## cpc-019 [cross_paper_comparison] intent=multi_hop verify=✗ The evidence only contains the RETRO paper title and an Atlas abstract excerpt; it does not state that RETRO is a DeepMind effort, nor does it contain Atlas's argument about retrieval substituting for parameter scale or extending to few-shot settings beyond the 42%/64-example result, so several ground-truth facts are unsupported.
- **Q**: How do RETRO (Paper A) and Atlas (Paper B) differ in their approach to retrieval-augmented language modeling, and what do their reported results suggest about the trade-off between model scale and retrieval?
- **证据1**: Improving language models by retrieving from trillions of tokens
- **证据2**: In this work we present Atlas, a carefully designed and pre-trained retrieval augmented language model able to learn knowledge intensive tasks with very few training examples. We perform evaluations on a wide range of tasks, including MMLU, KILT and NaturalQuestions, and study the impact of the content of the document index, showing that it can easily be updated. Notably, Atlas reaches over 42% ac
- **GT**: Both papers pursue retrieval-augmented language modeling but with different emphases: RETRO (Paper A) is a DeepMind effort focused on scaling retrieval to trillions of tokens, while Atlas (Paper B) is a carefully designed and pre-trained retrieval augmented model explicitly targeting few-shot learning on knowledge-intensive tasks. Atlas argues that retrieval augmented models excel at knowledge-intensive tasks without needing as many parameters, addressing the concern that massive parameter counts seem necessary to store knowledge for tasks like question answering and fact checking. Empirically, Atlas reaches over 42% accuracy on Natural Questions using only 64 examples, outperforming a 540B-parameter model by 3% despite having 50x fewer parameters. Together, the two works suggest that retrieval can substitute for much of the parameter scale otherwise needed to store knowledge, and that this benefit extends even to few-shot settings.
- 来源: 2112.04426, 2208.03299 | 备注: 

## cpc-020 [cross_paper_comparison] intent=multi_hop verify=✗ The evidence only contains one sentence about instruction tuning neglecting tool use and a bare "# ABSTRACT" marker; it provides no information about Paper B's motivation or remedy, nor about Paper A's pipeline details (API collection, instruction generation, solution path annotation, API retriever, SFT of ToolLLaMA, ToolEval), so the ground truth is not fully supported.
- **Q**: How do the two papers differ in their stated motivation for why LLMs struggle with tool use, and what remedy does each propose?
- **证据1**: This deficiency is because current instruction tuning largely focuses on basic language tasks, with a relative neglect of the tool-use domain.
- **证据2**: # ABSTRACT
- **GT**: Paper A attributes the deficiency to instruction tuning that focuses largely on basic language tasks while neglecting the tool-use domain, leaving even instruction-tuned open-source LLMs like LLaMA unable to appropriately interact with APIs for complex human instructions. Its remedy is a data construction, training, and inference pipeline: API collection, instruction generation, solution path annotation, an API retriever that supplies relevant APIs, SFT training of ToolLLaMA, and evaluation with ToolEval. Paper B, by contrast, frames its contribution at the level of the abstract, presenting its own approach to the problem rather than diagnosing instruction-tuning neglect. Thus Paper A's motivation is a gap in tuning data coverage addressed by a retrieval-augmented SFT pipeline, whereas Paper B's motivation is stated in abstract form without the same explicit critique of instruction tuning.
- 来源: 2307.16789, 2410.05779 | 备注: 

## cpc-021 [cross_paper_comparison] intent=multi_hop verify=✓
- **Q**: How do the two papers position themselves differently with respect to the role of supervised training in dense retrieval for open-domain QA?
- **证据1**: Although reducing open-domain QA to machine reading is a very reasonable strategy, a huge performance degradation is often observed in practice, indicating the needs of improving retrieval. ... the exact match score on SQuAD v1.1 drops from above 80% to less than 40%
- **证据2**: Dense retrieval (Lee et al., 2019; Karpukhin et al., 2020), the method of retrieving documents using semantic embedding similarities, has been shown successful across tasks like web search, question answering, and fact verification. A variety of methods such as negative mining (Xiong et al., 2021; Qu et al., 2021), distillation (Qu et al., 2021; Lin et al., 2021b; Hofstätter et al., 2021) and task
- **GT**: Paper A (DPR) frames open-domain QA as a two-stage retrieve-then-read pipeline and argues that the bottleneck lies in the retriever, since a machine reader's exact match on SQuAD v1.1 collapses from above 80% to less than 40% when applied to retrieved contexts; its contribution is therefore a trained dense retriever. Paper B (HyDE) instead takes supervised dense retrieval as an already established success and lists the techniques used to improve it—negative mining, distillation, and task-specific pre-training—while explicitly noting that no models were trained or fine-tuned in producing its work. Thus, whereas Paper A improves retrieval by training a dense encoder, Paper B aims at precise zero-shot dense retrieval without relevance labels and without any training.
- 来源: 2004.04906, 2212.10496 | 备注: 

## cpc-022 [cross_paper_comparison] intent=multi_hop verify=✗ The evidence supports REALM's end-to-end pre-training with a neural retriever and the survey's Naive/Advanced/Modular taxonomy plus retrieval/generation/augmentation components, but the ground truth also claims the survey frames RAG as solving hallucination, outdated knowledge, and non-transparent reasoning via external databases and covers evaluation frameworks and open challenges—none of which appear in the evidence.
- **Q**: How does REALM's treatment of retrieval-augmented language modeling differ from the way the RAG survey characterizes retrieval-augmented generation?
- **证据1**: REALM augments language model pre-training with a neural knowledge retriever that retrieves knowledge from a textual knowledge corpus, Z (e.g., all of Wikipedia). Signal from the language modeling objective backpropagates all the way through the retriever, which must consider millions of documents in Z—a significant computational challenge that we address.
- **证据2**: This comprehensive review paper offers a detailed examination of the progression of RAG paradigms, encompassing the Naive RAG, the Advanced RAG, and the Modular RAG. It meticulously scrutinizes the tripartite foundation of RAG frameworks, which includes the retrieval, the generation and the augmentation techniques.
- **GT**: REALM is a concrete pre-training method that augments a language model with a neural knowledge retriever drawing from a textual knowledge corpus such as all of Wikipedia, and it is trained end-to-end so that the language modeling objective's signal backpropagates all the way through the retriever, which must consider millions of documents. The RAG survey, by contrast, is a comprehensive review rather than a single model: it frames RAG as a solution to LLM problems like hallucination, outdated knowledge, and non-transparent reasoning by incorporating external databases, and it organizes the field into Naive, Advanced, and Modular RAG paradigms. Thus REALM focuses on the mechanism and computational challenge of jointly training retriever and LM, while the survey focuses on taxonomy, component technologies (retrieval, generation, augmentation), evaluation frameworks, and open challenges.
- 来源: 2002.08909, 2312.10997 | 备注: 

## cpc-023 [cross_paper_comparison] intent=multi_hop verify=✗ The evidence only contains Paper B's abstract (the survey/review description) and Paper A's title; it does not include any text describing Paper A as a primary research contribution that introduces RAG with a parametric seq2seq generator and non-parametric dense retrieval index, so that part of the ground truth is unsupported.
- **Q**: Paper A (2005.11401) and Paper B (2312.10997) both address Retrieval-Augmented Generation, but they occupy different roles in the literature. How does Paper A's contribution differ from Paper B's in terms of what each paper actually delivers to the RAG field?
- **证据1**: Retrieval-Augmented Generation for Knowledge-Intensive NLP Tasks
- **证据2**: This comprehensive review paper offers a detailed examination of the progression of RAG paradigms, encompassing the Naive RAG, the Advanced RAG, and the Modular RAG. It meticulously scrutinizes the tripartite foundation of RAG frameworks, which includes the retrieval, the generation and the augmentation techniques. The paper highlights the state-of-theart technologies embedded in each of these cri
- **GT**: Paper A is a primary research contribution that introduces RAG itself as a method for knowledge-intensive NLP tasks, combining a parametric seq2seq generator with a non-parametric dense retrieval index so that generation is conditioned on retrieved passages. Paper B, by contrast, is a survey/review that does not propose a new RAG model but instead organizes the field's development into three paradigms—Naive RAG, Advanced RAG, and Modular RAG—and dissects RAG frameworks into retrieval, generation, and augmentation components. Paper B also catalogs state-of-the-art techniques for each component and introduces an up-to-date evaluation framework and benchmark, whereas Paper A's focus is on the model and task performance itself. Thus Paper A supplies the foundational method, while Paper B supplies a systematic taxonomy, technology survey, and evaluation scaffolding built on top of that line of work.
- 来源: 2005.11401, 2312.10997 | 备注: 

## cpc-024 [cross_paper_comparison] intent=multi_hop verify=✗ The evidence only provides a title for RAPTOR with no details about recursive abstractive processing, tree-organized retrieval, or index-side intervention, so the claim's RAPTOR description is unsupported.
- **Q**: Query2doc and RAPTOR both use LLMs to improve retrieval, but they intervene at different stages of the pipeline. How do the two approaches differ in terms of what they generate and how that generated content is used by the retriever?
- **证据1**: The proposed method first generates pseudo-documents by few-shot prompting large language models (LLMs), and then expands the query with generated pseudodocuments. LLMs are trained on web-scale text corpora and are adept at knowledge memorization. The pseudo-documents from LLMs often contain highly relevant information that can aid in query disambiguation and guide the retrievers. Experimental res
- **证据2**: RAPTOR: RECURSIVE ABSTRACTIVE PROCESSING FOR TREE-ORGANIZED RETRIEVAL
- **GT**: Query2doc intervenes on the query side: it uses few-shot prompting of LLMs to generate pseudo-documents, then expands the original query with these generated pseudo-documents so that the retriever (sparse or dense) sees a richer query containing relevant, disambiguating information. RAPTOR instead intervenes on the corpus/index side, recursively and abstractively processing documents to build a tree-organized retrieval structure. Thus Query2doc's LLM output is consumed as extra query text at retrieval time, whereas RAPTOR's LLM-generated abstractions are embedded into the index hierarchy itself. Both exploit LLM knowledge to bridge the gap between short queries and relevant content, but Query2doc requires no model fine-tuning and boosts BM25 by 3%–15% on datasets like MSMARCO and TREC DL, while RAPTOR restructures how documents are represented and retrieved.
- 来源: 2303.07678, 2401.18059 | 备注: 

## cpc-025 [cross_paper_comparison] intent=multi_hop verify=✗ 证据仅列出两篇论文标题，未包含任何关于 ReAct 推理-行动交替机制、RAG 检索器-生成器架构、知识更新方式或可解释性对比的具体内容，无法支撑 ground truth 中的各项事实性断言。
- **Q**: ReAct 与 RAG 都试图让语言模型突破"仅凭参数化知识作答"的局限，但二者在"模型与外部资源交互的方式"上采取了不同路线。请对比说明：ReAct 如何组织推理与行动的交替过程，RAG 又如何把检索结果接入生成过程，以及这种差异如何导致两者在知识更新与可解释性上的不同表现？
- **证据1**: ReAct: Synergizing Reasoning and Acting in Language Models
- **证据2**: Retrieval-Augmented Generation for Knowledge-Intensive NLP Tasks
- **GT**: ReAct 的核心是让语言模型在"推理轨迹（reasoning trace）"与"动作（action）"之间交替：模型先以自然语言生成思考，再调用外部工具（如 Wikipedia 搜索 API）获取观察结果，如此循环，从而把推理与行动交织在同一序列中。RAG 则采用"检索器—生成器"的端到端架构，把预训练的稠密检索器（如 DPR）与序列到序列生成模型结合，将检索到的文档作为隐变量（latent variable）条件化到生成过程中，使模型在解码时直接依据外部文档而非仅依赖参数记忆。因此，RAG 的知识更新只需替换非参数化的文档索引，无需重新训练模型，而 ReAct 的知识获取发生在推理时的工具调用中，同样避免了重训，但更依赖模型自主决定何时检索。在可解释性上，ReAct 的推理轨迹与动作步骤以自然语言显式呈现，人类可直接阅读其决策链条；RAG 的可解释性则主要体现在检索到的证据文档上，生成过程本身仍是黑箱式的隐变量推断。
- 来源: 2210.03629, 2005.11401 | 备注: 

## cpm-001 [cross_paper_multi_hop] intent=multi_hop verify=✗ The evidence supports Atlas's retrieval-augmentation finding and Paper B's identified gap, but it does not mention ToolLLaMA's proposed solution (API instructions, solution paths, API retriever) or the claim that Atlas's conclusion supports Paper B's premise, so those ground-truth facts are unsupported.
- **Q**: Atlas showed that a retrieval-augmented model with far fewer parameters can match or beat a much larger knowledge-storing LLM in few-shot knowledge-intensive tasks. Given that finding, what gap does the ToolLLaMA paper (Paper B) identify in current instruction tuning, and how does its proposed solution relate to the kind of capability Atlas demonstrated?
- **证据1**: Notably, Atlas reaches over 42% accuracy on Natural Questions using only 64 examples, outperforming a 540B parameters model by 3% despite having 50x fewer parameters.
- **证据2**: Although open-source LLMs, e.g., LLaMA, have achieved versatile capabilities through instruction tuning, they still lack the sophistication in performing higher-level tasks, such as appropriately interacting with tools (APIs) to fulfill complex human instruction. This deficiency is because current instruction tuning largely focuses on basic language tasks, with a relative neglect of the tool-use d
- **GT**: Atlas demonstrated that retrieval augmentation lets a smaller model (11B) outperform a 540B-parameter model on knowledge-intensive few-shot tasks like Natural Questions, showing that external retrieval can substitute for massive parameterized knowledge. Paper B argues that open-source LLMs, despite instruction tuning, still lack sophistication in higher-level tasks such as interacting with tools/APIs, because current instruction tuning focuses on basic language tasks and neglects the tool-use domain. ToolLLaMA addresses this by constructing API instructions and solution paths and training with an API retriever, extending the retrieval-augmented paradigm Atlas validated from knowledge retrieval to tool/API retrieval and use. Thus Atlas's conclusion that retrieval augmentation can compensate for model scale supports Paper B's premise that a smaller open-source LLM can be empowered to handle complex tool-use tasks via retrieval and targeted instruction tuning.
- 来源: 2208.03299, 2307.16789 | 备注: 

## cpm-002 [cross_paper_multi_hop] intent=multi_hop verify=✗ The evidence supports that ColBERT requires labeled relevance data and that HyDE generates a hypothetical document and encodes it without relevance labels or training, but it never mentions an instruction-following language model, zero-shot retrieval, or that HyDE removes the supervision bottleneck for zero-shot dense retrieval—so key parts of the ground truth are unsupported.
- **Q**: ColBERT achieves strong passage ranking through contextualized late interaction over BERT, but its design assumes a supervised setting with labeled relevance data. How does HyDE (Paper B) address the limitation that ColBERT-style dense retrieval models depend on relevance labels and task-specific training, and why does this matter for zero-shot retrieval?
- **证据1**: ColBERT introduces a late interaction architecture that applies BERT's contextualized representations to rank passages efficiently and effectively, but it operates within a supervised ranking paradigm requiring labeled relevance data.
- **证据2**: Dense retrieval has been shown successful across tasks like web search, question answering, and fact verification, with methods such as negative mining, distillation and task-specific pre-training proposed to improve the effectiveness of supervised dense retrieval models. HyDE generates a hypothetical document and encodes it into an embedding, requiring no relevance labels and no model training.
- **GT**: ColBERT improves retrieval effectiveness by applying BERT's contextualized representations through a late-interaction architecture, but like other dense retrieval models it relies on supervised relevance labels and task-specific training to be effective. HyDE addresses this by generating a hypothetical document from the query using an instruction-following language model, then encoding that synthetic document into an embedding for retrieval—without any relevance labels or model fine-tuning. This matters because it removes the dependency on labeled data and task-specific training that ColBERT-style models require, enabling precise zero-shot dense retrieval. Thus HyDE can be seen as directly tackling the supervision bottleneck that ColBERT's approach leaves unaddressed.
- 来源: 2004.12832, 2212.10496 | 备注: 

## cpm-003 [cross_paper_multi_hop] intent=multi_hop verify=✓
- **Q**: ColBERT 通过"延迟交互"（late interaction）在 BERT 之上实现了高效且有效的段落检索，但它的架构本质上仍是一个"检索—排序"式的单轮信息获取模型。若把 ColBERT 视为一个 Agent 的"检索工具"，那么按照《深入理解 AI Agent》一书的框架，ColBERT 缺少了现代 Agent 的哪些关键组成要素，才能被真正嵌入到 ReAct 循环中？
- **证据1**: ColBERT: Efficient and Effective Passage Search via Contextualized Late Interaction over BERT — 提出在 BERT 之上使用 contextualized late interaction 进行段落检索，以兼顾效率与效果。
- **证据2**: 1.1 现代Agent = LLM + 上下文+ 工具；1.1.1 观察空间与动作空间：模型与世界的接口；1.1.2 工具：Agent 的手脚；1.1.3 LLM：Agent 的大脑；1.1.4 上下文：Agent 的眼睛；1.1.5 ReAct 循环。
- **GT**: ColBERT 的贡献在于用 late interaction 在 BERT 之上兼顾检索的效率与效果，但它本质上仍是一个被动的、单轮的"查询→排序"检索模型，只提供检索结果这一种输出，本身不具备与外部世界交互的接口。而《深入理解 AI Agent》指出"现代 Agent = LLM + 上下文 + 工具"，其中工具是 Agent 的手脚、LLM 是大脑、上下文是眼睛，并通过 ReAct 循环（观察空间与动作空间）反复迭代。因此，若要把 ColBERT 作为工具嵌入 Agent，它只充当了"检索"这一动作，缺少 LLM 推理大脑、观察/动作空间接口以及 ReAct 循环所要求的迭代式决策能力，必须由外层 Agent 框架补齐这些要素，ColBERT 才能从单轮排序器升级为可被反复调用的检索工具。
- 来源: 2004.12832, AI-Agents-in-Depth-zh-CN | 备注: 

## cpm-004 [cross_paper_multi_hop] intent=multi_hop verify=✓
- **Q**: ColBERT's late-interaction design was motivated by the need to make BERT-based ranking efficient enough for large-scale retrieval, yet it still relies on a fixed, single-query retrieval stage. How does RAG-Fusion's query-generation and reciprocal-rank-fusion mechanism address the query-side limitation that ColBERT's late-interaction architecture leaves untouched, and what new failure mode does RAG-Fusion introduce that ColBERT's single-query paradigm does not have to worry about?
- **证据1**: ColBERT introduces a late interaction architecture that adapts BERT to efficient and effective passage search, retaining BERT's deep contextualized query–document interaction while enabling offline pre-computation of document representations and cheap MaxSim scoring at query time.
- **证据2**: RAG-Fusion combines RAG and reciprocal rank fusion (RRF) by generating multiple queries, reranking them with reciprocal scores and fusing the documents and scores... RAG-Fusion was able to provide accurate and comprehensive answers due to the generated queries contextualizing the original query from various perspectives. However, some answers strayed off topic when the generated queries' relevance
- **GT**: ColBERT's contribution is architectural: it keeps BERT's contextualized query–document interaction but decomposes it into cheap, pre-computable MaxSim operations, so it improves the efficiency and effectiveness of scoring a single query against a corpus rather than changing how the query itself is formed. Its late-interaction paradigm therefore leaves the query-side bottleneck open: retrieval quality is still bounded by one fixed query representation, and ColBERT offers no mechanism to reformulate or diversify the query. RAG-Fusion targets exactly this gap by generating multiple queries that contextualize the original query from various perspectives, then reranking and fusing the resulting documents with reciprocal rank fusion, which yields answers judged more accurate and comprehensive. However, this multi-query expansion introduces a failure mode absent from ColBERT's single-query setting: when the generated queries' relevance to the original query is insufficient, the answers stray off topic. Thus RAG-Fusion trades ColBERT's query-side rigidity for a new risk of query drift.
- 来源: 2004.12832, 2402.03367 | 备注: 

## cpm-005 [cross_paper_multi_hop] intent=multi_hop verify=✗ The evidence only states ColBERT's motivation (prohibitive cost of BERT's full cross-encoder interaction) and shows paper B has only an abstract; it does not contain ColBERT's conclusion about replacing it with a cheap late-interaction step preserving effectiveness, nor any basis for the claim that paper B's abstract is insufficient to judge improvement over ColBERT.
- **Q**: ColBERT's late-interaction design was motivated by the prohibitive cost of BERT's full cross-encoder query–document interaction. Given that motivation, how should one interpret the abstract of paper B (2501.09136), which is presented without any body text?
- **证据1**: ColBERT introduces a late interaction architecture that adapts BERT to efficient and effective passage search, addressing the prohibitive cost of BERT's full cross-encoder interaction.
- **证据2**: # **ABSTRACT**
- **GT**: ColBERT's core conclusion is that BERT's full cross-encoder interaction is too expensive for large-scale retrieval, so it replaces it with a cheap late-interaction step that preserves most effectiveness. Paper B (2501.09136) is presented only as an abstract with no body text, so its claims cannot be evaluated against ColBERT's cost/effectiveness trade-off. Because ColBERT established that any BERT-based ranker must justify its interaction cost, paper B's abstract alone is insufficient to judge whether it improves on or merely restates ColBERT's late-interaction compromise. Thus the ColBERT conclusion sets the evaluation criterion that paper B's truncated presentation fails to meet.
- 来源: 2004.12832, 2501.09136 | 备注: 

## cpm-006 [cross_paper_multi_hop] intent=multi_hop verify=✗ The evidence supports DPR's diagnosis and M3-Embedding's multi-linguality/multi-functionality claims, but it does not mention multi-granularity details (sentences to 8,192-token documents), self-knowledge distillation, or batching, so the ground truth contains unsupported facts.
- **Q**: DPR's introduction frames open-domain QA as a two-stage retrieve-then-read pipeline and notes that a huge performance degradation is observed in practice (e.g., SQuAD v1.1 exact match dropping from above 80% to less than 40%), implicitly attributing the bottleneck to the retriever. Given that diagnosis, how should we interpret M3-Embedding's claim of being "distinguished for its versatility" across multi-linguality, multi-functionality, and multi-granularity — does it address the specific retrieval weakness DPR identified, or does it target a different set of problems?
- **证据1**: "a huge performance degradation is often observed in practice, indicating the needs of improving retrieval." ... "the exact match score on SQuAD v1.1 drops from above 80% to less than 40%"
- **证据2**: "distinguished for its versatility in Multi-Linguality, Multi-Functionality, and Multi-Granularity. It provides a uniform support for the semantic retrieval of more than 100 working languages. It can simultaneously accomplish the three common retrieval functionalities: dense retrieval, multi-vector retrieval, and sparse retrieval."
- **GT**: DPR diagnoses the open-domain QA bottleneck as a retrieval problem: the retriever, not the reader, causes the drop from >80% to <40% EM, so improving retrieval is the stated need. M3-Embedding does improve retrieval, but its "versatility" claim is orthogonal to DPR's diagnosis: it targets multi-linguality (>100 languages), multi-functionality (dense + multi-vector + sparse in one model), and multi-granularity (sentences to 8,192-token documents), plus training-quality innovations like self-knowledge distillation and batching. So M3-Embedding addresses breadth/coverage and training quality of retrieval rather than the single-retriever accuracy gap DPR pinpointed; it is a generalization of the retrieval stage DPR argued must be strengthened, not a direct answer to DPR's specific accuracy-degradation finding.
- 来源: 2004.04906, 2402.03216 | 备注: 

## cpm-007 [cross_paper_multi_hop] intent=multi_hop verify=✗ The evidence only shows HyDE trained no models and M3-Embedding uses self-knowledge distillation, but it lacks support for the claims about M3-Embedding's versatility across languages/functionalities/granularities, its optimized batching strategy, or HyDE's conclusion about achieving precise dense retrieval without relevance labels.
- **Q**: HyDE (Paper A) deliberately avoids training or fine-tuning any model and relies on a zero-shot, label-free pipeline to improve dense retrieval. Given that design choice, what specific capability gap does M3-Embedding (Paper B) claim to fill, and why can M3-Embedding's approach not be considered a direct substitute for HyDE's zero-shot setting?
- **证据1**: "1No models were trained or fine-tuned in making this preprint."
- **证据2**: "we propose a novel self-knowledge distillation approach, where the relevance scores from different retrieval functionalities can be integrated as the teacher signal to enhance the training quality."
- **GT**: HyDE's core conclusion is that precise dense retrieval can be achieved without relevance labels and without training or fine-tuning any model, making it a purely zero-shot, inference-time method. M3-Embedding, by contrast, addresses versatility across languages, retrieval functionalities, and granularities, but it does so through an effective training recipe—notably self-knowledge distillation that integrates relevance scores from different retrieval functionalities as teacher signals, plus an optimized batching strategy for large batch sizes. Therefore M3-Embedding is a supervised/trained embedding model that improves embedding discriminativeness, whereas HyDE explicitly requires no training. Because M3-Embedding's gains depend on a training procedure and teacher signals, it cannot directly substitute for HyDE's label-free, training-free zero-shot retrieval setting; the two operate under fundamentally different assumptions about supervision.
- 来源: 2212.10496, 2402.03216 | 备注: 

## cpm-008 [cross_paper_multi_hop] intent=multi_hop verify=✗ The evidence only shows Paper A flags the bias-vs-size trade-off as a future direction and a bare "# **Abstract**" header; it contains no information about Paper B (Reflexion), its self-reflection/episodic memory mechanism, or whether it relies on A's compact representations, so the ground truth's claims about B are unsupported.
- **Q**: Matryoshka Representation Learning (Paper A) explicitly flags the trade-off between representation size and the tendency to encode biases as an open future direction, and its checklist confirms this was not resolved within the paper. How does this unresolved limitation shape how we should interpret the claims of Paper B (Reflexion, 2303.11366), and does Paper B's approach address or sidestep the bias-vs-size problem A left open?
- **证据1**: "a study on the trade-off between representation size and the tendency to encode biases is an interesting future direction along the lines of existing literature [36, 37]. A part of this is already presented in Section 5."
- **证据2**: "# **Abstract**"
- **GT**: Paper A leaves open the question of how compressing representations (smaller Matryoshka sizes) affects the tendency to encode biases, treating it only as an "interesting future direction" rather than a solved problem. This means any downstream method that relies on A's compact representations—such as Paper B's Reflexion, which uses self-reflection to improve agent behavior—cannot assume that smaller embeddings are bias-neutral; the bias/size trade-off remains an unverified risk. Paper B does not directly address this limitation: Reflexion operates at the level of verbal self-reflection and episodic memory for language agents, not at the level of representation compression, so it neither resolves nor explicitly measures the bias-vs-size trade-off A identified. Thus B should be read as complementary rather than as a solution to A's open problem.
- 来源: 2205.13147, 2303.11366 | 备注: 

## cpm-009 [cross_paper_multi_hop] intent=multi_hop verify=✓
- **Q**: Matryoshka Representation Learning (Paper A) explicitly flags the trade-off between representation size and the tendency to encode biases as an open future direction. How does the GraphRAG approach in Paper B relate to this limitation — does it resolve the bias-vs-compression problem, or does it sidestep it by operating at a different level of the pipeline?
- **证据1**: "However, a study on the trade-off between representation size and the tendency to encode biases is an interesting future direction along the lines of existing literature [36, 37]. A part of this is already presented in Section 5."
- **证据2**: "From Local to Global: A GraphRAG Approach to Query-Focused Summarization" — the paper's contribution is a graph-based indexing and community-summarization method for query-focused summarization, not a study of embedding size, compression, or encoded bias.
- **GT**: Paper A (Matryoshka Representation Learning) leaves open the question of how representation size trades off against the tendency to encode biases, explicitly naming it as an interesting future direction and only partially addressing it. Paper B (GraphRAG) does not resolve this bias-vs-compression trade-off at all: it is a query-focused summarization approach that builds a graph index and generates community summaries, operating at the retrieval/summarization level rather than at the level of learned embedding representations. Therefore GraphRAG sidesteps rather than solves A's open problem — it neither measures nor mitigates bias encoded in compressed representations, because its contribution lies in the indexing and summarization pipeline, not in representation learning.
- 来源: 2205.13147, 2404.16130 | 备注: 

## cpm-010 [cross_paper_multi_hop] intent=multi_hop verify=✓
- **Q**: Matryoshka Representation Learning (Paper A) explicitly flags the trade-off between representation size and the tendency to encode biases as an unstudied "interesting future direction." How does the introduction of Paper B (2501.09136) frame its contribution relative to that open problem, and does Paper B's framing actually close the gap Paper A left open?
- **证据1**: "a study on the trade-off between representation size and the tendency to encode biases is an interesting future direction along the lines of existing literature [36, 37]. A part of this is already presented in Section 5."
- **证据2**: Paper B's introduction/abstract frames its contribution around its own stated problem (not the representation-size/bias trade-off), so its framing does not reference or resolve Matryoshka's flagged open direction.
- **GT**: Paper A (Matryoshka Representation Learning) states in its checklist that it does not study the trade-off between representation size and the tendency to encode biases, explicitly calling this "an interesting future direction" and noting only partial treatment in Section 5. Paper B's introduction, however, does not frame its contribution as addressing this specific representational-bias/size trade-off; its abstract/introduction positions the work around a different problem entirely. Therefore Paper B does not close the gap Paper A left open — the bias-vs-size question remains an open direction, and Paper B's framing is orthogonal to (rather than a response to) Paper A's stated limitation.
- 来源: 2205.13147, 2501.09136 | 备注: 

## cpm-011 [cross_paper_multi_hop] intent=multi_hop verify=✗ The evidence only shows MRL flags the size-vs-bias trade-off as future work and that Toolformer is self-supervised API-calling; it does not state MRL leaves open adaptive representation-size/capability selection at inference time, nor that MRL's flexibility is baked into nested representation geometry, nor that Toolformer solves the adaptive-selection problem MRL leaves unaddressed.
- **Q**: Matryoshka Representation Learning (Paper A) reports that its flexible-size representations are competitive with fixed-size baselines and even suggests studying the trade-off between representation size and encoded biases, but it does not address whether a language model can autonomously decide when to invoke an external capability. How does Toolformer (Paper B) address the gap that MRL leaves open, and why does Toolformer's self-supervised API-calling mechanism represent a different solution to the same underlying problem of "getting the best of both worlds" that MRL pursues through nested representations?
- **证据1**: "However, a study on the trade-off between representation size and the tendency to encode biases is an interesting future direction along the lines of existing literature [36, 37]. A part of this is already presented in Section 5."
- **证据2**: "We introduce Toolformer, a model trained to decide which APIs to call, when to call them, what arguments to pass, and how to best incorporate the results into future token prediction. This is done in a self-supervised way, requiring nothing more than a handful of demonstrations for each API."
- **GT**: MRL (Paper A) leaves open the question of how a model can adaptively choose the right representation size/capability at inference time; it only shows that nested representations can be trained and that smaller sizes remain competitive, and it explicitly flags the size-vs-bias trade-off as future work rather than solving adaptive selection. Toolformer (Paper B) addresses this by training an LM to decide which APIs to call, when, with what arguments, and how to incorporate results, all in a self-supervised way requiring only a handful of demonstrations per API. Both papers pursue a "best of both worlds" goal — MRL by making one model serve many representation budgets, Toolformer by letting one LM combine its own language abilities with external tools for arithmetic, lookup, translation, etc. The key difference is that MRL's flexibility is baked into the representation geometry (nested subspaces), whereas Toolformer's flexibility is learned as a decision policy over external tool calls, so Toolformer solves the adaptive-selection problem that MRL's conclusion leaves unaddressed.
- 来源: 2205.13147, 2302.04761 | 备注: 

## cpm-012 [cross_paper_multi_hop] intent=multi_hop verify=✗ The evidence only states Paper A noted general limitations in reliability and efficiency and that Paper B claims to address those challenges; it does not mention Paper A's conclusion about improved multi-hop reasoning, the specific unresolved problem of excessive retrieval steps or error accumulation, or Paper B proposing a "more structured agentic RAG framework," so key facts in the ground truth are unsupported.
- **Q**: Paper A (2410.05779) and Paper B (2501.09136) both address agentic retrieval-augmented generation. Based on Paper A's stated conclusion and limitations, what open problem does Paper B claim to address, and how does Paper B's framing of that problem depend on the gap Paper A left unresolved?
- **证据1**: Paper A's abstract/introduction states that agentic RAG enables iterative planning, retrieval, and reflection for multi-hop reasoning, while noting limitations in reliability and efficiency of such iterative agentic pipelines.
- **证据2**: Paper B's abstract/introduction frames its contribution as addressing the reliability and efficiency challenges of agentic RAG that prior work (including Paper A) left unresolved.
- **GT**: Paper A concludes that agentic RAG systems improve multi-hop reasoning by letting an LLM iteratively plan, retrieve, and reflect, but it leaves open the problem of how to make such iterative agentic retrieval reliable and efficient across diverse tasks without excessive retrieval steps or error accumulation. Paper B positions itself as addressing precisely this unresolved reliability/efficiency gap by proposing a more structured agentic RAG framework. Thus Paper B's contribution can only be evaluated relative to the limitation Paper A acknowledged: whether it actually resolves the reliability and efficiency issues that Paper A's conclusion left open.
- 来源: 2410.05779, 2501.09136 | 备注: 

## cpm-013 [cross_paper_multi_hop] intent=multi_hop verify=✓
- **Q**: Paper A (DPR) frames open-domain QA as a two-stage retrieve-then-read pipeline and shows that the bottleneck is the retriever, since exact match collapses from >80% on SQuAD v1.1 to <40% in the open-domain setting. Given that diagnosis, how should we interpret Paper B's (RETRO) decision to retrieve from trillions of tokens and fuse the retrieved evidence directly into the language model's forward pass, rather than retrieving a small set of passages for a separate downstream reader?
- **证据1**: "the advances of reading comprehension models suggest a much simplified two-stage framework: (1) a context retriever first selects a small subset of passages where some of them contain the answer to the question, and then (2) a machine reader can thoroughly examine the retrieved contexts and identify the correct answer... Although reducing open-domain QA to machine reading is a very reasonable str
- **证据2**: "Improving language models by retrieving from trillions of tokens" — RETRO retrieves from a database of trillions of tokens and conditions the language model on the retrieved neighbors (chunked cross-attention), integrating retrieval into the model rather than treating it as a separate pre-filtering stage feeding a downstream reader.
- **GT**: DPR's conclusion is that the two-stage framework's weakness lies in retrieval quality, not in the reader, because the reader degrades sharply (SQuAD EM >80% → <40%) when it must operate over retrieved contexts. RETRO can therefore be read as attacking the same diagnosed bottleneck but at a different level: instead of improving a small passage retriever to feed a separate reader, it scales retrieval to trillions of tokens and conditions the LM itself on retrieved neighbors via chunked cross-attention, so retrieval and generation are jointly modeled rather than pipelined. This means RETRO does not simply "fix" DPR's retriever; it questions DPR's architectural premise that retrieval should be a discrete, small-candidate pre-filtering stage for a downstream reader. The two works are complementary in motivation (retrieval is the key lever for knowledge-intensive tasks) but divergent in solution: DPR optimizes the retriever within a two-stage pipeline, whereas RETRO dissolves the pipeline boundary by making retrieval an intrinsic part of the model.
- 来源: 2004.04906, 2112.04426 | 备注: 

## cpm-014 [cross_paper_multi_hop] intent=multi_hop verify=✗ The evidence only contains E5's single-vector claim and a bare outline of B's sections (1.1, 1.1.1, 1.1.5, 1.2); it does not include the specific claims attributed to B (LLM as "brain" 1.1.3, context as "eyes" 1.1.4, tools as "hands" 1.1.2), nor any statement that a static embedding cannot adapt at inference time or that the Harness layer compensates—so key facts in the ground truth are unsupported.
- **Q**: Paper A (E5) claims that a single-vector embedding trained with weak supervision can serve as a general-purpose representation for retrieval, clustering, and classification, and that it beats BM25 zero-shot on BEIR. Paper B describes an AI Agent as "LLM + 上下文 + 工具" with a ReAct loop and a "Harness 工程" layer. Given A's claim that one fixed embedding vector suffices for any task, what limitation of that single-vector assumption does B's architecture expose, and how does B's design compensate for it?
- **证据1**: "E5 can be readily used as a general-purpose embedding model for any tasks requiring a single-vector representation of texts such as retrieval, clustering, and classification, achieving strong performance in both zero-shot and fine-tuned settings."
- **证据2**: "1.1 现代Agent = LLM + 上下文+ 工具 ... 1.1.1 观察空间与动作空间：模型与世界的接口 ... 1.1.5 ReAct 循环 ... 1.2 Harness 工程：模型之外的竞争力"
- **GT**: E5 (Paper A) assumes a single, task-agnostic vector representation is sufficient for retrieval, clustering, and classification, with the model itself being the source of capability. Paper B's architecture, however, treats the LLM as only the "brain" (1.1.3) and insists that an Agent = LLM + 上下文 + 工具, with the observation/action space (1.1.1) as the interface to the world and a ReAct loop (1.1.5) that iteratively interleaves reasoning and acting. This exposes the limitation that a static single-vector embedding cannot adapt its representation to new observations or task feedback at inference time. B compensates by externalizing capability into the context (the "eyes", 1.1.4), tools (the "hands", 1.1.2), and the Harness engineering layer (1.2), which together supply the dynamic, task-specific information that a frozen embedding must otherwise encode in advance.
- 来源: 2212.03533, AI-Agents-in-Depth-zh-CN | 备注: 

## cpm-015 [cross_paper_multi_hop] intent=multi_hop verify=✗ The evidence only states that GraphRAG builds a graph index with community summaries and that LightRAG uses dual-level retrieval, but it never mentions GraphRAG's LLM-based community detection/summarization being expensive or slow to update, nor that LightRAG avoids that pipeline or is more efficient/scalable—so key claims in the ground truth are unsupported.
- **Q**: Paper A (GraphRAG) argues that baseline RAG fails on global, query-focused summarization because it cannot aggregate information across an entire corpus. Paper B (LightRAG) proposes a dual-level retrieval architecture. How does Paper B's design specifically address the scalability and cost limitations that Paper A's graph-based global summarization approach leaves open?
- **证据1**: GraphRAG: baseline RAG fails on global questions directed at an entire text corpus, such as "What are the main themes in the dataset?", since this is a query-focused summarization task rather than an explicit retrieval task; the approach builds a graph index with community summaries to answer such global questions.
- **证据2**: LightRAG: proposes a dual-level retrieval paradigm that integrates graph structures into text indexing and querying, enabling comprehensive retrieval of both low-level (specific entities) and high-level (broad themes/concepts) information, thereby handling both local and global queries efficiently.
- **GT**: Paper A's GraphRAG shows that baseline RAG cannot answer global, query-focused summarization questions because it only retrieves local, top-k text chunks and cannot aggregate information across the whole corpus; its solution builds a hierarchical entity graph with community summaries, but this requires expensive LLM-based community detection and summarization over the entire graph, which is costly and slow to update. Paper B's LightRAG addresses exactly this open problem by combining graph structures with a dual-level retrieval paradigm (low-level for specific entities, high-level for broad themes), which captures both local and global information while avoiding the heavy community-summarization pipeline. Thus LightRAG is positioned as a more efficient, scalable alternative that preserves GraphRAG's global-awareness advantage at lower cost.
- 来源: 2404.16130, 2410.05779 | 备注: 

## cpm-016 [cross_paper_multi_hop] intent=multi_hop verify=✗ The evidence supports that Reflexion relies on reward/unit-test signals and that GraphRAG uses LLM-generated community summaries with map-reduce aggregation, but it does not state that Reflexion "cannot be applied" to reward-free tasks, nor that GraphRAG "sidesteps" the problem or is "complementary-but-not-a-solution"—those interpretive claims go beyond the provided excerpts.
- **Q**: Paper A (Reflexion, 2303.11366) frames its contribution as verbal reinforcement learning that converts sparse binary environment feedback into linguistic self-reflections stored in an episodic memory buffer, but it explicitly limits its evaluation to decision-making, coding, and reasoning tasks where a scalar or binary reward signal is available to trigger reflection. Given that limitation, how should we interpret Paper B's (GraphRAG, 2404.16130) claim that a graph-based retrieval-augmented generation pipeline improves "global" query-focused summarization over a corpus? Specifically, does GraphRAG solve the problem Reflexion left open, or does it sidestep it by replacing the missing reward signal with a different mechanism?
- **证据1**: Reflexion: "we introduce Reflexion, a framework that equips agents with dynamic memory and self-reflection capabilities... converting sparse binary or scalar reward signals into verbal self-reflections stored in an episodic memory buffer." Its evaluations are confined to tasks with verifiable outcomes (ALFWorld, HotPotQA, HumanEval/MBPP), i.e., settings where a reward or unit-test signal exists to
- **证据2**: GraphRAG: "we propose a graph-based retrieval-augmented generation (RAG) approach... to answer global questions about an entire text corpus... using LLM-generated community summaries and a map-reduce approach to produce partial responses that are aggregated into a final answer."
- **GT**: Reflexion's contribution depends on an external scalar/binary reward (or unit-test pass/fail) to decide when a self-reflection is warranted, so it cannot be applied to open-ended, reward-free tasks such as whole-corpus summarization. GraphRAG does not supply such a reward signal; instead it sidesteps the problem by changing the task formulation and the retrieval substrate: it builds an LLM-derived entity/knowledge graph with community summaries and uses a map-reduce style hierarchical aggregation to answer query-focused summarization questions over an entire corpus. Thus GraphRAG addresses the *symptom* Reflexion left open (no way to improve on tasks without verifiable feedback) by removing the need for iterative self-correction altogether, rather than by extending Reflexion's verbal reinforcement learning to the reward-free setting. The correct interpretation is therefore that B is complementary-but-not-a-solution: it substitutes graph-structured global context for Reflexion's reflection-on-reward loop.
- 来源: 2303.11366, 2404.16130 | 备注: 

## cpm-017 [cross_paper_multi_hop] intent=multi_hop verify=✗ The evidence supports Paper A's finding and Paper B's "LLM + 上下文 + 工具" and Harness 工程 framing, but it does not contain the claimed "brain/eyes/hands" metaphor, nor any statement that RAG-Fusion's drift is a context/harness failure or that the fix is to engineer the loop rather than swap in a stronger LLM—those are inferences beyond the excerpts.
- **Q**: Paper A concludes that RAG-Fusion's generated queries can cause answers to stray off topic when those queries' relevance to the original query is insufficient. How does Paper B's framing of a modern Agent as "LLM + 上下文 + 工具" with a ReAct loop and "Harness 工程" reframe this failure — i.e., is the off-topic drift a flaw of the LLM itself or of the surrounding harness/context engineering, and what does that imply for fixing RAG-Fusion?
- **证据1**: "I found that RAG-Fusion was able to provide accurate and comprehensive answers due to the generated queries contextualizing the original query from various perspectives. However, some answers strayed off topic when the generated queries' relevance to the original query is insufficient."
- **证据2**: "1.1 现代Agent = LLM + 上下文+ 工具" ... "1.1.1 观察空间与动作空间：模型与世界的接口" ... "1.2 Harness 工程：模型之外的竞争力" ... "1.2.1 从提示工程到Loop 工程：工程范式的演进"
- **GT**: Paper A's evaluation shows RAG-Fusion improves accuracy and comprehensiveness because generated queries contextualize the original query from multiple perspectives, but it fails when those generated queries are insufficiently relevant to the original query, causing answers to stray off topic. Paper B reframes such failures by defining a modern Agent as LLM + 上下文 + 工具, where the LLM is only the "brain" while context is the "eyes" and tools are the "hands," and by emphasizing Harness 工程 (the engineering around the model) as the real source of competitiveness, evolving from prompt engineering to loop engineering. Read together, RAG-Fusion's off-topic drift is not primarily an LLM capability failure but a context/harness failure: the query-generation and RRF fusion step is part of the harness that shapes the agent's observation space, so the fix is to engineer that loop (e.g., constrain or verify generated-query relevance) rather than to swap in a stronger LLM. This means Paper A's limitation is addressable at the harness level, which Paper B treats as the locus of competitive advantage.
- 来源: 2402.03367, AI-Agents-in-Depth-zh-CN | 备注: 

## cpm-018 [cross_paper_multi_hop] intent=multi_hop verify=✗ The evidence supports the general claims about RETRO's single forward pass and SELF-REFINE's iterative feedback/refinement improving outputs by ~20%, but it does not mention the specific evaluation details in the ground truth: 7 diverse tasks, dialog response generation to mathematical reasoning, or GPT-3.5 and GPT-4.
- **Q**: RETRO (Paper A) improves language models by retrieving from trillions of tokens, yet it still relies on a single forward pass to produce its output. Given that limitation, how does SELF-REFINE (Paper B) offer a complementary way to improve an LLM's output at test time, and what does SELF-REFINE's evaluation show about whether even a strong retrieval-augmented or state-of-the-art LLM's first-pass output is optimal?
- **证据1**: RETRO (Paper A) improves language models by retrieving from trillions of tokens, enhancing predictions via a massive retrieval database, but it produces its output in a single forward pass without any iterative refinement of that output.
- **证据2**: "Like humans, large language models (LLMs) do not always generate the best output on their first try... SELF-REFINE does not require any supervised training data, additional training, or reinforcement learning... Across all evaluated tasks, outputs generated with SELF-REFINE are preferred by humans and automatic metrics over those generated with the same LLM using conventional one-step generation,
- **GT**: RETRO augments a language model with a massive retrieval database (trillions of tokens) to improve its predictions, but it still generates output in a single forward pass and does not iteratively revise that output. SELF-REFINE addresses exactly this gap by having the same LLM generate an initial output, then provide feedback on it and refine itself iteratively, without any supervised training data, additional training, or reinforcement learning. Evaluated across 7 diverse tasks (from dialog response generation to mathematical reasoning) with GPT-3.5 and GPT-4, SELF-REFINE outputs are preferred by humans and automatic metrics over conventional one-step generation, improving task performance by ~20% absolute on average. This shows that even state-of-the-art LLMs do not produce their best output on the first try, so test-time iterative refinement is a complementary improvement axis to RETRO's retrieval-based scaling.
- 来源: 2112.04426, 2303.17651 | 备注: 

## cpm-019 [cross_paper_multi_hop] intent=multi_hop verify=✗ The evidence supports RETRO's fixed non-differentiable retrieval and Toolformer's learned API-calling decision, but the ground truth adds unsupported specifics—the list of APIs (calculator, QA, search, translation, calendar) and the claim of improving zero-shot performance without sacrificing core language modeling—that do not appear in the evidence.
- **Q**: RETRO (Paper A) scales retrieval to trillions of tokens via a frozen BERT-embedding nearest-neighbour index and shows large perplexity gains, yet it keeps the retrieval mechanism fixed and non-differentiable. How does Toolformer (Paper B) address the specific limitation that RETRO's retrieval is a static, hand-designed component that the LM cannot itself decide when or how to invoke?
- **证据1**: RETRO combines a 2 trillion token database with a retrieval-enhanced autoregressive language model, using a frozen BERT-embedded nearest-neighbour index; the retrieval is a fixed, non-differentiable component rather than something the model learns to control.
- **证据2**: We introduce Toolformer, a model trained to decide which APIs to call, when to call them, what arguments to pass, and how to best incorporate the results into future token prediction. This is done in a self-supervised way, requiring nothing more than a handful of demonstrations for each API.
- **GT**: RETRO demonstrates that conditioning an LM on retrieved chunks from a trillion-token datastore yields substantial gains, but its retrieval is a fixed, non-differentiable nearest-neighbour lookup over frozen BERT embeddings—the model never learns when retrieval is useful or how to integrate it. Toolformer addresses exactly this gap by making tool/API invocation a learned, self-supervised decision: the LM itself decides which API to call, when, with what arguments, and how to fold the result into future token prediction, using only a handful of demonstrations per API. Thus where RETRO supplies a static retrieval module, Toolformer turns external access (calculator, QA, search, translation, calendar) into an LM-controlled action, improving zero-shot performance without sacrificing core language modeling.
- 来源: 2112.04426, 2302.04761 | 备注: 

## cpm-020 [cross_paper_multi_hop] intent=multi_hop verify=✗ The evidence confirms ReAct's limitation and lists ToolLLaMA's pipeline components (API Collection, Instruction Generation, Solution Path Annotation, API Retriever, ToolLLaMA, ToolEval), but it does not mention RapidAPI, thousands of candidates, or fine-tuning LLaMA on the data, so key specifics of the ground truth are unsupported.
- **Q**: ReAct (Paper A) demonstrated that interleaving reasoning traces with actions lets LLMs solve knowledge-intensive tasks, but it relied on a small set of hand-crafted, task-specific action spaces and was evaluated only on a few benchmarks. How does ToolLLaMA (Paper B) address the limitation that ReAct left open, and how does its data-construction and evaluation design (API collection, instruction generation, solution-path annotation, API retriever, ToolEval) specifically overcome the problem of scaling tool use beyond ReAct's narrow, hand-designed action space?
- **证据1**: ReAct: Synergizing Reasoning and Acting in Language Models — the paper's core contribution is interleaving reasoning traces with task-specific actions (e.g., search/lookup on Wikipedia) and its limitation is that the action space is small, hand-crafted, and benchmark-specific.
- **证据2**: Tool learning aims to unleash the power of LLMs to effectively interact with various tools (APIs) to accomplish complex tasks... current instruction tuning largely focuses on basic language tasks, with a relative neglect of the tool-use domain... Data Construction & Train & Inference: API Collection, Instruction Generation, Solution Path Annotation, API Retriever, ToolLLaMA, ToolEval.
- **GT**: ReAct showed that interleaving reasoning and acting works, but its action space was small, hand-crafted, and task-specific (e.g., Wikipedia search/lookup), so it could not generalize to the vast, heterogeneous API ecosystem. ToolLLaMA addresses this by building a scalable tool-learning pipeline: it collects a large set of real-world APIs (from RapidAPI), auto-generates diverse instructions, annotates solution paths, trains an API retriever to select relevant APIs from thousands of candidates, and fine-tunes LLaMA on this data. It also introduces ToolEval for automatic evaluation. Thus, where ReAct proved the concept with a handful of curated actions, ToolLLaMA operationalizes it at scale by replacing hand-designed action spaces with retrieved, real-world APIs and instruction-tuned tool use.
- 来源: 2210.03629, 2307.16789 | 备注: 

## cpm-021 [cross_paper_multi_hop] intent=multi_hop verify=✗ The evidence supports ReAct's tool-grounding mechanism and SELF-REFINE's no-training self-improvement with ~20% average gains, but it does not mention "7 tasks" or "GPT-3.5/GPT-4," nor does it state that the two methods are complementary or specify when each is preferable, so those ground-truth facts are unsupported.
- **Q**: ReAct (Paper A) shows that interleaving reasoning traces with actions lets LLMs use external tools like Wikipedia to overcome hallucination and error propagation, but its gains depend on having a tool/environment to act on. Given this limitation, how should we interpret SELF-REFINE's (Paper B) claim that a single LLM can improve itself at test time with no external tools or training—and what does that imply about the two methods' applicability?
- **证据1**: ReAct: synergizing reasoning and acting in language models — interleaves reasoning traces with task-specific actions, where actions allow interaction with external sources such as Wikipedia, and this reduces hallucination and error propagation compared to reasoning-only baselines.
- **证据2**: SELF-REFINE does not require any supervised training data, additional training, or reinforcement learning, and instead uses a single LLM as the generator, refiner and the feedback provider... outputs generated with SELF-REFINE are preferred by humans and automatic metrics over those generated with the same LLM using conventional one-step generation, improving by ~20% absolute on average.
- **GT**: ReAct's conclusion is that grounding reasoning in actions against an external source (e.g., Wikipedia) is what reduces hallucination and error propagation, so its improvement mechanism is tied to having an interactive environment/tool. SELF-REFINE, by contrast, claims improvement comes purely from the same LLM generating feedback and refining its own output, with no supervised data, extra training, or reinforcement learning, and reports ~20% absolute average gains across 7 tasks with GPT-3.5/GPT-4. Read together, SELF-REFINE suggests that the external-tool grounding ReAct relies on is not strictly necessary for test-time gains, meaning the two approaches are complementary rather than competing: ReAct is preferable when a reliable external knowledge source/action space exists, while SELF-REFINE is applicable when no such environment is available but the model can critique itself.
- 来源: 2210.03629, 2303.17651 | 备注: 

## cpm-022 [cross_paper_multi_hop] intent=multi_hop verify=✗ The evidence only states that current instruction tuning neglects the tool-use domain; it does not mention LLaMA's inability to interact with APIs, the reasoning that self-feedback cannot supply missing tool-use supervision, or ToolLLaMA's specific pipeline (API collection, instruction generation, solution-path annotation, API retriever, SFT on ToolBench, ToolEval).
- **Q**: SELF-REFINE shows that a single LLM can iteratively improve its own outputs at test time without any training, yet it evaluates this only on tasks like dialog generation and math reasoning. Given that limitation, what specific deficiency does the ToolLLaMA paper identify in current instruction tuning that SELF-REFINE's training-free, self-feedback paradigm cannot address, and why does it require the different solution ToolLLaMA proposes?
- **证据1**: SELF-REFINE does not require any supervised training data, additional training, or reinforcement learning, and instead uses a single LLM as the generator, refiner and the feedback provider. We evaluate SELF-REFINE across 7 diverse tasks, ranging from dialog response generation to mathematical reasoning...
- **证据2**: This deficiency is because current instruction tuning largely focuses on basic language tasks, with a relative neglect of the tool-use domain.
- **GT**: SELF-REFINE demonstrates that a single LLM can improve its own outputs through iterative self-feedback with no supervised training, extra training, or reinforcement learning, but it only validates this on general language tasks such as dialog response generation and mathematical reasoning. The ToolLLaMA paper argues that current instruction tuning largely focuses on basic language tasks while relatively neglecting the tool-use domain, leaving even capable open-source LLMs like LLaMA unable to appropriately interact with APIs to fulfill complex human instructions. Because this deficiency stems from a gap in the training data/domain rather than from suboptimal single-pass generation, SELF-REFINE's test-time self-refinement cannot fix it: no amount of self-feedback supplies the missing tool-use supervision. ToolLLaMA therefore addresses it with a data-construction and training pipeline (API collection, instruction generation, solution-path annotation, an API retriever, SFT on ToolBench, and ToolEval), i.e., it must add the tool-use domain knowledge that SELF-REFINE deliberately avoids acquiring.
- 来源: 2303.17651, 2307.16789 | 备注: 

## cpm-023 [cross_paper_multi_hop] intent=multi_hop verify=✗ The evidence supports Toolformer's self-supervised API-calling and SELF-REFINE's iterative feedback/refinement with ~20% average gain, but it never states Toolformer's decision is single/one-shot with no correction loop, never says SELF-REFINE can be layered on a tool-augmented model to fix bad API calls, and never mentions 7 tasks or GPT-3.5/GPT-4, so key parts of the ground truth are unsupported.
- **Q**: Toolformer shows that an LM can self-supervise its own API calls (calculator, QA, search) with no extra training data and no loss of core language modeling ability, yet it commits to a single, one-shot decision about which API to call and how to fold the result into the next token. Given that Toolformer's tool use is a fixed, single-pass decision with no mechanism for revisiting a bad call or a poorly integrated result, how does SELF-REFINE's design address exactly this limitation, and why does that make SELF-REFINE's ~20% absolute average gain across 7 tasks a meaningful complement to Toolformer rather than a redundant result?
- **证据1**: "We introduce Toolformer, a model trained to decide which APIs to call, when to call them, what arguments to pass, and how to best incorporate the results into future token prediction. This is done in a self-supervised way, requiring nothing more than a handful of demonstrations for each API."
- **证据2**: "The main idea is to generate an initial output using an LLM; then, the same LLM provides feedback for its output and uses it to refine itself, iteratively. SELF-REFINE does not require any supervised training data, additional training, or reinforcement learning... outputs generated with SELF-REFINE are preferred by humans and automatic metrics over those generated with the same LLM using conventi
- **GT**: Toolformer's contribution is a self-supervised scheme in which the LM decides which API to call, what arguments to pass, and how to incorporate the result into future token prediction — but this is a single, one-shot decision made at generation time, with no loop for detecting or correcting a wrong call or a badly integrated tool output. SELF-REFINE targets precisely this gap: it generates an initial output, then has the same LLM produce feedback on that output and refine itself iteratively, with no supervised data, additional training, or RL. Because SELF-REFINE operates purely at test time on the model's own output, it can be layered on top of a tool-augmented model like Toolformer to catch and repair bad API calls or poor result integration. This is why its ~20% absolute average improvement across 7 diverse tasks (dialog to math reasoning, GPT-3.5/GPT-4) is complementary rather than redundant: Toolformer improves what the model can access in one pass, while SELF-REFINE improves the model's ability to critique and fix that pass.
- 来源: 2302.04761, 2303.17651 | 备注: 

## cpm-024 [cross_paper_multi_hop] intent=multi_hop verify=✗ The evidence supports the Toolformer/Query2doc contrast and the parametric-memory interpretation, but it never mentions Query2doc's "3–15% BM25 gains" or improvements to dense retrievers, so that specific fact in the ground truth is unsupported.
- **Q**: Toolformer shows that an LM can teach itself to call external tools (e.g., a search engine or Q&A API) and fold the returned results into its own token predictions, achieving strong zero-shot gains without losing language-modeling ability. Query2doc, by contrast, never calls any tool at inference time — it only uses an LLM's own generated text to expand queries. Given Toolformer's demonstration that tool/API outputs can be injected into a model's context to improve downstream predictions, how should we interpret Query2doc's claim that LLM-generated pseudo-documents "contain highly relevant information that can aid in query disambiguation," and what does this comparison reveal about the source of Query2doc's gains?
- **证据1**: We introduce Toolformer, a model trained to decide which APIs to call, when to call them, what arguments to pass, and how to best incorporate the results into future token prediction. This is done in a self-supervised way... We incorporate a range of tools, including a calculator, a Q&A system, a search engine, a translation system, and a calendar. Toolformer achieves substantially improved zero-s
- **证据2**: The proposed method first generates pseudo-documents by few-shot prompting large language models (LLMs), and then expands the query with generated pseudodocuments. LLMs are trained on web-scale text corpora and are adept at knowledge memorization. The pseudo-documents from LLMs often contain highly relevant information that can aid in query disambiguation and guide the retrievers.
- **GT**: Toolformer establishes that an LM can be trained to decide when to invoke an external API and to incorporate the returned result (e.g., a search-engine or Q&A answer) directly into its context to improve subsequent token prediction, so external, retrieved information is a proven source of downstream gains. Query2doc does not invoke any such API; it instead relies solely on the LLM's own few-shot-generated pseudo-documents, which it appends to the query to expand it. Read against Toolformer, Query2doc's "highly relevant information" is therefore not externally retrieved evidence but internally generated, memorized knowledge — the LLM's parametric memory rather than a tool's output. The comparison shows that Query2doc's 3–15% BM25 gains and its improvements to dense retrievers come from exploiting the LLM as a knowledge source for query disambiguation, not from any tool-use or retrieval-augmentation mechanism of the kind Toolformer validates.
- 来源: 2302.04761, 2303.07678 | 备注: 

## cpm-025 [cross_paper_multi_hop] intent=multi_hop verify=✗ 证据仅包含 Toolformer 的简介和《深入理解 AI Agent》的章节标题（"现代Agent = LLM + 上下文 + 工具"、"观察空间与动作空间"、"ReAct 循环"），并未说明"工具是 Agent 的手脚"、上下文是"Agent 的眼睛"、Toolformer 调用是"单步、无状态"或缺少上下文与循环控制等具体论断，故 ground truth 中多项事实无证据支撑。
- **Q**: Toolformer 用自监督方式让 LLM 学会调用 API，但它的工具调用是"单步、即时嵌入 token 流"的；结合《深入理解 AI Agent》中"现代 Agent = LLM + 上下文 + 工具"以及 ReAct 循环的框架，Toolformer 所展示的能力在多大程度上构成了一个完整的 Agent，它缺少了该框架中的哪些关键要素？
- **证据1**: "We introduce Toolformer, a model trained to decide which APIs to call, when to call them, what arguments to pass, and how to best incorporate the results into future token prediction. This is done in a self-supervised way, requiring nothing more than a handful of demonstrations for each API."
- **证据2**: "1.1 现代Agent = LLM + 上下文+ 工具"；"1.1.1 观察空间与动作空间：模型与世界的接口"；"1.1.5 ReAct 循环"
- **GT**: Toolformer 证明了 LLM 可以通过自监督学习决定"调用哪个 API、何时调用、传什么参数、如何把结果融入后续 token 预测"，这对应《深入理解 AI Agent》框架中"工具是 Agent 的手脚"这一要素，即模型与外部世界接口的动作空间。但 Toolformer 的调用是单步、无状态的：它在生成文本时即时插入一次 API 结果并继续预测，并不存在"观察空间—动作空间"的持续交互，也没有 ReAct 式的"推理—行动—观察"循环，因此缺少该框架中的上下文（Agent 的眼睛）与循环控制这两个关键要素。换言之，Toolformer 提供的是 Agent 的"工具使用"能力，而非完整的"LLM + 上下文 + 工具"闭环 Agent。
- 来源: 2302.04761, AI-Agents-in-Depth-zh-CN | 备注: 

## tam-001 [term_ambiguity] intent=multi_hop verify=✓
- **Q**: Do the papers 2002.08909, 2004.04906, and 2004.12832 use the term "arxiv" with different meanings?
- **证据1**: 2002.08909: 'arXiv' denotes the preprint repository, cited as 'arXiv preprint arXiv:XXXX.XXXXX' or 'ArXiv, abs/XXXX.XXXXX' in the reference list
- **证据2**: 2004.04906: 'arXiv' denotes the preprint repository, cited as 'ArXiv, abs/XXXX.XXXXX' in the reference list
- **证据3**: 2004.12832: 'arXiv' denotes the preprint repository, cited as 'arXiv preprint arXiv:XXXX.XXXXX' in the reference list
- **GT**: No real divergence. In all three papers, "arXiv" (variously written "arXiv preprint arXiv:XXXX.XXXXX", "ArXiv, abs/XXXX.XXXXX", or "_arXiv preprint arXiv:XXXX.XXXXX_") is used identically: as a bibliographic venue/repository reference for citing preprints. The only differences are stylistic citation-formatting conventions (e.g., including the "abs/" prefix or italicizing the venue), not a difference in the term's meaning.
- 来源: 2002.08909, 2004.04906, 2004.12832 | 备注: 

## tam-002 [term_ambiguity] intent=multi_hop verify=✓
- **Q**: Do the papers 2002.08909, 2004.04906, and 2004.12832 use the term "conference" with different meanings?
- **证据1**: 2002.08909: A type of academic venue/meeting appearing in publication venue names (e.g., Conference on Empirical Methods in Natural Language Processing)
- **证据2**: 2004.04906: A type of academic venue/meeting appearing in publication venue names (e.g., International Conference on Learning Representations, International Conference of the Cross-Language Evaluation Forum)
- **证据3**: 2004.12832: A type of academic venue/meeting appearing in publication venue names (e.g., International ACM SIGIR Conference, International Conference on Data Engineering)
- **GT**: No real divergence. In all three papers "conference" is used in the same sense: as part of the name/venue designation of academic publication venues (e.g., "Conference on Empirical Methods in Natural Language Processing", "International Conference on Learning Representations (ICLR)", "International ACM SIGIR Conference on Research and Development in Information Retrieval", "International Conference on Data Engineering (ICDE)"). It refers to a type of academic meeting/venue where papers are published, and the term carries essentially the same meaning across the papers.
- 来源: 2002.08909, 2004.04906, 2004.12832 | 备注: 

## tam-003 [term_ambiguity] intent=multi_hop verify=✓
- **Q**: Do the papers 2002.08909, 2004.04906, and 2004.12832 use the term "learning" with different meanings?
- **证据1**: 2002.08909: training a neural language model to capture world knowledge in its parameters (pre-training/fine-tuning)
- **证据2**: 2004.04906: training dense retrieval models (question/passage encoders) to learn vector representations from labeled pairs
- **证据3**: 2004.12832: training BERT-based encoders, including a differentiable mechanism for learning to expand queries with new terms
- **GT**: No real divergence. All three papers use "learning" in the standard machine-learning sense of training/optimizing model parameters (or, in 2004.12832, a differentiable mechanism for learning to expand/re-weight queries). The meanings are essentially the same; no cross-paper meaning difference exists.
- 来源: 2002.08909, 2004.04906, 2004.12832 | 备注: 

## tam-004 [term_ambiguity] intent=multi_hop verify=✓
- **Q**: Do the papers 2002.08909, 2004.04906, and 2004.12832 use the term "picture" with different meanings?
- **证据1**: 2002.08909: 'picture' occurs only in the OCR marker '<!-- Start of picture text -->' delimiting the extracted text of a figure (bar chart comparing masking strategies); it denotes a figure/image, not a technical concept
- **证据2**: 2004.04906: 'picture' does not appear as a term in the provided context; no distinct meaning is defined
- **证据3**: 2004.12832: 'picture' occurs only in the OCR marker '<!-- Start of picture text -->' delimiting the extracted text of Figure 1 (effectiveness vs. query latency plot); it denotes a figure/image, not a technical concept
- **GT**: No real divergence. In all three papers, "picture" appears only as part of the OCR artifact marker "<!-- Start of picture text -->" / "<!-- End of picture text -->" that delimits figure content extracted from the PDF. It refers to a figure/image in the paper (e.g., a bar chart of masking strategies in 2002.08909, a scatter plot of effectiveness vs. latency in 2004.12832), not to a technical concept. The term is used with essentially the same (non-technical, artifact) meaning across the papers, so no cross-paper meaning difference exists.
- 来源: 2002.08909, 2004.04906, 2004.12832 | 备注: 

## tam-005 [term_ambiguity] intent=multi_hop verify=✓
- **Q**: Do the papers 2002.08909, 2004.04906, and 2005.11401 use the term "reasoning" with different meanings?
- **证据1**: 2002.08909: inference performed by a pre-trained representation over a large corpus of knowledge retrieved on-the-fly during inference
- **证据2**: 2004.04906: multi-hop inference over reasoning paths in a Wikipedia graph for question answering (as in the cited work)
- **证据3**: 2005.11401: entailment-style inference over retrieved Wikipedia evidence to verify a claim
- **GT**: No real divergence. In all three papers "reasoning" is used in the same general sense of performing inference/computation over retrieved knowledge or evidence. 2002.08909: reasoning as the process a pre-trained representation performs over a large corpus of knowledge on-the-fly during inference (retrieval-augmented reasoning). 2004.04906: reasoning appears only in the cited title "Learning to retrieve reasoning paths over Wikipedia graph for question answering," i.e., multi-hop reasoning over a knowledge graph to answer questions. 2005.11401: reasoning as entailment-style inference over retrieved Wikipedia evidence to classify a claim (FEVER fact verification). These are essentially the same notion of inference over retrieved evidence, so no cross-paper meaning difference exists.
- 来源: 2002.08909, 2004.04906, 2005.11401 | 备注: 

## tam-006 [term_ambiguity] intent=multi_hop verify=✓
- **Q**: Does the term "agent" carry different meanings across these papers?
- **证据1**: 2112.04426: ordinary English sense, only in the phrase 'literary agent' (a person who represents authors); not a technical term
- **证据2**: 2210.03629: technical RL/LLM sense—an entity interacting with an environment, receiving observations and taking actions via a policy, with language added to its action space
- **证据3**: 2302.04761: no technical usage of 'agent' in the provided context (only bibliographic references)
- **GT**: 2112.04426: "agent" appears only as part of the common noun phrase "literary agent" (a person who represents authors), i.e., an ordinary English occupational sense, not a technical term. 2210.03629: "agent" is a technical term denoting an entity that interacts with an environment, receiving observations ot ∈ O and taking actions at ∈ A according to a policy π(at|ct), with its action space augmented to include language (thoughts/reasoning traces). 2302.04761: "agent" does not appear as a defined technical term in the provided context (only bibliographic references are shown). Divergence: there is no genuine cross-paper technical divergence—2112.04426 uses "agent" in a non-technical, everyday sense, while 2210.03629 uses it in the standard RL/LLM technical sense; 2302.04761 provides no relevant usage. The meanings are essentially unrelated rather than conflicting technical definitions.
- 来源: 2112.04426, 2210.03629, 2302.04761 | 备注: 

## tam-007 [term_ambiguity] intent=multi_hop verify=✓
- **Q**: Does the term "natural" carry different technical meanings across papers 2002.08909, 2004.04906, and 2004.12832?
- **证据1**: 2002.08909: part of the compound 'natural language processing', referring to the general NLP field
- **证据2**: 2004.04906: part of 'natural paragraphs', meaning paragraphs as they naturally occur in text (vs. fixed-length passages)
- **证据3**: 2004.12832: part of 'Natural Language Understanding (NLU)', referring to the general NLU field
- **GT**: No real divergence. In all three papers "natural" appears only as part of fixed compound terms ("natural language processing", "natural paragraphs", "Natural Language Understanding") with its ordinary, non-technical sense. 2002.08909: "natural" occurs in "natural language processing" (the general NLP field). 2004.04906: "natural" occurs in "natural paragraphs" (paragraphs as they naturally occur in text, contrasted with fixed-length passages). 2004.12832: "natural" occurs in "Natural Language Understanding (NLU)" (the general NLU field). These are essentially the same everyday usage, not a technical term with divergent definitions, so no cross-paper meaning difference exists.
- 来源: 2002.08909, 2004.04906, 2004.12832 | 备注: 

## tam-008 [term_ambiguity] intent=multi_hop verify=✓
- **Q**: Does the term "prompt" carry different meanings across papers 2112.04426, 2208.03299, and 2210.03629?
- **证据1**: 2112.04426: The input/query format conditioning a retrieval-augmented model, with retrieved documents prepended to the prompt
- **证据2**: 2208.03299: The input context for in-context learning into which retrieved documents are added
- **证据3**: 2210.03629: The in-context examples and thought-action trajectories provided to an LLM to elicit reasoning/acting
- **GT**: 2112.04426: "Prompt" denotes the input/query format used to condition a retrieval-augmented model (e.g., the query or input text fed to the retriever/reader, with retrieved documents prepended to the prompt). 2208.03299: "Prompt" refers to the input context given to a large language model for in-context learning, into which retrieved documents are inserted as additional context. 2210.03629: "Prompt" refers to the in-context examples and task-solving trajectory (thoughts/actions) provided to the LLM to elicit reasoning and acting behavior. Divergence: While all three use "prompt" to mean the input text conditioning a model, the emphasis differs — 2112.04426 treats it as the retrieval-augmented input/query format, 2208.03299 as the in-context learning context augmented with retrieved documents, and 2210.03629 as the reasoning/acting demonstration (thought-action trajectories) for prompting methods like ReAct. These are essentially the same core notion (model input context) with different application emphases rather than a genuine terminological conflict.
- 来源: 2112.04426, 2208.03299, 2210.03629 | 备注: 

## tam-009 [term_ambiguity] intent=multi_hop verify=✓
- **Q**: Does the term "search" carry different meanings across papers 2002.08909, 2004.04906, and 2004.12832?
- **证据1**: 2002.08909: retrieval as latent-variable document selection; the retriever picks documents z from corpus Z and search is embedded in maximizing log p(y|x) via marginalization over all documents
- **证据2**: 2004.04906: efficient decomposable similarity search (e.g., inner product search) over precomputed passage representations, contrasted with sparse keyword matching like TF-IDF/BM25
- **证据3**: 2004.12832: passage search as the neural ranking task of scoring query-document pairs with a deep LM (ColBERT late interaction), focused on efficiency and effectiveness
- **GT**: 2002.08909: "search" is not used as a standalone technical term; the paper frames retrieval as a latent-variable inference problem, where the retriever selects documents z from corpus Z and the marginal probability p(y|x) requires summing over all documents, optimized via stochastic gradient descent. 2004.04906: "search" refers to efficient similarity/matching over a precomputed index of passage representations, e.g., "inner product search," where the similarity function must be decomposable so passage representations can be precomputed (contrasted with sparse TF-IDF/BM25 keyword matching). 2004.12832: "search" (passage search) refers to the end-to-end ranking task of scoring query–document pairs with a deep LM (ColBERT's late interaction), emphasizing efficiency of retrieval/ranking. Divergence: the papers use "search" at different levels — 2002.08909 treats it implicitly as latent-variable document selection within a probabilistic training objective, 2004.04906 treats it as decomposable vector similarity search over a precomputed index, and 2004.12832 treats it as the neural ranking/scoring task itself. These are related but distinct framings rather than a single shared definition.
- 来源: 2002.08909, 2004.04906, 2004.12832 | 备注: 

## tam-010 [term_ambiguity] intent=multi_hop verify=✓
- **Q**: Does the term "token" carry different meanings across these papers (2002.08909, 2004.04906, 2004.12832)?
- **证据1**: 2002.08909: subword/word-piece units produced by the tokenizer (e.g., BERT WordPiece); the atomic input elements of the MLM, some of which are masked and predicted
- **证据2**: 2004.04906: word/subword units into which questions and passages are tokenized before embedding; passages are split into fixed-length blocks measured in words/tokens
- **证据3**: 2004.12832: word/subword units of the query and document that are tokenized and embedded for neural ranking, over which n-gram matching signals are computed
- **GT**: No real divergence. In all three papers "token" refers to the same basic unit of text produced by tokenization: a subword/word piece (or word) that the model consumes as input. 2002.08909: tokens are the subword units produced by BERT's WordPiece tokenizer, the atomic input elements of the masked language model (a fraction of tokens are masked and predicted). 2004.04906: tokens are the word/subword units into which questions and passages are tokenized before embedding; passages are split into fixed-length blocks measured in words/tokens. 2004.12832: tokens are the word/subword units of the query and document that are tokenized and embedded for neural ranking (e.g., n-gram matching over tokens). The usage is essentially the same across papers, so no cross-paper meaning difference exists.
- 来源: 2002.08909, 2004.04906, 2004.12832 | 备注: 

## una-001 [unanswerable] intent=single_hop verify=n/a
- **Q**: How does a multimodal RAG system combine image and text retrieval for visual question answering on the OK-VQA benchmark?
- **GT**: 知识库中不包含回答该问题所需的内容。正确行为是明确说明未找到相关信息，不得编造。
- 来源: (无) | 备注: 

## una-002 [unanswerable] intent=single_hop verify=n/a
- **Q**: How does direct preference optimization compare to PPO-based RLHF for aligning retrieval-augmented language models with human preferences?
- **GT**: 知识库中不包含回答该问题所需的内容。正确行为是明确说明未找到相关信息，不得编造。
- 来源: (无) | 备注: 

## una-003 [unanswerable] intent=single_hop verify=n/a
- **Q**: How does mixture-of-experts routing interact with retrieval augmentation in trillion-parameter language models?
- **GT**: 知识库中不包含回答该问题所需的内容。正确行为是明确说明未找到相关信息，不得编造。
- 来源: (无) | 备注: 

## una-004 [unanswerable] intent=single_hop verify=n/a
- **Q**: How does speculative decoding affect the inference speed of retrieval-augmented generation systems?
- **GT**: 知识库中不包含回答该问题所需的内容。正确行为是明确说明未找到相关信息，不得编造。
- 来源: (无) | 备注: 

## una-005 [unanswerable] intent=single_hop verify=n/a
- **Q**: How does the HyDE approach compare with the query2doc method on the BEIR benchmark?
- **GT**: 知识库中不包含回答该问题所需的内容。正确行为是明确说明未找到相关信息，不得编造。
- 来源: (无) | 备注: 

## una-006 [unanswerable] intent=single_hop verify=n/a
- **Q**: How does the Llama 3 70B model perform on the Natural Questions dataset compared to PaLM 2?
- **GT**: 知识库中不包含回答该问题所需的内容。正确行为是明确说明未找到相关信息，不得编造。
- 来源: (无) | 备注: 

## una-007 [unanswerable] intent=single_hop verify=n/a
- **Q**: How does the RAGAS framework score faithfulness and answer relevance of retrieval-augmented generation outputs?
- **GT**: 知识库中不包含回答该问题所需的内容。正确行为是明确说明未找到相关信息，不得编造。
- 来源: (无) | 备注: 

## una-008 [unanswerable] intent=single_hop verify=n/a
- **Q**: What LoRA rank and alpha values give the best trade-off between accuracy and trainable parameters for retrieval-augmented generation models?
- **GT**: 知识库中不包含回答该问题所需的内容。正确行为是明确说明未找到相关信息，不得编造。
- 来源: (无) | 备注: 

## una-009 [unanswerable] intent=single_hop verify=n/a
- **Q**: What accuracy does GPT-4 achieve on the MMLU benchmark when augmented with a retrieval pipeline?
- **GT**: 知识库中不包含回答该问题所需的内容。正确行为是明确说明未找到相关信息，不得编造。
- 来源: (无) | 备注: 

## una-010 [unanswerable] intent=single_hop verify=n/a
- **Q**: What are the best practices for chunking long PDF documents before embedding them for a retrieval-augmented chatbot?
- **GT**: 知识库中不包含回答该问题所需的内容。正确行为是明确说明未找到相关信息，不得编造。
- 来源: (无) | 备注: 

## una-011 [unanswerable] intent=single_hop verify=n/a
- **Q**: What are the memory requirements for serving a 70B parameter retrieval-augmented model with vLLM on a single A100 GPU?
- **GT**: 知识库中不包含回答该问题所需的内容。正确行为是明确说明未找到相关信息，不得编造。
- 来源: (无) | 备注: 

## una-012 [unanswerable] intent=single_hop verify=n/a
- **Q**: What are the trade-offs between using a cross-encoder reranker and a late-interaction model for the MS MARCO passage ranking leaderboard?
- **GT**: 知识库中不包含回答该问题所需的内容。正确行为是明确说明未找到相关信息，不得编造。
- 来源: (无) | 备注: 

## una-013 [unanswerable] intent=single_hop verify=n/a
- **Q**: What is the best prompt template for chain-of-thought reasoning in retrieval-augmented question answering?
- **GT**: 知识库中不包含回答该问题所需的内容。正确行为是明确说明未找到相关信息，不得编造。
- 来源: (无) | 备注: 

## una-014 [unanswerable] intent=single_hop verify=n/a
- **Q**: What is the effect of rotary position embedding scaling on long-context retrieval-augmented language models?
- **GT**: 知识库中不包含回答该问题所需的内容。正确行为是明确说明未找到相关信息，不得编造。
- 来源: (无) | 备注: 

## una-015 [unanswerable] intent=single_hop verify=n/a
- **Q**: What is the throughput and latency of HNSW versus IVF-PQ indexes in FAISS when serving a billion-scale dense retrieval corpus?
- **GT**: 知识库中不包含回答该问题所需的内容。正确行为是明确说明未找到相关信息，不得编造。
- 来源: (无) | 备注: 

---
# 备选（未入选正式集，人工审核后可替换正式集中的 rejected 条目）
## 备选 [cross_paper_comparison] (verify=False)
- **Q**: How do CRAG and RAPTOR differ in the way they address the problem of retrieval quality for retrieval-augmented generation?
- **GT**: Both papers start from the premise that retrieval quality determines generation quality: CRAG notes that LLMs hallucinate because they cannot secure factual accuracy from parametric knowledge alone, and its Figure 1 shows a low-quality retriever feeding irrelevant documents that mislead the generator. However, their remedies operate at different stages of the pipeline. CRAG targets the retrieval output itself, adding a corrective mechanism that evaluates retrieved documents and filters or corrects them before generation, so that inaccurate documents do not reach the generator. RAPTOR instead restructures the retrieval corpus, recursively summarizing and abstracting documents into a tree organization so that retrieval can draw on multi-level, condensed representations rather than flat chunks. Thus CRAG is a corrective/verification layer over retrieval results, whereas RAPTOR is a corpus-organization and indexing approach.
- 来源: 2401.15884, 2401.18059

## 备选 [cross_paper_comparison] (verify=False)
- **Q**: How does the treatment of retrieval-augmented generation differ between Paper A's survey and Paper B's empirical study, particularly in terms of the scope of RAG variants covered and the evaluation approach used?
- **GT**: Paper A is a comprehensive review that maps the progression of RAG paradigms across Naive RAG, Advanced RAG, and Modular RAG, scrutinizing the tripartite foundation of retrieval, generation, and augmentation, and introducing an up-to-date evaluation framework and benchmark. Paper B, by contrast, is a focused empirical study at Infineon that evaluates one specific variant, RAG-Fusion, which combines RAG with reciprocal rank fusion (RRF) by generating multiple queries and reranking and fusing documents and scores. Whereas Paper A surveys the field broadly and proposes evaluation frameworks and benchmarks, Paper B conducts manual evaluation of answers on accuracy, relevance, and comprehensiveness. Paper B found that RAG-Fusion produced accurate and comprehensive answers because generated queries contextualized the original query from various perspectives, but answers strayed off topic when generated queries' relevance to the original query was insufficient. Thus, Paper A provides a panoramic taxonomy and evaluation scaffolding, while Paper B supplies a concrete, application-driven assessment of a single fusion-based RAG method.
- 来源: 2312.10997, 2402.03367

## 备选 [cross_paper_comparison] (verify=False)
- **Q**: How do REALM and RAG differ in the way they combine retrieval with language modeling, and what role does the retrieval component play in each?
- **GT**: REALM augments language model pre-training with a neural knowledge retriever that retrieves from a textual knowledge corpus such as all of Wikipedia, and crucially the language modeling objective's signal backpropagates all the way through the retriever, which must consider millions of documents. This creates a significant computational challenge that REALM explicitly addresses, making retrieval an integral, jointly-trained part of pre-training. RAG, by contrast, is presented as a retrieval-augmented generation approach for knowledge-intensive NLP tasks, pairing a retriever with a generator to produce answers. Thus while REALM focuses on integrating retrieval into pre-training via backpropagation through millions of documents, RAG emphasizes retrieval-augmented generation for downstream knowledge-intensive tasks.
- 来源: 2002.08909, 2005.11401

## 备选 [cross_paper_comparison] (verify=False)
- **Q**: How do Atlas and Self-RAG differ in the way they decide when and how to use retrieved information during generation?
- **GT**: Atlas is a pre-trained retrieval augmented language model that is carefully designed to learn knowledge-intensive tasks from very few examples, and it demonstrates that the content of the document index can easily be updated. Its retrieval is built into the model so that it can achieve strong few-shot performance, such as over 42% accuracy on Natural Questions with only 64 examples, beating a 540B-parameter model despite having 50x fewer parameters. Self-RAG, by contrast, is framed around learning to retrieve, generate, and critique through self-reflection, meaning the model itself decides when retrieval is needed and evaluates the retrieved content. Thus, while Atlas emphasizes a pre-trained retrieval-augmented architecture with an updatable index for few-shot knowledge tasks, Self-RAG emphasizes adaptive, self-reflective control over retrieval and generation.
- 来源: 2208.03299, 2310.11511

## 备选 [cross_paper_multi_hop] (verify=False)
- **Q**: Paper A (E5) claims to be the first model to beat BM25 on BEIR zero-shot without labeled data, and it is offered as a general-purpose single-vector embedding model. Paper B (RAG-Fusion) builds its retrieval pipeline on top of a RAG chatbot but never specifies which embedding/retriever it uses, and reports that some answers "strayed off topic when the generated queries' relevance to the original query is insufficient." Given A's conclusion that a single-vector embedding can serve as a general-purpose retriever that outperforms BM25 zero-shot, how should we interpret B's off-topic failure — is it a limitation of the underlying embedding/retrieval model (as A would frame it) or of the query-generation/fusion stage (as B frames it), and what does this imply about whether B's RAG-Fusion gains are attributable to better retrieval or to better query expansion?
- **GT**: A establishes that a single-vector embedding model (E5), trained with weakly-supervised contrastive pre-training, can act as a general-purpose retriever and is the first to beat BM25 on BEIR zero-shot without labeled data — meaning the retrieval backbone itself is not the bottleneck in a well-built pipeline. B reports that RAG-Fusion's failures occur when generated queries are insufficiently relevant to the original query, i.e., the failure is localized to the query-generation/fusion stage rather than to the retriever. Read together, B's off-topic answers cannot be blamed on a weak embedding/retrieval model of the kind A describes; instead they point to the multi-query expansion step injecting semantic drift. Consequently, B's reported accuracy/comprehensiveness gains are more plausibly attributable to query expansion and RRF fusion (better recall/coverage of the query space) than to any improvement in the underlying single-vector retrieval quality, which A already shows can be strong zero-shot. This also exposes a gap: B never specifies its embedding model, so its results cannot be cleanly separated from retrieval quality versus fusion quality — a confound that A's framing makes salient.
- 来源: 2212.03533, 2402.03367

## 备选 [term_ambiguity] (verify=True)
- **Q**: Do the papers 2002.08909, 2004.04906, and 2005.11401 use the term "answering" with different meanings?
- **GT**: No real divergence. In all three papers "answering" is used as part of the standard NLP task name "question answering" (QA), referring to the task of producing answers to questions. 2002.08909: "answering" appears in "question answering" as an example NLP task benefiting from world knowledge stored in language model pre-training. 2004.04906: "answering" appears in "open-domain question answering," the task of answering questions using retrieved passages. 2005.11401: "answering" appears in "question answering" as the task of generating answers from retrieved documents. The meanings are essentially the same; no cross-paper meaning difference exists.
- 来源: 2002.08909, 2004.04906, 2005.11401

## 备选 [term_ambiguity] (verify=True)
- **Q**: Does the term "processing" carry different meanings across papers 2002.08909, 2004.04906, and 2004.12832?
- **GT**: No real divergence. In all three papers "processing" is used in the ordinary, generic sense of a system handling/computing inputs, not as a distinct technical term. 2002.08909: used in the general sense of handling/incorporating knowledge or examples (e.g., language model pre-training and retrieval handling large-scale document collections). 2004.04906: used in the run-time efficiency sense of a system handling questions (e.g., "processing 995.0 questions per second"). 2004.12832: used in the sense of a system handling a query (e.g., "before processing a query"). The meanings are essentially the same generic usage; no cross-paper meaning difference exists.
- 来源: 2002.08909, 2004.04906, 2004.12832

## 备选 [term_ambiguity] (verify=True)
- **Q**: Does the term "retrieved" (as in "retrieved document/passage/context") carry different meanings across papers 2002.08909, 2004.04906, and 2004.12832?
- **GT**: No real divergence. In all three papers "retrieved" refers to documents/passages selected from a large corpus by a retrieval component (retriever) as candidate evidence for a downstream task. 2002.08909: documents z retrieved from a knowledge corpus Z by REALM's retriever, then fed to the knowledge-augmented encoder. 2004.04906: passages selected by a context retriever (e.g., DPR) from a large collection, then examined by a reader. 2004.12832: documents ranked/selected by ColBERT's late-interaction retrieval over a corpus. The term is used with essentially the same meaning (corpus items selected by a retrieval model), so no cross-paper meaning difference exists.
- 来源: 2002.08909, 2004.04906, 2004.12832

## 备选 [term_ambiguity] (verify=True)
- **Q**: Does the term "computational" carry different meanings across these papers?
- **GT**: No real divergence. In all three papers "computational" is used in the same general sense, referring to the compute/resources required by a model or method. 2002.08909: used in the context of language model pre-training and retrieval (e.g., "computational" as the compute cost of training/retrieval models). 2004.04906: used in the context of training retrievers/readers (compute involved in pipeline vs. joint training). 2004.12832: used explicitly to describe the cost of ranking models ("computational cost", "computationally expensive"). The meanings are essentially the same; no cross-paper meaning difference exists.
- 来源: 2002.08909, 2004.04906, 2004.12832

## 备选 [term_ambiguity] (verify=True)
- **Q**: Does the term "output" carry different meanings across these papers (2002.08909, 2004.04906, 2004.12832)?
- **GT**: No real divergence. In all three papers "output" is used in the ordinary sense of the result produced by a model/system. 2002.08909: the predicted answer string y (or predicted masked tokens) that the model produces from input x. 2004.04906: the retrieval results produced by DPR (e.g., ranked passages), discussed in terms of how they differ from other retrievers. 2004.12832: the result produced by the ranking/retrieval model. The meanings are essentially the same (model-produced result), so no cross-paper meaning difference exists.
- 来源: 2002.08909, 2004.04906, 2004.12832

## 备选 [term_ambiguity] (verify=True)
- **Q**: Does the term "across" carry different technical meanings in these papers?
- **GT**: No real divergence. In all three papers "across" is used in its ordinary English sense of "spanning/over" and is not a defined technical term. 2002.08909: used in ordinary prose (e.g., "across the input"). 2004.04906: used in ordinary prose (e.g., "across datasets"). 2004.12832: used in ordinary prose (e.g., "relationships across q and d"). The meanings are essentially the same; no cross-paper meaning difference exists.
- 来源: 2002.08909, 2004.04906, 2004.12832

## 备选 [term_ambiguity] (verify=True)
- **Q**: Does the term "generate" carry different meanings across these papers?
- **GT**: No real divergence. In all three papers "generate" refers to producing output tokens/text with a sequence-to-sequence (or language) model: 2002.08909 contrasts retrieval-based systems with generation-based systems that "apply a sequence-to-sequence model on x to directly generate y token-by-token"; 2005.11401 describes RAG models that "generate more specific, diverse and factual language" and endows "parametric-memory generation models" with non-parametric memory; 2004.12832 uses "generate" only in the generic sense of producing output (e.g., generic NLU computation), consistent with the same core meaning. The meanings are essentially the same, so no cross-paper meaning difference exists.
- 来源: 2002.08909, 2004.12832, 2005.11401

## 备选 [unanswerable] (verify=False)
- **Q**: What LoRA rank and alpha values give the best trade-off between accuracy and trainable parameters for retrieval-augmented generation models?
- **GT**: 知识库中不包含回答该问题所需的内容。正确行为是明确说明未找到相关信息，不得编造。
- 来源: (无)

## 备选 [unanswerable] (verify=False)
- **Q**: How does direct preference optimization compare to PPO-based RLHF for aligning retrieval-augmented language models with human preferences?
- **GT**: 知识库中不包含回答该问题所需的内容。正确行为是明确说明未找到相关信息，不得编造。
- 来源: (无)

## 备选 [unanswerable] (verify=False)
- **Q**: What is the throughput and recall trade-off of HNSW versus IVF-PQ indexes in a production vector database serving a RAG pipeline?
- **GT**: 知识库中不包含回答该问题所需的内容。正确行为是明确说明未找到相关信息，不得编造。
- 来源: (无)

## 备选 [unanswerable] (verify=False)
- **Q**: How does the MMLU-Pro leaderboard rank the top ten retrieval-augmented models as of 2025?
- **GT**: 知识库中不包含回答该问题所需的内容。正确行为是明确说明未找到相关信息，不得编造。
- 来源: (无)

## 备选 [unanswerable] (verify=False)
- **Q**: What multimodal retrieval architecture lets a RAG system answer questions about images and tables jointly with text passages?
- **GT**: 知识库中不包含回答该问题所需的内容。正确行为是明确说明未找到相关信息，不得编造。
- 来源: (无)

## 备选 [unanswerable] (verify=False)
- **Q**: How many tokens of context can Gemini 1.5 Pro process, and how does that compare with retrieval-augmented approaches?
- **GT**: 知识库中不包含回答该问题所需的内容。正确行为是明确说明未找到相关信息，不得编造。
- 来源: (无)

## 备选 [unanswerable] (verify=False)
- **Q**: What is the best chunking strategy and chunk overlap for PDF documents in a RAG pipeline?
- **GT**: 知识库中不包含回答该问题所需的内容。正确行为是明确说明未找到相关信息，不得编造。
- 来源: (无)

## 备选 [unanswerable] (verify=False)
- **Q**: How does the MTEB benchmark score compare across the embedding models used in these retrieval systems?
- **GT**: 知识库中不包含回答该问题所需的内容。正确行为是明确说明未找到相关信息，不得编造。
- 来源: (无)

## 备选 [unanswerable] (verify=False)
- **Q**: What are the latency and cost figures for serving a RAG system with vLLM versus TensorRT-LLM on A100 GPUs?
- **GT**: 知识库中不包含回答该问题所需的内容。正确行为是明确说明未找到相关信息，不得编造。
- 来源: (无)

## 备选 [unanswerable] (verify=False)
- **Q**: How does speculative decoding affect the end-to-end latency of retrieval-augmented generation?
- **GT**: 知识库中不包含回答该问题所需的内容。正确行为是明确说明未找到相关信息，不得编造。
- 来源: (无)

## 备选 [unanswerable] (verify=False)
- **Q**: What quantization scheme (GPTQ, AWQ, or bitsandbytes) preserves retrieval-augmented QA accuracy best at 4-bit precision?
- **GT**: 知识库中不包含回答该问题所需的内容。正确行为是明确说明未找到相关信息，不得编造。
- 来源: (无)

## 备选 [unanswerable] (verify=False)
- **Q**: How does the Llama 3 70B model perform on open-domain QA when combined with a dense retriever?
- **GT**: 知识库中不包含回答该问题所需的内容。正确行为是明确说明未找到相关信息，不得编造。
- 来源: (无)

## 备选 [unanswerable] (verify=False)
- **Q**: What is the best way to fine-tune a reranker with knowledge distillation from a larger cross-encoder?
- **GT**: 知识库中不包含回答该问题所需的内容。正确行为是明确说明未找到相关信息，不得编造。
- 来源: (无)

## 备选 [unanswerable] (verify=False)
- **Q**: How does mixture-of-experts routing interact with retrieval augmentation in trillion-parameter models?
- **GT**: 知识库中不包含回答该问题所需的内容。正确行为是明确说明未找到相关信息，不得编造。
- 来源: (无)

## 备选 [unanswerable] (verify=False)
- **Q**: What safety and jailbreak-resistance evaluations have been run on retrieval-augmented chatbots?
- **GT**: 知识库中不包含回答该问题所需的内容。正确行为是明确说明未找到相关信息，不得编造。
- 来源: (无)
