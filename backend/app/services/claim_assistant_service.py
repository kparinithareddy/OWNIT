import logging
from datetime import datetime, timezone
from typing import List, Dict, Any, Optional

from app.schemas.claim_assistant import (
    ClaimProvenanceType,
    ClaimFieldItem,
    ChecklistItem,
    ClaimPreparationRequest,
    ClaimPreparationResponse
)
from app.schemas.product import ProductResponse
from app.schemas.warranty import WarrantyResponse
from app.schemas.sources import SourceReference
from app.services.product_service import product_service
from app.services.warranty_service import warranty_service
from app.services.document_service import document_service
from app.services.retrieval_service import retrieval_service

logger = logging.getLogger("ownit.services.claim_assistant")


class ClaimAssistantService:
    """
    Synthesizes a structured, provenance-tagged warranty claim preparation dossier
    and generates an editable draft support message with mandatory user review.
    Does NOT submit claims or send emails automatically.
    """

    async def prepare_claim_dossier(
        self,
        user_id: str,
        request: ClaimPreparationRequest
    ) -> ClaimPreparationResponse:
        """
        Builds the complete warranty claim preparation dossier with distinct
        provenance indicators (document_verified, ai_generated, needs_confirmation).
        """
        # 1. Fetch Product
        product = await product_service.get_product_by_id(request.productId, user_id)

        # 2. Fetch Warranties
        warranties = await warranty_service.get_warranties_by_product(request.productId, user_id)

        # Identify selected or primary active warranty
        selected_warranty: Optional[WarrantyResponse] = None
        if request.warrantyId:
            for w in warranties:
                if w.id == request.warrantyId:
                    selected_warranty = w
                    break

        if not selected_warranty:
            # Pick first active or expiring soon warranty, else first warranty
            active_list = [w for w in warranties if w.status in ["Active", "Expiring Soon"]]
            selected_warranty = active_list[0] if active_list else (warranties[0] if warranties else None)

        # 3. Fetch Uploaded Documents
        documents = []
        try:
            doc_objs = await document_service.get_documents(user_id=user_id, product_id=request.productId)
            documents = [d.model_dump() for d in doc_objs]
        except Exception as e:
            logger.warning("Could not fetch documents for claim assistant: %s", e)


        # 4. Fetch Verified Sources
        sources = retrieval_service.retrieve_hierarchical_sources(
            product=product,
            warranties=warranties,
            documents=documents,
            maintenance_records=[],
            query=request.problemDescription
        )

        # -------------------------------------------------------------
        # Section 1: Product Information Fields with Provenance
        # -------------------------------------------------------------
        product_info_fields = [
            ClaimFieldItem(
                label="Product Name",
                value=f"{product.brand} {product.name}",
                provenance=ClaimProvenanceType.DOCUMENT_VERIFIED,
                notes="From recorded asset registry"
            ),
            ClaimFieldItem(
                label="Model Number",
                value=product.model or "Not specified",
                provenance=ClaimProvenanceType.DOCUMENT_VERIFIED,
                notes="From purchase records"
            ),
            ClaimFieldItem(
                label="Purchase Date",
                value=product.purchaseDate,
                provenance=ClaimProvenanceType.DOCUMENT_VERIFIED,
                notes="Recorded purchase date"
            ),
            ClaimFieldItem(
                label="Purchased From / Seller",
                value=product.seller or "Retail Seller",
                provenance=ClaimProvenanceType.DOCUMENT_VERIFIED,
                notes="Recorded vendor"
            ),
            ClaimFieldItem(
                label="Serial Number / IMEI",
                value=product.serialNumber or product.imei or "Pending Physical Verification",
                provenance=(
                    ClaimProvenanceType.DOCUMENT_VERIFIED if product.serialNumber or product.imei
                    else ClaimProvenanceType.NEEDS_CONFIRMATION
                ),
                notes="Must match physical barcode label on product or carton"
            )
        ]

        # -------------------------------------------------------------
        # Section 2: Problem Summary (AI-Generated Synthesis)
        # -------------------------------------------------------------
        clean_problem_desc = request.problemDescription.strip()
        problem_summary_text = (
            f"The asset is experiencing: {clean_problem_desc}. "
            f"Onset: {request.problemStartDate or 'Recently observed during normal operating conditions'}. "
            f"Prior troubleshooting: {request.incidentDetails or 'Basic power cycle performed without resolution'}."
        )

        problem_summary = ClaimFieldItem(
            label="Synthesized Defect Summary",
            value=problem_summary_text,
            provenance=ClaimProvenanceType.AI_GENERATED,
            notes="AI-synthesized from owner description. Fully editable."
        )

        # -------------------------------------------------------------
        # Section 3: Warranty Status Fields
        # -------------------------------------------------------------
        warranty_status_fields = []
        if selected_warranty:
            warranty_status_fields.extend([
                ClaimFieldItem(
                    label="Warranty Component",
                    value=f"{selected_warranty.type} ({selected_warranty.provider})",
                    provenance=ClaimProvenanceType.DOCUMENT_VERIFIED,
                    notes="Registered warranty component"
                ),
                ClaimFieldItem(
                    label="Current Status",
                    value=f"{selected_warranty.status} ({selected_warranty.daysRemaining} days remaining)",
                    provenance=ClaimProvenanceType.DOCUMENT_VERIFIED,
                    notes=f"Valid from {selected_warranty.startDate} to {selected_warranty.expiryDate}"
                ),
                ClaimFieldItem(
                    label="Policy Duration",
                    value=str(selected_warranty.duration or (f"{selected_warranty.durationMonths} Months" if getattr(selected_warranty, 'durationMonths', None) else "Standard Term")),
                    provenance=ClaimProvenanceType.DOCUMENT_VERIFIED,
                    notes="Coverage term"
                )
            ])
        else:
            warranty_status_fields.append(
                ClaimFieldItem(
                    label="Warranty Status",
                    value="No active warranty component registered in vault",
                    provenance=ClaimProvenanceType.NEEDS_CONFIRMATION,
                    notes="Please attach your warranty card or receipt to verify coverage"
                )
            )

        # -------------------------------------------------------------
        # Section 4: Coverage Information
        # -------------------------------------------------------------
        coverage_fields = []
        if selected_warranty and selected_warranty.benefits:
            benefits_text = (
                ", ".join(selected_warranty.benefits)
                if isinstance(selected_warranty.benefits, list)
                else str(selected_warranty.benefits)
            )
            coverage_fields.append(
                ClaimFieldItem(
                    label="Covered Inclusions & Parts",
                    value=benefits_text,
                    provenance=ClaimProvenanceType.DOCUMENT_VERIFIED,
                    notes="Directly extracted from warranty terms"
                )
            )
        else:
            coverage_fields.append(
                ClaimFieldItem(
                    label="Standard Inclusions",
                    value="Internal hardware manufacturing defects, logic board, and certified replacement parts.",
                    provenance=ClaimProvenanceType.AI_GENERATED,
                    notes="Standard industry limited warranty coverage"
                )
            )

        # -------------------------------------------------------------
        # Section 5: Relevant Exclusions to Be Aware Of
        # -------------------------------------------------------------
        relevant_exclusions = []
        if selected_warranty and selected_warranty.exclusions:
            exclusions_text = (
                ", ".join(selected_warranty.exclusions)
                if isinstance(selected_warranty.exclusions, list)
                else str(selected_warranty.exclusions)
            )
            relevant_exclusions.append(
                ClaimFieldItem(
                    label="Documented Policy Exclusions",
                    value=exclusions_text,
                    provenance=ClaimProvenanceType.DOCUMENT_VERIFIED,
                    notes="Exclusions specified in warranty certificate"
                )
            )
        else:
            relevant_exclusions.append(
                ClaimFieldItem(
                    label="Standard Warranty Exclusions",
                    value="Physical drops, liquid/water ingress, unauthorized modification, and cosmetic scratches.",
                    provenance=ClaimProvenanceType.AI_GENERATED,
                    notes="Ensure your device does not exhibit external impact or moisture damage."
                )
            )

        relevant_exclusions.append(
            ClaimFieldItem(
                label="Physical & Liquid Condition Confirmation",
                value="User must confirm no liquid exposure or physical impact prior to submission.",
                provenance=ClaimProvenanceType.NEEDS_CONFIRMATION,
                notes="Service centers perform chemical/physical inspections upon intake"
            )
        )

        # -------------------------------------------------------------
        # Section 6: Required Documents Check
        # -------------------------------------------------------------
        doc_types = [d.get("documentType", "Document") for d in documents]
        required_documents_list = [
            {
                "name": "Original Tax Invoice / Bill",
                "inVault": any("Invoice" in t or "Bill" in t or "Receipt" in t for t in doc_types),
                "provenance": ClaimProvenanceType.DOCUMENT_VERIFIED if any("Invoice" in t or "Bill" in t or "Receipt" in t for t in doc_types) else ClaimProvenanceType.NEEDS_CONFIRMATION,
                "notes": "Proof of purchase date and authorized dealer origin"
            },
            {
                "name": "Warranty Card / Certificate",
                "inVault": any("Warranty" in t for t in doc_types) or selected_warranty is not None,
                "provenance": ClaimProvenanceType.DOCUMENT_VERIFIED if (any("Warranty" in t for t in doc_types) or selected_warranty is not None) else ClaimProvenanceType.NEEDS_CONFIRMATION,
                "notes": "Manufacturer registration or stamped card"
            },
            {
                "name": "Clear Photo of Serial Number / IMEI Label",
                "inVault": bool(product.serialNumber or product.imei),
                "provenance": ClaimProvenanceType.NEEDS_CONFIRMATION,
                "notes": "Photo of barcode sticker on device underside or carton"
            },
            {
                "name": "Valid Government Photo ID",
                "inVault": False,
                "provenance": ClaimProvenanceType.NEEDS_CONFIRMATION,
                "notes": "Matching the name on the purchase invoice"
            }
        ]

        # -------------------------------------------------------------
        # Section 7: Claim Procedure & Service Contacts
        # -------------------------------------------------------------
        claim_procedure = selected_warranty.claimProcedure if selected_warranty and selected_warranty.claimProcedure else None
        support_info = selected_warranty.serviceInformation if selected_warranty and selected_warranty.serviceInformation else None

        claim_steps = [
            f"1. Keep your original invoice (Date: {product.purchaseDate}) and serial number ({product.serialNumber or 'on product label'}) ready.",
            f"2. Contact {product.brand} authorized customer care at {support_info or 'the official toll-free helpline'} or book online.",
            f"3. Quote Product Model: '{product.model}' and provide the detailed symptom description below.",
            "4. Book an authorized on-site engineer visit or note the nearest authorized walk-in service center.",
            "5. Collect and keep your Service Job Sheet / RMA tracking number upon handover."
        ]

        # Determine official support contact info
        oem_ref = None
        for s in sources:
            if s.sourceType == "official_manufacturer":
                oem_ref = s
                break

        service_contact = {
            "brand": product.brand,
            "helpline": support_info or "Check official manufacturer portal",
            "portalUrl": oem_ref.url if oem_ref else None,
            "domain": oem_ref.domain if oem_ref else None
        }

        # -------------------------------------------------------------
        # Section 8: Recommended Next Step
        # -------------------------------------------------------------
        recommended_next_step = (
            f"Review the draft support message below, verify that all checklist items are confirmed, "
            f"and copy the text to send via {product.brand}'s official support email or online ticket portal."
        )

        # -------------------------------------------------------------
        # Section 9: Editable Draft Support Message (AI-Generated)
        # -------------------------------------------------------------
        serial_display = product.serialNumber or product.imei or "[Insert Serial Number / IMEI here]"
        warranty_title = f"{selected_warranty.type} ({selected_warranty.provider})" if selected_warranty else "Standard Manufacturer Warranty"
        expiry_display = f"Valid until {selected_warranty.expiryDate}" if selected_warranty else "Purchased on " + product.purchaseDate

        draft_message = (
            f"Subject: Warranty Service Request – {product.brand} {product.model or product.name} (Serial: {serial_display})\n\n"
            f"Dear {product.brand} Customer Support Team,\n\n"
            f"I am writing to request warranty service and inspection for my {product.brand} {product.name}, "
            f"purchased on {product.purchaseDate} from {product.seller or 'an authorized retailer'}.\n\n"
            f"--- Product & Warranty Details ---\n"
            f"• Product: {product.brand} {product.name}\n"
            f"• Model Number: {product.model or 'N/A'}\n"
            f"• Serial Number / IMEI: {serial_display}\n"
            f"• Registered Warranty: {warranty_title} ({expiry_display})\n\n"
            f"--- Issue Description ---\n"
            f"• Defect Observed: {clean_problem_desc}\n"
            f"• First Occurred: {request.problemStartDate or 'Recently observed during regular normal usage'}\n"
            f"• Troubleshooting Attempted: {request.incidentDetails or 'Device restarted; defect persists'}\n"
            f"• Physical Condition: Normal operating condition with no external impact or liquid exposure.\n\n"
            f"--- Documentation Ready ---\n"
            f"• Original Tax Invoice: Available upon request / attached\n"
            f"• Serial Number Photo: Available upon request\n\n"
            f"Could you please advise on scheduling an authorized technician inspection or provide the details "
            f"of the nearest authorized service center to diagnose and repair this unit under warranty?\n\n"
            f"Thank you for your assistance.\n\n"
            f"Sincerely,\n"
            f"[Your Name]\n"
            f"[Your Contact Phone Number]\n"
            f"[Your Email Address]"
        )

        # -------------------------------------------------------------
        # Section 10: Mandatory Confirmation Checklist (Review Step)
        # -------------------------------------------------------------
        confirmation_checklist = [
            ChecklistItem(
                id="chk-serial",
                label="Physical Serial Number Match",
                description=f"I have verified that the serial number on my physical device ({serial_display}) matches this claim.",
                confirmed=bool(product.serialNumber)
            ),
            ChecklistItem(
                id="chk-condition",
                label="No Physical or Liquid Damage",
                description="I confirm this malfunction occurred under normal usage without liquid spills, accidental drops, or unauthorized opening.",
                confirmed=False
            ),
            ChecklistItem(
                id="chk-invoice",
                label="Purchase Invoice Accessibility",
                description=f"I have the original tax invoice from {product.seller or 'seller'} dated {product.purchaseDate} ready to present.",
                confirmed=any("Invoice" in t or "Bill" in t for t in doc_types)
            ),
            ChecklistItem(
                id="chk-review",
                label="Draft Message Reviewed",
                description="I have reviewed and customized the generated draft message to accurately describe my specific situation.",
                confirmed=False
            )
        ]

        return ClaimPreparationResponse(
            productId=product.id,
            productName=product.name,
            brand=product.brand,
            model=product.model or "",
            productInfoFields=product_info_fields,
            problemSummary=problem_summary,
            selectedWarranty=selected_warranty.model_dump() if selected_warranty else None,
            warrantyStatusFields=warranty_status_fields,
            coverageFields=coverage_fields,
            relevantExclusions=relevant_exclusions,
            requiredDocuments=required_documents_list,
            claimProcedureSteps=claim_steps,
            serviceContact=service_contact,
            recommendedNextStep=recommended_next_step,
            draftSupportMessage=draft_message,
            confirmationChecklist=confirmation_checklist,
            sourceReferences=sources
        )


claim_assistant_service = ClaimAssistantService()
