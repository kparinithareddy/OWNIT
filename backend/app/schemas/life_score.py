from pydantic import BaseModel, Field
from typing import List, Optional, Literal
from datetime import datetime


ScoreGradeType = Literal["Excellent", "Good", "Fair", "Needs Attention"]
FactorStatusType = Literal["positive", "warning", "negative"]


class LifeScoreFactor(BaseModel):
    name: str = Field(..., description="Factor name (e.g. Warranty Coverage, Document Completeness)")
    score: int = Field(..., ge=0, description="Points earned for this factor")
    maxScore: int = Field(..., ge=1, description="Maximum possible points for this factor")
    status: FactorStatusType = Field(..., description="Status tier: positive, warning, negative")
    description: str = Field(..., description="Short explanation of how this factor was evaluated")
    details: Optional[str] = Field(default=None, description="Additional itemized context")


class LifeScoreResponse(BaseModel):
    productId: str = Field(..., description="Unique product ID")
    score: int = Field(..., ge=0, le=100, description="Calculated score between 0 and 100")
    grade: ScoreGradeType = Field(..., description="Score classification: Excellent, Good, Fair, Needs Attention")
    color: str = Field(..., description="Semantic color: green, amber, red")
    summary: str = Field(..., description="High-level health and completeness summary")
    disclaimer: str = Field(
        default="This rule-based score evaluates ownership completeness and maintenance health. It is not a scientifically predictive model of hardware failure.",
        description="Mandatory disclaimer clarifying the nature of the score"
    )
    factors: List[LifeScoreFactor] = Field(default_factory=list, description="Breakdown of individual scoring factors")
    positiveReasons: List[str] = Field(default_factory=list, description="Bullet points explaining why points were awarded")
    improvementTips: List[str] = Field(default_factory=list, description="Actionable recommendations to improve asset health & completeness")
    calculatedAt: datetime = Field(default_factory=datetime.utcnow, description="Calculation timestamp")

    model_config = {
        "json_schema_extra": {
            "example": {
                "productId": "673abc1234567890efabcdef",
                "score": 82,
                "grade": "Good",
                "color": "green",
                "summary": "Asset has active warranty protection and verified documents, but could benefit from a service record.",
                "disclaimer": "This rule-based score evaluates ownership completeness and maintenance health. It is not a scientifically predictive model of hardware failure.",
                "factors": [
                    {
                        "name": "Warranty Coverage",
                        "score": 25,
                        "maxScore": 30,
                        "status": "positive",
                        "description": "Comprehensive warranty active (320 days remaining)."
                    },
                    {
                        "name": "Document Completeness",
                        "score": 20,
                        "maxScore": 20,
                        "status": "positive",
                        "description": "Purchase Bill and Warranty Card attached."
                    },
                    {
                        "name": "Device Age",
                        "score": 15,
                        "maxScore": 15,
                        "status": "positive",
                        "description": "Product is under 1 year old."
                    },
                    {
                        "name": "Maintenance & Care",
                        "score": 10,
                        "maxScore": 20,
                        "status": "warning",
                        "description": "No recent maintenance or routine service logged."
                    },
                    {
                        "name": "Asset Records & Identifiers",
                        "score": 12,
                        "maxScore": 15,
                        "status": "positive",
                        "description": "Serial number recorded and return window verified."
                    }
                ],
                "positiveReasons": [
                    "Active warranty coverage in good standing",
                    "Purchase Bill and documentation attached",
                    "Valid hardware serial number recorded",
                    "Asset is relatively new (< 1 year)"
                ],
                "improvementTips": [
                    "Log routine maintenance or cleaning to ensure longevity",
                    "Attach User Manual or Service Invoice for 100% complete records"
                ],
                "calculatedAt": "2026-09-10T17:55:00Z"
            }
        }
    }
