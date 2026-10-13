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