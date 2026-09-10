from datetime import datetime, timezone
from enum import Enum
from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field
from app.schemas.sources import SourceReference


class ClaimProvenanceType(str, Enum):
    DOCUMENT_VERIFIED = "document_verified"  # Extracted from invoice / database records
    AI_GENERATED = "ai_generated"            # Synthesized summary / recommended phrasing
    NEEDS_CONFIRMATION = "needs_confirmation" # User must verify/confirm before submission


class ClaimFieldItem(BaseModel):
    label: str
    value: str
    provenance: ClaimProvenanceType
    notes: Optional[str] = None


class ChecklistItem(BaseModel):
    id: str
    label: str
    description: str
    confirmed: bool = False


class ClaimPreparationRequest(BaseModel):
    productId: str = Field(..., description="Target product ID")
    warrantyId: Optional[str] = Field(None, description="Specific warranty component ID if chosen")
    problemDescription: str = Field(..., min_length=3, max_length=1000, description="User description of the malfunction or defect")
    problemStartDate: Optional[str] = Field(None, description="Approximate date when problem first occurred")
    incidentDetails: Optional[str] = Field(None, description="Any troubleshooting steps already attempted")


class ClaimPreparationResponse(BaseModel):
    productId: str
    productName: str
    brand: str
    model: str
    productInfoFields: List[ClaimFieldItem] = Field(default_factory=list)
    problemSummary: ClaimFieldItem
    selectedWarranty: Optional[Dict[str, Any]] = None
    warrantyStatusFields: List[ClaimFieldItem] = Field(default_factory=list)
    coverageFields: List[ClaimFieldItem] = Field(default_factory=list)
    relevantExclusions: List[ClaimFieldItem] = Field(default_factory=list)
    requiredDocuments: List[Dict[str, Any]] = Field(default_factory=list)
    claimProcedureSteps: List[str] = Field(default_factory=list)
    serviceContact: Dict[str, Any] = Field(default_factory=dict)
    recommendedNextStep: str
    draftSupportMessage: str
    confirmationChecklist: List[ChecklistItem] = Field(default_factory=list)
    sourceReferences: List[SourceReference] = Field(default_factory=list)
    disclaimer: str = (
        "Important: OWNIT prepares this claim dossier for your convenience and does NOT submit claims or contact manufacturers automatically. "
        "Please review all information, edit your draft message as needed, and submit through the manufacturer's official authorized support channels."
    )
    createdAt: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
