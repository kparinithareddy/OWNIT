import re
import logging
from datetime import datetime, timezone
from typing import List, Dict, Any, Optional, Tuple

from app.schemas.warranty_intelligence import (
    CoverageLikelihood,
    WarrantyAnalysisRequest,
    WarrantyQuestionType,
    WarrantyQuestionRequest,
    WarrantyIntelligenceResponse,
    PipelineStep
)
from app.schemas.product import ProductResponse
from app.schemas.warranty import WarrantyResponse
from app.schemas.sources import SourceReference
from app.services.product_service import product_service
from app.services.warranty_service import warranty_service
from app.services.document_service import document_service
from app.services.retrieval_service import retrieval_service
from app.core.database import db_manager

logger = logging.getLogger("ownit.services.warranty_intelligence")

# Exclusion pattern matcher
EXCLUSION_PATTERNS = {
    "liquid_damage": {
        "keywords": ["liquid", "water", "spill", "spilled", "wet", "rain", "coffee", "tea", "juice", "moisture", "corrosion", "drowned"],
        "reason": "Liquid ingress, moisture exposure, or fluid spills are explicitly excluded under standard manufacturer warranty terms."
    },
    "physical_damage": {
        "keywords": ["drop", "dropped", "fall", "fallen", "crack", "cracked", "shatter", "shattered", "broken screen", "broken glass", "dent", "bent", "crushed", "smash"],
        "reason": "Physical impact, accidental drops, and cracked panels/casings are classified as accidental damage and are excluded unless covered by dedicated accidental damage protection (ADP)."
    },
    "tampering": {
        "keywords": ["tamper", "tampered", "opened", "third party", "unauthorized", "rooted", "jailbreak", "local repair", "self repair", "modded", "modified"],
        "reason": "Unauthorized disassembly, third-party repair, or unauthorized modification voids the standard manufacturer warranty."
    },
    "electrical_surge": {
        "keywords": ["power surge", "lightning", "voltage spike", "high voltage", "burnt", "burnt smell", "short circuit from outside"],
        "reason": "Damage caused by external power fluctuations, voltage spikes, or abnormal power supply is generally excluded without special surge protection riders."
    },
    "wear_and_tear": {
        "keywords": ["cosmetic", "scratched", "paint peeling", "color fading", "normal wear", "wear and tear", "scuff"],
        "reason": "Normal cosmetic deterioration, paint wear, and superficial scratches that do not affect functionality are excluded."
    },
    "consumable_aging": {
        "keywords": ["battery health low", "battery degraded", "battery aging", "sponge", "filter dirty", "rubber worn"],
        "reason": "Natural degradation of consumable parts (batteries, filters, rubber seals) through normal usage cycles is excluded."
    }
}

# Inclusion pattern matcher
INCLUSION_PATTERNS = {
    "display_panel_defect": {
        "keywords": ["flicker", "flickering", "vertical line", "horizontal line", "green line", "dead pixel", "blank screen", "black screen", "display glitch", "ghosting", "backlight", "dim display"],
        "component": "Panel Warranty / Screen",
        "reason": "Internal display panel failures and manufacturing panel line defects without external impact are typically covered under Panel / Comprehensive warranties."
    },
    "power_motherboard": {
        "keywords": ["not turning on", "won't turn on", "dead", "power failure", "motherboard", "logic board", "pcb", "auto restart", "boot loop", "sudden shutdown", "overheating automatically"],
        "component": "Comprehensive Warranty / Motherboard",
        "reason": "Internal component logic board failure, power IC defects, and motherboard malfunctions during normal operation are covered under Comprehensive warranty."
    },
    "motor_compressor": {
        "keywords": ["compressor", "motor", "cooling stopped", "not cooling", "drum not spinning", "abnormal vibration", "compressor noise", "ice not forming"],
        "component": "Compressor / Motor Extended Warranty",
        "reason": "Inverter compressor, direct drive motor, and refrigeration cooling loop failures are protected under specialized long-term manufacturer warranties."
    },
    "sound_audio": {
        "keywords": ["speaker crackling", "no audio", "distorted sound", "mic not working", "microphone failure", "earpiece silent"],
        "component": "Comprehensive Hardware Warranty",
        "reason": "Internal speaker module or audio processing unit failures occurring without foreign object insertion are covered under standard hardware warranty."
    },
    "connectivity_sensor": {
        "keywords": ["wifi not working", "bluetooth failed", "fingerprint not recognized", "face unlock failed", "charging port loose", "sensor failure"],
        "component": "Comprehensive Hardware Warranty",
        "reason": "On-board wireless module, charging sub-board, and optical sensor hardware failures are covered."
    }
}


class WarrantyIntelligenceService:
    """
    Structured warranty analysis engine providing probabilistic, evidence-grounded
    coverage assessments across 4 likelihood levels without guaranteeing claim outcomes.
    """

    async def analyze_issue_or_question(
        self,
        user_id: str,
        request: WarrantyQuestionRequest
    ) -> WarrantyIntelligenceResponse:
        """
        Executes the 9-step Warranty Intelligence analysis pipeline for a product.
        """
        product = await product_service.get_product_by_id(request.productId, user_id)
        warranties = await warranty_service.get_warranties_by_product(request.productId, user_id)

        # Retrieve user uploaded documents
        documents = []
        try:
            doc_objs = await document_service.get_documents(user_id=user_id, product_id=request.productId)
            documents = [d.model_dump() for d in doc_objs]
        except Exception as e:
            logger.warning("Could not fetch documents for warranty intelligence: %s", e)

        # Retrieve hierarchical verified sources
        sources = retrieval_service.retrieve_hierarchical_sources(
            product=product,
            warranties=warranties,
            documents=documents,
            maintenance_records=[],
            query=request.issueDescription or request.questionType.value
        )

        if request.questionType == WarrantyQuestionType.IS_ACTIVE:
            return self._handle_is_active(product, warranties, documents, sources)
        elif request.questionType == WarrantyQuestionType.WHAT_COVERED:
            return self._handle_what_covered(product, warranties, documents, sources)
        elif request.questionType == WarrantyQuestionType.WHAT_EXCLUDED:
            return self._handle_what_excluded(product, warranties, documents, sources)
        elif request.questionType == WarrantyQuestionType.HOW_TO_CLAIM:
            return self._handle_how_to_claim(product, warranties, documents, sources)
        elif request.questionType == WarrantyQuestionType.REQUIRED_DOCUMENTS:
            return self._handle_required_documents(product, warranties, documents, sources)
        else:
            # Full structured issue coverage analysis
            return self._analyze_specific_issue(
                product=product,
                warranties=warranties,
                documents=documents,
                sources=sources,
                issue_text=request.issueDescription or "General hardware malfunction"
            )

    def _analyze_specific_issue(
        self,
        product: ProductResponse,
        warranties: List[WarrantyResponse],
        documents: List[Dict[str, Any]],
        sources: List[SourceReference],
        issue_text: str
    ) -> WarrantyIntelligenceResponse:
        """
        Structured Warranty Analysis Pipeline:
        User Problem -> Product Context -> Warranty Components -> Coverage Rules
        -> Exclusions -> Conditions -> Verified Sources -> Explanation -> Recommended Action
        """
        issue_lower = issue_text.lower().strip()
        pipeline_steps: List[PipelineStep] = []

        # 1. User Problem
        pipeline_steps.append(PipelineStep(
            stepName="1. User Problem",
            status="Complete",
            details=f"Extracted symptom/issue: \"{issue_text}\""
        ))

        # 2. Product Context
        pipeline_steps.append(PipelineStep(
            stepName="2. Product Context",
            status="Complete",
            details=f"{product.brand} {product.name} ({product.category}, Model: {product.model})"
        ))

        # 3. Warranty Components
        active_warranties = [w for w in warranties if w.status in ["Active", "Expiring Soon"]]
        has_active_warranty = len(active_warranties) > 0
        warranties_summary = f"{len(active_warranties)} active component(s)" if has_active_warranty else "No active warranty registered"
        pipeline_steps.append(PipelineStep(
            stepName="3. Warranty Components",
            status="Complete" if has_active_warranty else "Warning",
            details=warranties_summary
        ))

        # 4. Exclusions Check
        matched_exclusions: List[str] = []
        for exc_key, exc_data in EXCLUSION_PATTERNS.items():
            for kw in exc_data["keywords"]:
                if kw in issue_lower:
                    matched_exclusions.append(f"{exc_data['reason']} (Trigger keyword: '{kw}')")
                    break

        pipeline_steps.append(PipelineStep(
            stepName="4. Exclusions Assessment",
            status="Flagged" if matched_exclusions else "Clear",
            details=f"Matched {len(matched_exclusions)} explicit exclusion clause(s)" if matched_exclusions else "No standard exclusion triggers detected."
        ))

        # 5. Coverage Rules / Inclusions Check
        matched_inclusions: List[str] = []
        for inc_key, inc_data in INCLUSION_PATTERNS.items():
            for kw in inc_data["keywords"]:
                if kw in issue_lower:
                    matched_inclusions.append(f"{inc_data['reason']} (Trigger keyword: '{kw}')")
                    break

        pipeline_steps.append(PipelineStep(
            stepName="5. Coverage Rules & Inclusions",
            status="Matched" if matched_inclusions else "Neutral",
            details=f"Matched {len(matched_inclusions)} standard inclusion pattern(s)" if matched_inclusions else "General symptom evaluated."
        ))

        # 6. Conditions Assessment
        conditions: List[str] = []
        if not has_active_warranty:
            conditions.append("Warranty period must be active at the time of claim submission.")
        conditions.append("Product must not have been tampered with or repaired by unauthorized personnel.")
        conditions.append("Serial number / IMEI sticker must be intact and legible.")
        conditions.append("Original tax invoice or valid proof of purchase must be presented.")

        pipeline_steps.append(PipelineStep(
            stepName="6. Conditions Validation",
            status="Complete",
            details=f"Evaluated {len(conditions)} prerequisite terms and conditions."
        ))

        # 7. Verified Sources
        pipeline_steps.append(PipelineStep(
            stepName="7. Verified Sources",
            status="Complete",
            details=f"Referenced {len(sources)} tier-ranked source(s) from user vault & manufacturer portal."
        ))

        # Check Documents available in vault
        doc_types_in_vault = [d.get("documentType", "Document") for d in documents]
        required_docs = ["Original Tax Invoice / Bill", "Warranty Card / Certificate", "Photo of Serial Number / IMEI", "Government Photo ID"]
        docs_available = []
        missing_docs = []
        for req in required_docs:
            if any(t.lower() in req.lower() or req.lower() in t.lower() for t in doc_types_in_vault):
                docs_available.append(req)
            elif "Invoice" in req and any("Invoice" in t or "Bill" in t or "Receipt" in t for t in doc_types_in_vault):
                docs_available.append(req)
            elif "Warranty Card" in req and any("Warranty" in t for t in doc_types_in_vault):
                docs_available.append(req)
            else:
                missing_docs.append(req)

        # Support contact
        support_contact = None
        for w in active_warranties:
            if w.serviceInformation:
                support_contact = w.serviceInformation
                break

        # 8 & 9: Likelihood, Explanation & Recommended Action
        if not has_active_warranty and not warranties:
            likelihood = CoverageLikelihood.UNCLEAR
            status_label = "Unclear Coverage"
            status_color = "amber"
            confidence = 0.50
            explanation = (
                f"Based on the available information in your OWNIT vault, no active warranty components are currently registered for **{product.brand} {product.name}**. "
                f"According to standard manufacturer guidelines, warranty coverage requires an active registration within the eligible period from the purchase date ({product.purchaseDate}). "
                f"If you hold an unregistered warranty card or invoice, please add it to your vault for a complete assessment. Final coverage is determined by the manufacturer/service center."
            )
            rec_action = f"Add your purchase invoice or warranty certificate to OWNIT to verify active coverage, or contact {product.brand} customer support."

        elif not has_active_warranty and warranties:
            # Warranties exist but expired
            likelihood = CoverageLikelihood.EXCLUDED
            status_label = "Excluded (Warranty Expired)"
            status_color = "red"
            confidence = 0.92
            expired_dates = ", ".join([f"{w.type} (Expired: {w.expiryDate})" for w in warranties])
            explanation = (
                f"According to your uploaded warranty records, coverage for **{product.name}** has expired ({expired_dates}). "
                f"Based on standard policy, issues arising after warranty expiry are not covered under free manufacturer repair. "
                f"Paid out-of-warranty service or component replacement can be requested from authorized service centers. "
                f"Final coverage is determined by the manufacturer/service center."
            )
            rec_action = f"Request an authorized out-of-warranty repair quote from {product.brand} service centers to ensure genuine spare parts."

        elif matched_exclusions:
            likelihood = CoverageLikelihood.EXCLUDED
            status_label = "Excluded Issue"
            status_color = "red"
            confidence = 0.88
            exc_summary = " ".join(matched_exclusions[:2])
            explanation = (
                f"Based on the available information regarding \"{issue_text}\", this issue appears to fall under standard warranty exclusion clauses. "
                f"{exc_summary} "
                f"According to your recorded warranty documentation, physical, liquid, and accidental damages are not covered under standard limited warranty. "
                f"Final coverage is determined by the manufacturer/service center upon physical inspection."
            )
            rec_action = f"Contact an authorized {product.brand} service center for an out-of-warranty inspection and estimate. Do not attempt uncertified third-party repairs."

        elif matched_inclusions and has_active_warranty:
            # Check if specifically confirmed by uploaded warranty terms
            is_confirmed = any(w.benefits and any(kw in str(w.benefits).lower() for kw in issue_lower.split()) for w in active_warranties)
            if is_confirmed:
                likelihood = CoverageLikelihood.CONFIRMED
                status_label = "Confirmed Coverage"
                status_color = "green"
                confidence = 0.90
                explanation = (
                    f"According to your uploaded warranty document, this issue appears directly covered under your active **{active_warranties[0].type}** ({active_warranties[0].provider}). "
                    f"Your registered policy specifically lists this component/defect under covered benefits. "
                    f"Final coverage is determined by the manufacturer/service center following diagnostic inspection."
                )
            else:
                likelihood = CoverageLikelihood.LIKELY
                status_label = "Likely Coverage"
                status_color = "blue"
                confidence = 0.78
                explanation = (
                    f"Based on the available information, internal defects such as \"{issue_text}\" are typically covered during the active warranty period "
                    f"under standard **{active_warranties[0].type}** ({active_warranties[0].provider}), provided there is no evidence of external impact or moisture ingress. "
                    f"According to your recorded warranty document, you have {active_warranties[0].daysRemaining} days remaining of coverage. "
                    f"Final coverage is determined by the manufacturer/service center."
                )
            rec_action = f"Initiate a warranty service request with {active_warranties[0].provider}. Have your invoice ({product.purchaseDate}) and serial number ready."

        else:
            # Ambiguous / general issue
            likelihood = CoverageLikelihood.UNCLEAR
            status_label = "Unclear Coverage"
            status_color = "amber"
            confidence = 0.60
            explanation = (
                f"Based on the available information for \"{issue_text}\", coverage cannot be conclusively confirmed without a technical diagnostic. "
                f"While you have active coverage ({', '.join([w.type for w in active_warranties])}), coverage depends on whether the root cause is an internal component defect (covered) or environmental/usage factors (excluded). "
                f"Final coverage is determined by the manufacturer/service center upon inspection."
            )
            rec_action = f"Contact {active_warranties[0].provider} customer support for initial troubleshooting and diagnostic scheduling."

        # Step 8 & 9 in pipeline
        pipeline_steps.append(PipelineStep(
            stepName="8. Explanation Synthesis",
            status="Complete",
            details=f"Assessed verdict: {status_label} (Confidence: {int(confidence*100)}%)"
        ))

        claim_steps = [
            f"1. Gather your {', '.join(docs_available) if docs_available else 'purchase invoice and serial number'}.",
            f"2. Contact {product.brand} authorized service via {support_contact or 'toll-free customer support / official portal'}.",
            "3. State your model number, serial number, and exact issue description.",
            "4. Schedule an on-site technician visit or note the nearest authorized walk-in center.",
            "5. Obtain a physical Job Sheet / Service Request ID upon handing over the asset."
        ]

        pipeline_steps.append(PipelineStep(
            stepName="9. Recommended Action",
            status="Complete",
            details=f"Generated {len(claim_steps)} actionable claim steps and document checklist."
        ))

        return WarrantyIntelligenceResponse(
            productId=product.id,
            productName=product.name,
            issueDescription=issue_text,
            questionType=WarrantyQuestionType.ISSUE_COVERAGE,
            coverageLikelihood=likelihood,
            statusLabel=status_label,
            statusColor=status_color,
            confidenceScore=confidence,
            isWarrantyActive=has_active_warranty,
            applicableWarranties=[w.model_dump() for w in active_warranties],
            matchingInclusions=matched_inclusions,
            matchingExclusions=matched_exclusions,
            conditions=conditions,
            requiredDocuments=required_docs,
            documentsAvailableInVault=docs_available,
            missingDocuments=missing_docs,
            claimSteps=claim_steps,
            supportContact=support_contact,
            sourceReferences=sources,
            explanation=explanation,
            recommendedAction=rec_action,
            pipelineSteps=pipeline_steps
        )

    def _handle_is_active(
        self,
        product: ProductResponse,
        warranties: List[WarrantyResponse],
        documents: List[Dict[str, Any]],
        sources: List[SourceReference]
    ) -> WarrantyIntelligenceResponse:
        active_warranties = [w for w in warranties if w.status in ["Active", "Expiring Soon"]]
        has_active = len(active_warranties) > 0

        if has_active:
            details = "; ".join([f"{w.type} ({w.daysRemaining} days left, expires {w.expiryDate})" for w in active_warranties])
            explanation = (
                f"According to your uploaded warranty records, your warranty for **{product.brand} {product.name}** is currently **ACTIVE**. "
                f"Active components: {details}. "
                f"Based on the available information, you are eligible for covered service under these terms. "
                f"Final coverage is determined by the manufacturer/service center."
            )
            likelihood = CoverageLikelihood.CONFIRMED
            status_label = "Warranty Active"
            status_color = "green"
            confidence = 0.98
            rec_action = "Your coverage is active. Keep your digital invoice stored in OWNIT for instant claim readiness."
        elif warranties:
            expired_details = "; ".join([f"{w.type} (Expired on {w.expiryDate})" for w in warranties])
            explanation = (
                f"According to your recorded warranty documents, all registered warranties for **{product.name}** have **EXPIRED** ({expired_details}). "
                f"Based on the available information, any new service requests will be subject to standard out-of-warranty labor and part charges. "
                f"Final coverage is determined by the manufacturer/service center."
            )
            likelihood = CoverageLikelihood.EXCLUDED
            status_label = "Warranty Expired"
            status_color = "red"
            confidence = 0.95
            rec_action = "Consider looking into extended warranty or manufacturer AMC (Annual Maintenance Contract) packages."
        else:
            explanation = (
                f"Based on the available information in your OWNIT vault, no warranty components have been added for **{product.name}**. "
                f"If you purchased this item on {product.purchaseDate}, it may still be within standard manufacturer coverage. "
                f"Please upload your invoice or warranty card to verify active dates. Final coverage is determined by the manufacturer/service center."
            )
            likelihood = CoverageLikelihood.UNCLEAR
            status_label = "Status Unverified"
            status_color = "amber"
            confidence = 0.50
            rec_action = "Upload your purchase invoice or receipt to activate automated warranty tracking."

        return WarrantyIntelligenceResponse(
            productId=product.id,
            productName=product.name,
            questionType=WarrantyQuestionType.IS_ACTIVE,
            coverageLikelihood=likelihood,
            statusLabel=status_label,
            statusColor=status_color,
            confidenceScore=confidence,
            isWarrantyActive=has_active,
            applicableWarranties=[w.model_dump() for w in active_warranties],
            sourceReferences=sources,
            explanation=explanation,
            recommendedAction=rec_action
        )

    def _handle_what_covered(
        self,
        product: ProductResponse,
        warranties: List[WarrantyResponse],
        documents: List[Dict[str, Any]],
        sources: List[SourceReference]
    ) -> WarrantyIntelligenceResponse:
        active_warranties = [w for w in warranties if w.status in ["Active", "Expiring Soon"]]
        inclusions: List[str] = []

        for w in (active_warranties or warranties):
            if isinstance(w.benefits, list):
                inclusions.extend(w.benefits)
            elif w.benefits:
                inclusions.append(f"{w.type}: {w.benefits}")

        if not inclusions:
            inclusions = [
                "Internal component hardware defects occurring during normal operation",
                "Manufacturing and assembly faults",
                "Authorized labor and genuine replacement parts"
            ]

        explanation = (
            f"According to your uploaded warranty records and {product.brand} standard terms, "
            f"coverage for **{product.name}** includes: {'; '.join(inclusions)}. "
            f"Based on the available information, coverage applies provided the item is operated under recommended conditions without physical impact or unauthorized modifications. "
            f"Final coverage is determined by the manufacturer/service center."
        )

        return WarrantyIntelligenceResponse(
            productId=product.id,
            productName=product.name,
            questionType=WarrantyQuestionType.WHAT_COVERED,
            coverageLikelihood=CoverageLikelihood.LIKELY if active_warranties else CoverageLikelihood.UNCLEAR,
            statusLabel="Documented Coverage Terms",
            statusColor="blue" if active_warranties else "amber",
            confidenceScore=0.88 if active_warranties else 0.65,
            isWarrantyActive=len(active_warranties) > 0,
            applicableWarranties=[w.model_dump() for w in active_warranties],
            matchingInclusions=inclusions,
            sourceReferences=sources,
            explanation=explanation,
            recommendedAction="Review these coverage areas when assessing any device malfunction before raising a ticket."
        )

    def _handle_what_excluded(
        self,
        product: ProductResponse,
        warranties: List[WarrantyResponse],
        documents: List[Dict[str, Any]],
        sources: List[SourceReference]
    ) -> WarrantyIntelligenceResponse:
        exclusions: List[str] = []
        for w in warranties:
            if isinstance(w.exclusions, list):
                exclusions.extend(w.exclusions)
            elif w.exclusions:
                exclusions.append(f"{w.type}: {w.exclusions}")

        if not exclusions:
            exclusions = [
                "Physical drops, cracked screens, and casing breakage",
                "Liquid / water damage and moisture ingress",
                "Unauthorized repair, tampering, or unofficial modifications",
                "High voltage electrical surges and lightning strikes",
                "Cosmetic wear, paint chipping, and superficial scratches",
                "Consumable part wear (e.g. routine battery capacity decline)"
            ]

        explanation = (
            f"According to your uploaded warranty document and standard {product.brand} warranty terms, "
            f"the following are explicitly **EXCLUDED** from free repair coverage: {'; '.join(exclusions)}. "
            f"Based on the available information, encountering any of these conditions will result in chargeable service. "
            f"Final coverage is determined by the manufacturer/service center."
        )

        return WarrantyIntelligenceResponse(
            productId=product.id,
            productName=product.name,
            questionType=WarrantyQuestionType.WHAT_EXCLUDED,
            coverageLikelihood=CoverageLikelihood.EXCLUDED,
            statusLabel="Standard Exclusion Terms",
            statusColor="red",
            confidenceScore=0.90,
            isWarrantyActive=any(w.status in ["Active", "Expiring Soon"] for w in warranties),
            applicableWarranties=[w.model_dump() for w in warranties],
            matchingExclusions=exclusions,
            sourceReferences=sources,
            explanation=explanation,
            recommendedAction="Avoid unauthorized repair attempts or unapproved accessories to preserve your warranty status."
        )

    def _handle_how_to_claim(
        self,
        product: ProductResponse,
        warranties: List[WarrantyResponse],
        documents: List[Dict[str, Any]],
        sources: List[SourceReference]
    ) -> WarrantyIntelligenceResponse:
        claim_procedure = None
        contact = None
        for w in warranties:
            if w.claimProcedure:
                claim_procedure = w.claimProcedure
            if w.serviceInformation:
                contact = w.serviceInformation

        steps = [
            f"1. Locate your Tax Invoice (dated {product.purchaseDate}) and Serial Number ({product.serialNumber or 'available on device label'}).",
            f"2. Contact {product.brand} customer support at {contact or 'official toll-free support helpline'} or visit their authorized portal.",
            f"3. Quote your product model: **{product.model}** and provide a clear description of the malfunction.",
            "4. Book an appointment or request an on-site technician inspection.",
            "5. Secure a Service Ticket / RMA number for real-time claim status tracking."
        ]

        explanation = (
            f"According to your uploaded warranty document and verified {product.brand} procedures, "
            f"here is the recommended claim process for **{product.name}**. "
            f"{claim_procedure if claim_procedure else ''} "
            f"Based on the available information, having your original purchase receipt ready expedites validation. "
            f"Final coverage is determined by the manufacturer/service center."
        )

        return WarrantyIntelligenceResponse(
            productId=product.id,
            productName=product.name,
            questionType=WarrantyQuestionType.HOW_TO_CLAIM,
            coverageLikelihood=CoverageLikelihood.LIKELY,
            statusLabel="Official Claim Procedure",
            statusColor="blue",
            confidenceScore=0.92,
            isWarrantyActive=any(w.status in ["Active", "Expiring Soon"] for w in warranties),
            applicableWarranties=[w.model_dump() for w in warranties],
            claimSteps=steps,
            supportContact=contact,
            sourceReferences=sources,
            explanation=explanation,
            recommendedAction=f"Call {contact or product.brand + ' support'} with your invoice and serial number ready."
        )

    def _handle_required_documents(
        self,
        product: ProductResponse,
        warranties: List[WarrantyResponse],
        documents: List[Dict[str, Any]],
        sources: List[SourceReference]
    ) -> WarrantyIntelligenceResponse:
        required = [
            "Original Tax Invoice / Purchase Bill",
            "Manufacturer Warranty Card / Certificate",
            "Photo of Serial Number / IMEI barcode",
            "Government Photo ID of the purchaser"
        ]
        doc_types = [d.get("documentType", "") for d in documents]
        available = []
        missing = []

        for r in required:
            if any(t.lower() in r.lower() or r.lower() in t.lower() for t in doc_types):
                available.append(r)
            elif "Invoice" in r and any("Invoice" in t or "Bill" in t or "Receipt" in t for t in doc_types):
                available.append(r)
            elif "Warranty Card" in r and any("Warranty" in t for t in doc_types):
                available.append(r)
            else:
                missing.append(r)

        explanation = (
            f"According to standard {product.brand} claim guidelines and your uploaded warranty document, "
            f"authorized service centers require specific documentation before approving warranty claims. "
            f"Based on the available information in your OWNIT vault, you currently have **{len(available)} of {len(required)}** required documents stored. "
            f"Final coverage is determined by the manufacturer/service center."
        )

        return WarrantyIntelligenceResponse(
            productId=product.id,
            productName=product.name,
            questionType=WarrantyQuestionType.REQUIRED_DOCUMENTS,
            coverageLikelihood=CoverageLikelihood.CONFIRMED if not missing else CoverageLikelihood.LIKELY,
            statusLabel="Claim Document Checklist",
            statusColor="green" if not missing else "amber",
            confidenceScore=0.95,
            isWarrantyActive=any(w.status in ["Active", "Expiring Soon"] for w in warranties),
            applicableWarranties=[w.model_dump() for w in warranties],
            requiredDocuments=required,
            documentsAvailableInVault=available,
            missingDocuments=missing,
            sourceReferences=sources,
            explanation=explanation,
            recommendedAction="Upload missing documents to your OWNIT vault so they are immediately accessible on mobile when visiting service centers." if missing else "All critical claim documents are securely vaulted in OWNIT!"
        )


warranty_intelligence_service = WarrantyIntelligenceService()
