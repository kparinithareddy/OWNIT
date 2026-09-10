from pydantic import BaseModel, Field
from typing import List, Optional, Literal, Dict, Any


class RecallMatch(BaseModel):
    recallId: str = Field(..., description="Unique bulletin/recall identification code")
    title: str = Field(..., description="Official title of the recall or safety campaign")
    severity: Literal["CRITICAL", "WARNING", "INFO"] = Field(
        ...,
        description="Severity level of the safety issue"
    )
    affectedBrand: str = Field(..., description="Manufacturer brand name")
    affectedModel: str = Field(..., description="Affected product model identifier or series")
    affectedSerialRange: Optional[str] = Field(None, description="Affected serial number prefix, pattern, or batch window")
    isSerialMatched: Optional[bool] = Field(
        None,
        description="True if user's serial number explicitly matches affected batch; False if serial ruled out; None if unverified"
    )
    hazard: str = Field(..., description="Description of the safety hazard (e.g., battery overheating, electrical fire risk)")
    officialSource: str = Field(..., description="Name of the official safety authority or OEM portal")
    sourceUrl: str = Field(..., description="Direct authentic URL to the official recall program/bulletin")
    sourceDomain: str = Field(..., description="Domain of the official source (e.g., support.apple.com, cpsc.gov)")
    recommendedAction: str = Field(..., description="Step-by-step guidance for the product owner")
    publishDate: Optional[str] = Field(None, description="Date the safety bulletin was published (YYYY-MM-DD)")


class ProductRecallCheckResponse(BaseModel):
    productId: str = Field(..., description="Target product ID")
    productName: str = Field(..., description="Target product name")
    brand: str = Field(..., description="Target product brand")
    model: str = Field(..., description="Target product model")
    serialNumber: Optional[str] = Field(None, description="Target product serial number if recorded")
    hasPossibleRecall: bool = Field(..., description="Whether a potential recall match was identified")
    warningMessage: Optional[str] = Field(
        None,
        description="Standardized cautious warning message: 'Possible recall match — verify with the official source.'"
    )
    matches: List[RecallMatch] = Field(
        default_factory=list,
        description="List of matching safety bulletins or recall notices"
    )
    checkedAt: str = Field(..., description="Timestamp of the safety check (UTC ISO string)")
    disclaimer: str = Field(
        default="Possible recall match — verify with the official source. OWNIT does not initiate automatic external returns or claims.",
        description="Standard disclaimer regarding official verification"
    )


class VaultRecallSummaryResponse(BaseModel):
    totalScanned: int = Field(..., description="Total products evaluated in user vault")
    alertsCount: int = Field(..., description="Total products with possible recall alerts")
    alerts: List[ProductRecallCheckResponse] = Field(
        default_factory=list,
        description="List of products with active safety warnings"
    )
