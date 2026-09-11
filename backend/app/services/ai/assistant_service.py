import logging
from datetime import datetime, timezone
from typing import List, Dict, Any, Optional, Tuple
from bson import ObjectId

from app.core.exceptions import NotFoundException, ValidationException
from app.schemas.ai import (
    AIMessageSendRequest,
    AIMessageResponse,
    AIConversationResponse,
    AIAction
)
from app.schemas.sources import SourceReference
from app.services.ai.ollama_service import ollama_service
from app.services.ai.retrieval_service import retrieval_service, IntentClassifier
from app.services.ai.prompt_service import prompt_service
from app.services.ai.source_service import source_service
from app.services.ai.conversation_service import (
    conversation_service,
    format_conversation_doc,
    format_message_doc
)
from app.services.user_service import user_service
from app.services.translation_service import translation_service

logger = logging.getLogger("ownit.services.ai.assistant")


class AssistantService:
    """
    Master orchestrator for Global and Product AI Assistant modes.
    Integrates intent routing, targeted retrieval, prompt engineering, multi-turn memory,
    safe action generation, and deterministic offline fallbacks.
    """

    def _generate_offline_fallback(
        self,
        intent: str,
        context_type: str,
        portfolio_stats: Dict[str, Any],
        product_data: Dict[str, Any],
        query: str,
        language: str = "en"
    ) -> Tuple[str, List[AIAction]]:
        """
        Produces a factual, deterministic natural language response when Ollama is unreachable.
        """
        actions: List[AIAction] = []

        if context_type == "global" or intent in ["count_summary", "life_score"] or not product_data.get("product"):
            # Global fallbacks
            total_prod = portfolio_stats.get("totalProducts", 0)
            total_val = portfolio_stats.get("totalValue", 0)
            exp_warr = portfolio_stats.get("expiringSoonWarranties", [])
            act_warr = portfolio_stats.get("activeWarranties", [])
            ret_prods = portfolio_stats.get("returnEligibleProducts", [])
            lowest_ls = portfolio_stats.get("lowestLifeScoreProducts", [])
            products = portfolio_stats.get("products", [])

            if intent == "count_summary" or "how many" in query.lower():
                text = (
                    f"📊 **Portfolio Overview**\n\n"
                    f"You currently have **{total_prod} product(s)** registered in OWNIT, with a total estimated value of **₹{total_val:,.2f}**.\n\n"
                    f"• **Active Warranties:** {len(act_warr) + len(exp_warr)}\n"
                    f"• **Expiring Soon (<30 Days):** {len(exp_warr)}\n"
                    f"• **Return-Eligible Items:** {len(ret_prods)}\n"
                    f"• **Total Invoices / Documents:** {portfolio_stats.get('totalDocuments', 0)}\n\n"
                    f"*(Note: Local AI engine is currently in offline fallback mode, providing live database insights directly.)*"
                )
                if products:
                    actions.append(AIAction(
                        actionType="view_product",
                        label=f"View {products[0]['name']}",
                        route=f"/products/{products[0]['id']}",
                        params={"productId": products[0]["id"]}
                    ))
                return text, actions

            elif intent == "warranty":
                if exp_warr:
                    lines = [f"• **{w['productBrand']} {w['productName']}**: {w['type']} expiring on **{w['expiryDate']}** ({w.get('daysRemaining')} days left)" for w in exp_warr]
                    text = (
                        f"⚠️ **Warranties Expiring Soon (<30 Days):**\n\n" +
                        "\n".join(lines) +
                        f"\n\nTotal active warranties across your portfolio: **{len(act_warr) + len(exp_warr)}**."
                    )
                    actions.append(AIAction(
                        actionType="view_warranty",
                        label="View Expiring Warranty",
                        route=f"/products/{exp_warr[0]['productId']}",
                        params={"productId": exp_warr[0]["productId"]}
                    ))
                elif act_warr:
                    lines = [f"• **{w['productBrand']} {w['productName']}**: {w['type']} (Valid until {w['expiryDate']})" for w in act_warr[:5]]
                    text = (
                        f"🛡️ **Active Warranty Overview:**\n\n" +
                        "\n".join(lines) +
                        f"\n\nYou have **{len(act_warr)}** active warranties with no immediate expirations within the next 30 days."
                    )
                else:
                    text = "You currently have no active warranties recorded in your OWNIT vault."
                return text, actions

            elif intent == "return":
                if ret_prods:
                    lines = [f"• **{r['brand']} {r['name']}**: Return window active until **{r['returnDeadline']}** ({r['returnDuration']}, Seller: {r['seller']})" for r in ret_prods]
                    text = (
                        f"🔄 **Return-Eligible Items:**\n\n" +
                        "\n".join(lines) +
                        f"\n\nMake sure to initiate returns before the specified deadlines with original packaging."
                    )
                    actions.append(AIAction(
                        actionType="view_product",
                        label=f"Manage {ret_prods[0]['name']}",
                        route=f"/products/{ret_prods[0]['id']}",
                        params={"productId": ret_prods[0]["id"]}
                    ))
                else:
                    text = "None of your registered products currently have active return windows. All items are past their return deadlines."
                return text, actions

            elif intent == "life_score":
                if lowest_ls:
                    lines = [f"• **{item['brand']} {item['name']}**: Life Score **{item['lifeScore']}/100** ({item.get('category', 'Asset')})" for item in lowest_ls]
                    text = (
                        f"🩺 **Product Health & Life Score Insights:**\n\n"
                        f"The asset requiring the most attention is **{lowest_ls[0]['brand']} {lowest_ls[0]['name']}** with a Life Score of **{lowest_ls[0]['lifeScore']}/100**.\n\n"
                        f"**Lowest scoring items:**\n" +
                        "\n".join(lines) +
                        f"\n\nTip: Uploading missing warranty cards and completing routine maintenance boosts your Life Score."
                    )
                    actions.append(AIAction(
                        actionType="view_product",
                        label=f"Improve {lowest_ls[0]['name']} Score",
                        route=f"/products/{lowest_ls[0]['id']}",
                        params={"productId": lowest_ls[0]["id"]}
                    ))
                else:
                    text = "All your registered products are in good health."
                return text, actions

            else:
                # General global summary
                text = (
                    f"Hello! I am your **OWNIT Global Assistant**.\n\n"
                    f"I have full access to your **{total_prod} products**, **{portfolio_stats.get('totalWarranties', 0)} warranties**, and **{portfolio_stats.get('totalDocuments', 0)} uploaded documents**.\n\n"
                    f"You can ask me questions such as:\n"
                    f"• *'Which of my warranties are expiring soon?'*\n"
                    f"• *'How many products do I have and what is their value?'*\n"
                    f"• *'Which product has the lowest Life Score?'*\n"
                    f"• *'What items can I still return?'*"
                )
                return text, actions

        else:
            # Product-specific fallback
            product = product_data.get("product", {})
            warranties = product_data.get("warranties", [])
            docs = product_data.get("documents", [])
            maint = product_data.get("maintenanceRecords", [])
            srv = product_data.get("serviceRecords", [])

            p_name = product.get("name", "Product")
            p_brand = product.get("brand", "")
            p_id = str(product.get("_id", ""))

            actions.append(AIAction(
                actionType="view_product",
                label=f"View {p_name} Details",
                route=f"/products/{p_id}",
                params={"productId": p_id}
            ))

            if intent == "warranty":
                if warranties:
                    w_lines = []
                    for w in warranties:
                        w_lines.append(f"• **{w.get('type')} ({w.get('provider')})**: Valid until **{w.get('expiryDate')}** ({w.get('status')}, {w.get('daysRemaining')} days remaining)")
                    text = (
                        f"🛡️ **Warranty Details for {p_brand} {p_name}:**\n\n" +
                        "\n".join(w_lines) +
                        f"\n\nTo file a claim, bring your purchase invoice and serial number ({product.get('serialNumber') or 'on receipt'}) to an authorized center."
                    )
                    actions.append(AIAction(
                        actionType="prepare_claim",
                        label="Prepare Claim Draft",
                        route=f"/products/{p_id}",
                        params={"productId": p_id, "action": "claim"}
                    ))
                else:
                    text = f"No active warranties are registered for **{p_brand} {p_name}**. Standard statutory consumer terms may still apply."
                return text, actions

            elif intent == "claim":
                text = (
                    f"📝 **Warranty Claim Guidance for {p_brand} {p_name}:**\n\n"
                    f"1. **Required Documents:** Purchase receipt/bill ({len(docs)} attached in vault), serial number ({product.get('serialNumber') or 'listed on box'}).\n"
                    f"2. **Primary Provider:** {warranties[0].get('provider') if warranties else p_brand}.\n"
                    f"3. **Claim Steps:** Contact authorized service center or call brand support with your registered invoice number."
                )
                actions.append(AIAction(
                    actionType="view_document",
                    label="Open Attached Invoices",
                    route=f"/products/{p_id}",
                    params={"productId": p_id, "tab": "documents"}
                ))
                return text, actions

            elif intent == "maintenance":
                text = (
                    f"🔧 **Maintenance & Care for {p_brand} {p_name}:**\n\n"
                    f"• Clean surfaces regularly with a soft dry or microfiber cloth.\n"
                    f"• Avoid direct liquid sprays and keep vents free of dust.\n"
                    f"• Past maintenance logs recorded: **{len(maint)}**."
                )
                return text, actions

            else:
                text = (
                    f"Here is the dossier for **{p_brand} {p_name}**:\n\n"
                    f"• **Category:** {product.get('category')}\n"
                    f"• **Model:** {product.get('model') or 'N/A'}\n"
                    f"• **Purchase Date:** {product.get('purchaseDate') or 'N/A'} (₹{float(product.get('price', 0) or 0):,.2f})\n"
                    f"• **Warranties:** {len(warranties)} registered\n"
                    f"• **Documents:** {len(docs)} attached\n"
                    f"• **Life Score:** {product.get('lifeScore', 80)}/100"
                )
                return text, actions

    def _generate_contextual_actions(
        self,
        context_type: str,
        product_data: Dict[str, Any],
        portfolio_stats: Dict[str, Any],
        reply_text: str
    ) -> List[AIAction]:
        """
        Generates safe, structured navigation actions for the user based on context and reply content.
        """
        actions: List[AIAction] = []

        if context_type == "product" and product_data.get("product"):
            p = product_data["product"]
            pid = str(p.get("_id", ""))
            pname = p.get("name", "Product")

            # Always offer View Product button
            actions.append(AIAction(
                actionType="view_product",
                label=f"View {pname}",
                route=f"/products/{pid}",
                params={"productId": pid}
            ))

            # If reply mentions warranty or claim
            if any(k in reply_text.lower() for k in ["warranty", "claim", "expire", "coverage"]):
                actions.append(AIAction(
                    actionType="view_warranty",
                    label="Check Warranty",
                    route=f"/products/{pid}",
                    params={"productId": pid, "tab": "warranty"}
                ))

            # If documents exist or are mentioned
            if product_data.get("documents"):
                actions.append(AIAction(
                    actionType="view_document",
                    label="View Documents",
                    route=f"/products/{pid}",
                    params={"productId": pid, "tab": "documents"}
                ))

        elif context_type == "global":
            # If reply talks about expiring warranties, offer jump to that product
            exp_warr = portfolio_stats.get("expiringSoonWarranties", [])
            if exp_warr:
                target = exp_warr[0]
                actions.append(AIAction(
                    actionType="view_warranty",
                    label=f"View Expiring: {target.get('productName')}",
                    route=f"/products/{target.get('productId')}",
                    params={"productId": target.get("productId")}
                ))

            # If lowest life score is mentioned
            lowest = portfolio_stats.get("lowestLifeScoreProducts", [])
            if lowest and len(actions) < 2:
                actions.append(AIAction(
                    actionType="view_product",
                    label=f"View Asset: {lowest[0]['name']}",
                    route=f"/products/{lowest[0]['id']}",
                    params={"productId": lowest[0]["id"]}
                ))

        return actions[:3]

    async def process_message(
        self,
        conversation_id: str,
        user_id: str,
        request: AIMessageSendRequest
    ) -> AIMessageResponse:
        """
        Processes a conversation turn:
        1. Validates and loads conversation & user settings.
        2. Routes context (global vs product) and auto-detects product references.
        3. Retrieves targeted facts from MongoDB.
        4. Synthesizes prompt and calls Ollama LLM.
        5. Falls back cleanly to deterministic response if Ollama is unavailable.
        6. Persists message history and returns structured response with product-tailored source citations.
        """
        conv = await conversation_service.get_conversation(conversation_id, user_id)

        # Context mode determination
        context_type = request.contextType or conv.get("contextType", "global")
        product_id = request.productId or conv.get("productId")

        # Determine user language
        user_lang = "en"
        try:
            user_profile = await user_service.get_by_id(user_id)
            if user_profile and user_profile.get("preferredLanguage"):
                user_lang = user_profile.get("preferredLanguage", "en")
        except Exception as e:
            logger.debug("Could not lookup user preferredLanguage: %s", e)

        # Classify intent
        intent = IntentClassifier.classify_intent(request.message)

        # Retrieve Data
        portfolio_stats = await retrieval_service.get_global_portfolio_stats(user_id)
        product_data = {}
        if product_id:
            product_data = await retrieval_service.get_product_context_data(product_id, user_id)
        elif context_type == "global":
            # Auto-detect if user query mentions a specific product in vault
            msg_lower = request.message.lower()
            matching_prod = None
            for p in portfolio_stats.get("products", []):
                p_name = (p.get("name") or "").lower()
                p_brand = (p.get("brand") or "").lower()
                p_model = (p.get("model") or "").lower()
                if (p_name and p_name in msg_lower) or (p_brand and len(p_brand) > 2 and p_brand in msg_lower) or (p_model and len(p_model) > 3 and p_model in msg_lower):
                    matching_prod = p
                    break
            
            if matching_prod:
                product_data = await retrieval_service.get_product_context_data(matching_prod["id"], user_id)

        # Build System Prompt & Sources
        if context_type == "product" and product_data.get("product"):
            system_prompt, sources = prompt_service.build_product_system_prompt(
                product_data=product_data,
                portfolio_stats=portfolio_stats,
                language=user_lang
            )
        else:
            context_type = "global"
            system_prompt, sources = prompt_service.build_global_system_prompt(
                portfolio_stats=portfolio_stats,
                language=user_lang
            )
            # If a specific product was referenced in global query, include its exact verified sources
            if product_data.get("product"):
                prod_sources = source_service.get_sources_for_product(
                    product=product_data["product"],
                    warranties=product_data.get("warranties", []),
                    documents=product_data.get("documents", [])
                )
                sources = prod_sources + sources

        # Retrieve previous messages for multi-turn conversational transcript
        history_msgs = await conversation_service.get_messages(conversation_id, user_id, limit=8)

        conv_lines = []
        for h in history_msgs:
            spk = "User" if h["role"] == "user" else "Assistant"
            conv_lines.append(f"{spk}: {h['content']}")

        conv_lines.append(f"User: {request.message.strip()}")
        full_user_prompt = "\n\n".join(conv_lines) + "\n\nAssistant:"

        # Persist user message
        await conversation_service.add_message(
            conversation_id=conversation_id,
            user_id=user_id,
            role="user",
            content=request.message.strip()
        )

        # Execute LLM generation
        ai_res = await ollama_service.generate_text(
            prompt=full_user_prompt,
            system_prompt=system_prompt,
            temperature=0.6
        )

        # Determine reply text, sources, and actions
        cited_sources_str: List[str] = []
        cited_source_refs: List[Dict[str, Any]] = []
        actions: List[Dict[str, Any]] = []

        if ai_res.success and ai_res.response:
            ai_reply_text = ai_res.response
            model_used = ai_res.model
            duration_ms = ai_res.durationMs

            # Match source references
            for s in sources:
                s_title_words = [kw.lower() for kw in s.title.split() if len(kw) > 3]
                p_brand = (product_data.get("product", {}).get("brand") or "").lower()
                p_name = (product_data.get("product", {}).get("name") or "").lower()

                if (
                    any(kw in ai_reply_text.lower() for kw in s_title_words)
                    or (s.domain and s.domain.lower() in ai_reply_text.lower())
                    or (p_brand and p_brand in s.title.lower())
                    or (p_name and p_name in s.title.lower())
                    or (s.sourceType in ["user_document", "official_manufacturer"] and len(cited_source_refs) < 2)
                ):
                    if s.title not in cited_sources_str:
                        cited_sources_str.append(s.title)
                        cited_source_refs.append(s.model_dump())

            if not cited_source_refs and sources:
                cited_sources_str = [sources[0].title]
                cited_source_refs = [sources[0].model_dump()]

            gen_actions = self._generate_contextual_actions(context_type, product_data, portfolio_stats, ai_reply_text)
            actions = [a.model_dump() for a in gen_actions]

        else:
            # Deterministic offline fallback
            ai_reply_text, gen_actions = self._generate_offline_fallback(
                intent=intent,
                context_type=context_type,
                portfolio_stats=portfolio_stats,
                product_data=product_data,
                query=request.message,
                language=user_lang
            )
            model_used = "offline-fallback"
            duration_ms = 0.0

            # Tailor cited sources for offline fallback to the relevant product if present
            if sources:
                for s in sources:
                    p_brand = (product_data.get("product", {}).get("brand") or "").lower()
                    p_name = (product_data.get("product", {}).get("name") or "").lower()
                    if (
                        (p_brand and p_brand in s.title.lower())
                        or (p_name and p_name in s.title.lower())
                        or s.sourceType in ["user_document", "official_manufacturer"]
                    ):
                        if s.title not in cited_sources_str:
                            cited_sources_str.append(s.title)
                            cited_source_refs.append(s.model_dump())
                    if len(cited_source_refs) >= 3:
                        break

            if not cited_source_refs and sources:
                cited_sources_str = [sources[0].title]
                cited_source_refs = [sources[0].model_dump()]

            actions = [a.model_dump() for a in gen_actions]

        # Persist assistant reply
        assistant_doc = await conversation_service.add_message(
            conversation_id=conversation_id,
            user_id=user_id,
            role="assistant",
            content=ai_reply_text,
            sources=cited_sources_str[:4],
            source_references=cited_source_refs[:4],
            actions=actions,
            model=model_used,
            duration_ms=duration_ms
        )

        return format_message_doc(assistant_doc)


assistant_service = AssistantService()
