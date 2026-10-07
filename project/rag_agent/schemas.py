from typing import List, Literal
from pydantic import BaseModel, Field

class QueryAnalysis(BaseModel):
    is_clear: bool = Field(
        description="Indicates if the user's question is clear and answerable."
    )
    questions: List[str] = Field(
        description="List of rewritten, self-contained questions."
    )
    clarification_needed: str = Field(
        description="Explanation if the question is unclear."
    )

class IntentClassification(BaseModel):
    intent: Literal["simple_faq", "single_hop", "multi_hop"] = Field(
        description=(
            "Classified intent of the user's latest message: simple_faq is a "
            "one-place factual lookup; single_hop is one focused precise "
            "retrieval; multi_hop needs information combined from multiple places."
        )
    )


class CritiqueVerdict(BaseModel):
    """IsSup 判定的结构化输出：列出答案中未被证据支撑的事实性声明。"""
    is_sup: bool = Field(
        description="True if every factual claim in the answer is supported by the evidence."
    )
    unsupported_claims: list[str] = Field(
        description="The claims that are NOT supported by the evidence (empty if all supported)."
    )
    reason: str = Field(
        description="Short explanation of the verdict."
    )
