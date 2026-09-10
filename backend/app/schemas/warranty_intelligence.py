from datetime import datetime, timezone
from enum import Enum
from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field
from app.schemas.sources import SourceReference


class CoverageLikelihood(str, Enum):
    CONFIRMED = "confirmed_coverage"
    LIKELY = "likely_coverage"
    UNCLEAR = "unclear_coverage"
    EXCLUDED = "excluded_issue"


class WarrantyAnalysisRequest(BaseModel):
    productId: str = Field(..., description="Target product ID")
    issueDescription: str = Field(..., min_length=2, max_length=1000, description="Description of the symptom, defect, or damage")
    warrantyId: Optional[str] = Field(None, description="Optional specific warranty component ID to analyze against")


class WarrantyQuestionType(str, Enum):
    ISSUE_COVERAGE = "issue_coverage"
    IS_ACTIVE = "is_active"
    WHAT_COVERED = "what_covered"
    WHAT_EXCLUDED = "what_excluded"
    HOW_TO_CLAIM = "how_to_claim"
    REQUIRED_DOCUMENTS = "required_documents"


class WarrantyQuestionRequest(BaseModel):
    productId: str = Field(..., description="Target product ID")
    questionType: WarrantyQuestionType = Field(default=WarrantyQuestionType.ISSUE_COVERAGE)
    issueDescription: Optional[str] = Field(None, description="Problem description if questionType is issue_coverage")


class PipelineStep(BaseModel):
    stepName: str
    status: str
    details: str


class WarrantyIntelligenceResponse(BaseModel):
    productId: str
    productName: str
    issueDescription: Optional[str] = None
    questionType: WarrantyQuestionType = WarrantyQuestionType.ISSUE_COVERAGE
    coverageLikelihood: CoverageLikelihood
    statusLabel: str
    statusColor: str
    confidenceScore: float = Field(..., ge=0.0, le=1.0)
    isWarrantyActive: bool
    applicableWarranties: List[Dict[str, Any]] = Field(default_factory=list)
    matchingInclusions: List[str] = Field(default_factory=list)
    matchingExclusions: List[str] = Field(default_factory=list)
    conditions: List[str] = Field(default_factory=list)
    requiredDocuments: List[str] = Field(default_factory=list)
    documentsAvailableInVault: List[str] = Field(default_factory=list)
    missingDocuments: List[str] = Field(default_factory=list)
    claimSteps: List[str] = Field(default_factory=list)
    supportContact: Optional[str] = None
    sourceReferences: List[SourceReference] = Field(default_factory=list)
    explanation: str
    recommendedAction: str
    disclaimer: str = (
        "Disclaimer: This analysis is an informational assessment based on your recorded documents and manufacturer guidelines. "
        "Final coverage is determined by the manufacturer/service center upon physical inspection."
    )
    pipelineSteps: List[PipelineStep] = Field(default_factory=list)
    createdAt: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
