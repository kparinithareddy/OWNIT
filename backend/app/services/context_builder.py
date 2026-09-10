import logging
from typing import List, Dict, Any, Tuple, Optional
from app.schemas.product import ProductResponse
from app.schemas.warranty import WarrantyResponse
from app.schemas.sources import SourceReference
from app.services.retrieval_service import retrieval_service

logger = logging.getLogger("ownit.services.context_builder")


def build_product_system_context(
    product: ProductResponse,
    warranties: List[WarrantyResponse],
    documents: List[Dict[str, Any]],
    maintenance_records: List[Dict[str, Any]],
    recommendations: List[Dict[str, Any]],
    service_records: Optional[List[Dict[str, Any]]] = None,
    query: str = ""
) -> Tuple[str, List[SourceReference]]:
    """
    Constructs an extensive, fact-anchored system prompt containing all known product information
    structured by the 4-tier source hierarchy:
    Tier 1: Uploaded User Documents
    Tier 2: Official Manufacturer Sources
    Tier 3: Reliable External Sources (Seller policy)
    Tier 4: General Knowledge
    """
    # Retrieve ranked source references
    structured_sources = retrieval_service.retrieve_hierarchical_sources(
        product=product,
        warranties=warranties,
        documents=documents,
        maintenance_records=maintenance_records,
        query=query
    )

    # 1. Product Core Information
    product_lines = [
        f"Product Name: {product.name}",
        f"Brand / Manufacturer: {product.brand}",
        f"Model: {product.model}",
        f"Category: {product.category}",
        f"Purchase Date: {product.purchaseDate}",
        f"Unit Price: ₹{product.price:,.2f}",
        f"Quantity: {product.quantity}",
        f"Seller / Store: {product.seller or 'Not recorded'}",
        f"Serial Number: {product.serialNumber or 'Not recorded'}",
        f"IMEI: {product.imei or 'N/A'}",
        f"Notes: {product.notes or 'None'}"
    ]

    # 2. Return & Replacement Policy (Tier 3)
    if product.returnDuration and product.returnDuration != "None":
        product_lines.extend([
            f"Return Duration: {product.returnDuration}",
            f"Return Deadline: {product.returnDeadline or 'N/A'} (Status: {product.returnStatus})",
            f"Return Policy Source: {product.returnPolicySource or 'Seller policy'}"
        ])

    # 3. Warranty Components (Tier 1 & Tier 2)
    warranty_sections = []
    if warranties:
        for w in warranties:
            w_block = [
                f"• Type: {w.type}",
                f"  Provider: {w.provider}",
                f"  Duration: {w.duration}",
                f"  Coverage Window: {w.startDate} to {w.expiryDate} (Status: {w.status}, {w.daysRemaining} days remaining)",
                f"  Inclusions / Benefits: {', '.join(w.benefits) if isinstance(w.benefits, list) else (w.benefits or 'Standard parts and labor')}",
                f"  Exclusions: {', '.join(w.exclusions) if isinstance(w.exclusions, list) else (w.exclusions or 'Physical damage, liquid ingress, unauthorized tampering')}",
                f"  Claim Procedure: {w.claimProcedure or 'Contact authorized service center with bill and serial number'}",
                f"  Support Contact: {w.serviceInformation or 'Standard customer support'}"
            ]
            warranty_sections.append("\n".join(w_block))
    else:
        warranty_sections.append("No active warranty components registered in database.")

    # 4. Uploaded Documents (Tier 1)
    doc_sections = []
    if documents:
        for d in documents:
            doc_type = d.get("documentType", "Document")
            doc_sections.append(f"• [Tier 1 User Document] {doc_type}: {d.get('originalFilename')} (Uploaded: {d.get('uploadedAt', '')})")
    else:
        doc_sections.append("No paperwork or invoices attached yet.")

    # 5. Maintenance History
    maint_sections = []
    if maintenance_records:
        for m in maintenance_records:
            m_lines = [
                f"• [{m.get('status', 'Completed').upper()}] {m.get('title')} ({m.get('type')}) - Date: {m.get('date')}",
                f"  Description: {m.get('description', 'N/A')}",
                f"  Provider: {m.get('serviceProvider') or 'Self / Local Technician'}",
                f"  Cost: ₹{m.get('cost', 0):,.2f}" if m.get('cost') is not None else "  Cost: N/A",
                f"  Next Due Date: {m.get('nextDueDate') or 'None'}"
            ]
            maint_sections.append("\n".join(m_lines))
    else:
        maint_sections.append("No past routine maintenance logs recorded.")

    # 6. Service & Repair History
    service_sections = []
    if service_records:
        for s in service_records:
            covered_str = "Yes (Warranty Claim)" if s.get("warrantyCovered") else "No (Chargeable / Out-of-Warranty)"
            s_lines = [
                f"• [Date: {s.get('serviceDate')}] Defect/Problem: {s.get('problem')}",
                f"  Authorized Center / Provider: {s.get('serviceCenter')}",
                f"  Work Performed: {s.get('workPerformed')}",
                f"  Warranty Covered: {covered_str}",
                f"  Cost: ₹{s.get('cost', 0):,.2f}" if s.get('cost') is not None else "  Cost: N/A",
                f"  Notes: {s.get('notes') or 'None'}"
            ]
            service_sections.append("\n".join(s_lines))
    else:
        service_sections.append("No past official repair or service logs recorded.")

    # 7. Verified Manufacturer & External Sources Block
    source_hierarchy_lines = []
    for s in structured_sources:
        tier_label = {
            "user_document": "Priority 1: User Document",
            "official_manufacturer": "Priority 2: Official Manufacturer Source",
            "reliable_external": "Priority 3: Reliable External / Seller Source",
            "general_knowledge": "Priority 4: General Knowledge / Preventive Care"
        }.get(s.sourceType, "Source")
        url_part = f" ({s.url})" if s.url else (f" [Domain: {s.domain}]" if s.domain else "")
        source_hierarchy_lines.append(f"• [{tier_label}] {s.title}{url_part}: {s.details or ''}")

    # Assemble System Prompt
    system_prompt = f"""You are OWNIT Assistant, an intelligent, objective, and privacy-first product management assistant for physical consumer assets.

You are assisting the verified owner of this specific asset.

=== SOURCE PRIORITY HIERARCHY ===
When answering questions or checking policies, strictly prioritize information in this order:
1. Uploaded user documents & invoices (Highest priority)
2. Official manufacturer sources & verified OEM warranty portals
3. Reliable external sources & verified seller return terms
4. General AI knowledge & preventive guidelines (Lowest priority)

=== KNOWN SOURCES & POLICIES ===
{chr(10).join(source_hierarchy_lines)}

=== TARGET PRODUCT DOSSIER ===
{chr(10).join(product_lines)}

=== RECORDED WARRANTY COVERAGE ===
{chr(10).join(warranty_sections)}

=== ATTACHED DOCUMENTS & BILLS ===
{chr(10).join(doc_sections)}

=== PAST SERVICE & REPAIR HISTORY ===
{chr(10).join(service_sections)}

=== ROUTINE MAINTENANCE CARE ===
{chr(10).join(maint_sections)}

=== STRICT INSTRUCTIONS & ETHICAL BOUNDS ===
1. CONVERSATIONAL CONTEXT: The user may ask multi-turn questions like "How do I clean it?" followed by "Is that covered by warranty?". Understand pronouns and references in context of this specific product ({product.brand} {product.name}).
2. SOURCE IDENTIFICATION: Clearly identify the source used for key claims (e.g. "Source: Uploaded Warranty Card" or "Source: Samsung India Official Warranty Policy").
3. DO NOT FABRICATE SOURCES OR URLS: Never invent warranty coverage, URLs, or policy clauses.
4. UNVERIFIED INFORMATION: If information cannot be verified from the uploaded documents or official manufacturer records, clearly tell the user: "I cannot verify this from your uploaded documents or official manufacturer policies. Please consult authorized service representatives."
5. TONE: Helpful, concise, professional, and practical. Format responses cleanly with markdown bullet points where appropriate.
"""

    return system_prompt, structured_sources

