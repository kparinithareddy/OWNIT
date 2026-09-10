from datetime import datetime, timezone
from typing import Optional
from pydantic import BaseModel, Field


class ServiceRecordBase(BaseModel):
    productId: str = Field(..., description="ID of the associated product")
    serviceDate: str = Field(..., description="Date of service (YYYY-MM-DD)")
    problem: str = Field(..., min_length=1, max_length=500, description="Description of the symptom or defect")
    serviceCenter: str = Field(..., min_length=1, max_length=150, description="Authorized service center or technician name")
    workPerformed: str = Field(..., min_length=1, max_length=1000, description="Details of repairs, part replacement, or inspection performed")
    cost: Optional[float] = Field(default=0.0, ge=0.0, description="Cost of repair/service in ₹ (0 if fully covered)")
    warrantyCovered: bool = Field(default=False, description="Flag indicating if repair was covered by warranty")
    notes: Optional[str] = Field(default=None, max_length=1000, description="Technician notes, Job Sheet ID, or RMA number")
    documentId: Optional[str] = Field(default=None, description="Optional attached invoice/service bill document ID")


class ServiceRecordCreate(ServiceRecordBase):
    pass


class ServiceRecordUpdate(BaseModel):
    serviceDate: Optional[str] = None
    problem: Optional[str] = Field(default=None, min_length=1, max_length=500)
    serviceCenter: Optional[str] = Field(default=None, min_length=1, max_length=150)
    workPerformed: Optional[str] = Field(default=None, min_length=1, max_length=1000)
    cost: Optional[float] = Field(default=None, ge=0.0)
    warrantyCovered: Optional[bool] = None
    notes: Optional[str] = Field(default=None, max_length=1000)
    documentId: Optional[str] = None


class ServiceRecordResponse(BaseModel):
    id: str
    productId: str
    userId: str
    serviceDate: str
    problem: str
    serviceCenter: str
    workPerformed: str
    cost: float = 0.0
    warrantyCovered: bool = False
    notes: Optional[str] = None
    documentId: Optional[str] = None
    documentName: Optional[str] = None
    productName: Optional[str] = None
    productBrand: Optional[str] = None
    createdAt: datetime
    updatedAt: datetime
