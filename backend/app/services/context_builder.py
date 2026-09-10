import logging
from typing import List, Dict, Any, Tuple
from app.schemas.product import ProductResponse
from app.schemas.warranty import WarrantyResponse

logger = logging.getLogger("ownit.services.context_builder")


def build_product_system_context(
    product: ProductResponse,
    warranties: List[WarrantyResponse],
    documents: List[Dict[str, Any]],
    maintenance_records: List[Dict[str, Any]],
    recommendations: List[Dict[str, Any]]
) -> Tuple[str, List[str]]:
    """
    Constructs an extensive, fact-anchored system prompt containing all known product information.
    Enforces strict anti-hallucination rules and builds the list of verified sources.
    """
    sources: List[str] = []

    # 1. Product Core Information
    sources.append("Product Record")
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

    # 2. Return & Replacement Policy
    if product.returnDuration and product.returnDuration != "None":
        sources.append("Return & Replacement Policy")
        product_lines.extend([
            f"Return Duration: {product.returnDuration}",
            f"Return Deadline: {product.returnDeadline or 'N/A'} (Status: {product.returnStatus})",
            f"Return Policy Source: {product.returnPolicySource or 'Seller policy'}"
        ])

    # 3. Warranty Components
    warranty_sections = []
    if warranties:
        for w in warranties:
            sources.append(f"{w.type} ({w.provider})")
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

    # 4. Uploaded Documents
    doc_sections = []
    if documents:
        for d in documents:
            doc_type = d.get("documentType", "Document")
            sources.append(f"{doc_type}: {d.get('originalFilename', 'file')}")
            doc_sections.append(f"• {doc_type}: {d.get('originalFilename')} (Uploaded: {d.get('uploadedAt', '')})")
    else:
        doc_sections.append("No paperwork or invoices attached yet.")

    # 5. Maintenance History
    maint_sections = []
    if maintenance_records:
        for m in maintenance_records:
            sources.append(f"Maintenance Log: {m.get('title', 'Service')}")
            m_lines = [
                f"• [{m.get('status', 'Completed').upper()}] {m.get('title')} ({m.get('type')}) - Date: {m.get('date')}",
                f"  Description: {m.get('description', 'N/A')}",
                f"  Provider: {m.get('serviceProvider') or 'Self / Local Technician'}",
                f"  Cost: ₹{m.get('cost', 0):,.2f}" if m.get('cost') is not None else "  Cost: N/A",
                f"  Next Due Date: {m.get('nextDueDate') or 'None'}"
            ]
            maint_sections.append("\n".join(m_lines))
    else:
        maint_sections.append("No past maintenance or service logs recorded.")

    # 6. General Preventive Guidelines (Clearly marked as non-OEM unless verified)
    rec_sections = []
    if recommendations:
        for r in recommendations:
            rec_sections.append(
                f"• {r.get('title')}: {r.get('description')} (Interval: every {r.get('suggestedIntervalMonths')} months) "
                f"[Source: {r.get('source')} - Note: {r.get('disclaimer')}]"
            )
    else:
        rec_sections.append("Standard preventive care guidelines apply.")

    # Assemble System Prompt
    system_prompt = f"""You are OWNIT Assistant, an intelligent, objective, and privacy-first product management assistant for physical consumer assets.

You are assisting the verified owner of this specific asset.

=== TARGET PRODUCT DOSSIER ===
{chr(10).join(product_lines)}

=== RECORDED WARRANTY COVERAGE ===
{chr(10).join(warranty_sections)}

=== ATTACHED DOCUMENTS & BILLS ===
{chr(10).join(doc_sections)}

=== SERVICE & MAINTENANCE HISTORY ===
{chr(10).join(maint_sections)}

=== GENERAL CARE GUIDELINES ===
{chr(10).join(rec_sections)}

=== STRICT INSTRUCTIONS & ETHICAL BOUNDS ===
1. CONVERSATIONAL CONTEXT: The user may ask multi-turn questions like "How do I clean it?" followed by "Is that covered by warranty?". Understand pronouns and references in context of this specific product ({product.brand} {product.name}).
2. NO HALLUCINATED WARRANTIES: You must NOT invent warranty coverage. If the user asks whether a specific issue, cleaning, or accidental damage is covered and it is NOT explicitly listed in the inclusions above, state clearly: "I cannot verify warranty coverage for this from your recorded documents. Please check with the manufacturer or authorized service center."
3. SOURCING TRANSPARENCY: Never claim an instruction is manufacturer-approved unless it comes directly from verified documentation. State general care tips as general industry preventive practices.
4. TONE: Helpful, concise, professional, and practical. Format responses cleanly with markdown bullet points where appropriate.
"""

    return system_prompt, list(set(sources))
