from pydantic import BaseModel, Field
from typing import List, Optional, Literal


SourceTier = Literal[
    "user_document",           # Priority 1: User uploaded invoice, warranty card, manual
    "official_manufacturer",  # Priority 2: Verified official OEM policy & support portal
    "reliable_external",      # Priority 3: Verified seller / regulator policy (e.g. Amazon, Croma)
    "general_knowledge"       # Priority 4: General industry preventive guideline
]


class SourceReference(BaseModel):
    title: str = Field(..., description="Display title for the cited source")
    sourceType: SourceTier = Field(..., description="Source priority hierarchy tier")
    domain: Optional[str] = Field(None, description="Verified domain name (e.g. samsung.com, apple.com)")
    url: Optional[str] = Field(None, description="Verified real destination URL (no fabricated links)")
    details: Optional[str] = Field(None, description="Additional context or document filename")
    verified: bool = Field(default=True, description="Whether the source is verified authentic")
