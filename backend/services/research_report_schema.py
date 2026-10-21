from typing import Literal
from pydantic import BaseModel, Field


class FindingCitation(BaseModel):
    source_type: Literal["web", "document"] = Field(
        description="Whether the supporting evidence is from a web source or uploaded document."
    )

    url: str | None = Field(
        default=None,
        description="URL of the supporting web source. Null for document evidence."
    )

    filename: str | None = Field(
        default=None,
        description="Original filename of the supporting uploaded document."
    )

    chunk_index: int | None = Field(
        default=None,
        description="Index of the supporting document chunk."
    )


class CitedFinding(BaseModel):
    finding: str = Field(
        description="A factual research finding supported by supplied evidence."
    )

    citations: list[FindingCitation] = Field(
        default_factory=list,
        description="Evidence references supporting this finding."
    )

class ResearchReport(BaseModel):
    executive_summary: str = Field(
        description="A concise summary of the research."
    )

    key_findings: list[CitedFinding] = Field(
        description="Important research findings, each with citations to supporting evidence."
    )

    sources: list[str] = Field(
        description="Source URLs used to support the findings."
    )

    limitations: list[str] = Field(
        description="Evidence gaps, uncertainties, or research limitations."
    )


class ResearchAnalysis(BaseModel):
    main_insights: list[str] = Field(
        description="Key insights derived from the collected research evidence."
    )

    cross_source_agreements: list[str] = Field(
        description="Conclusions supported by multiple independent sources."
    )

    contradictions: list[str] = Field(
        description="Conflicting claims or inconsistencies found across sources."
    )

    evidence_gaps: list[str] = Field(
        description="Important questions that remain unanswered by the evidence."
    )





