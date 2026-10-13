from pydantic import BaseModel, Field


class ResearchReport(BaseModel):
    executive_summary: str = Field(
        description="A concise summary of the research."
    )

    key_findings: list[str] = Field(
        description="Important findings supported by the research evidence."
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

