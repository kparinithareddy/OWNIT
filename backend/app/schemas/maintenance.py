from datetime import datetime
from typing import Optional, List, Literal
from pydantic import BaseModel, Field

MaintenanceType = Literal[
    "Cleaning",
    "Filter Replacement",
    "Inspection",
    "Routine Servicing",
    "Battery Service",
    "Calibration",
    "Lubrication",
    "Software Update",
    "Repair",
    "Other"
]

MAINTENANCE_TYPES = [
    "Cleaning",
    "Filter Replacement",
    "Inspection",
    "Routine Servicing",
    "Battery Service",
    "Calibration",
    "Lubrication",
    "Software Update",
    "Repair",
    "Other"
]

MaintenanceStatus = Literal[
    "Scheduled",
    "In Progress",
    "Completed",
    "Overdue"
]


class MaintenanceBase(BaseModel):
    productId: str = Field(..., description="ID of the associated product")
    title: str = Field(..., min_length=1, max_length=120, description="Title of maintenance action")
    description: str = Field(default="", max_length=1000, description="Detailed description of service performed or needed")
    date: str = Field(..., description="Date of maintenance event (YYYY-MM-DD)")
    type: str = Field(default="Routine Servicing", description="Type of maintenance")
    status: str = Field(default="Completed", description="Status (Completed, Scheduled, In Progress, Overdue)")
    notes: Optional[str] = Field(default=None, max_length=1000, description="Additional technician notes or observations")
    cost: Optional[float] = Field(default=None, ge=0, description="Cost of service/parts in ₹")
    serviceProvider: Optional[str] = Field(default=None, max_length=120, description="Service center, vendor, or technician name")
    documentId: Optional[str] = Field(default=None, description="Optional attached invoice/service bill document ID")
    nextDueDate: Optional[str] = Field(default=None, description="Optional upcoming target date for next servicing (YYYY-MM-DD)")


class MaintenanceCreate(MaintenanceBase):
    pass


class MaintenanceUpdate(BaseModel):
    title: Optional[str] = Field(default=None, min_length=1, max_length=120)
    description: Optional[str] = Field(default=None, max_length=1000)
    date: Optional[str] = None
    type: Optional[str] = None
    status: Optional[str] = None
    notes: Optional[str] = Field(default=None, max_length=1000)
    cost: Optional[float] = Field(default=None, ge=0)
    serviceProvider: Optional[str] = Field(default=None, max_length=120)
    documentId: Optional[str] = None
    nextDueDate: Optional[str] = None


class MaintenanceResponse(BaseModel):
    id: str
    productId: str
    userId: str
    title: str
    description: str
    date: str
    type: str
    status: str
    notes: Optional[str] = None
    cost: Optional[float] = None
    serviceProvider: Optional[str] = None
    documentId: Optional[str] = None
    nextDueDate: Optional[str] = None
    documentName: Optional[str] = None
    createdAt: datetime
    updatedAt: datetime


class MaintenanceRecommendation(BaseModel):
    id: str
    category: str
    title: str
    description: str
    suggestedIntervalMonths: int
    source: str = Field(..., description="Source of the recommendation (e.g. 'General Preventive Care Guidelines', 'OEM Manual')")
    isManufacturerApproved: bool = Field(default=False, description="Strict boolean indicating if recommendation is verified manufacturer advice")
    disclaimer: str = Field(
        default="General preventive guideline. This recommendation is not verified or endorsed by the specific manufacturer unless cited.",
        description="Mandatory disclaimer ensuring transparency"
    )
