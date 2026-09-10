import logging
import time
from datetime import datetime, timezone
from typing import List, Dict, Any, Optional
from bson import ObjectId
from pymongo import ASCENDING, DESCENDING
import httpx

from app.core.database import db_manager
from app.core.exceptions import NotFoundException
from app.schemas.chat import (
    ChatMessage,
    ChatSendRequest,
    ChatResponse,
    ChatHistoryResponse
)
from app.services.product_service import product_service
from app.services.warranty_service import warranty_service
from app.services.maintenance_service import maintenance_service
from app.services.ai_service import ai_service, OllamaAIService
from app.services.context_builder import build_product_system_context
from app.services.translation_service import translation_service
from app.services.user_service import user_service

logger = logging.getLogger("ownit.services.chat")


from app.schemas.sources import SourceReference


def format_chat_message(doc: Dict[str, Any]) -> ChatMessage:
    raw_refs = doc.get("sourceReferences", [])
    parsed_refs = []
    for r in raw_refs:
        if isinstance(r, dict):
            parsed_refs.append(SourceReference(**r))
        elif isinstance(r, SourceReference):
            parsed_refs.append(r)

    return ChatMessage(
        id=str(doc["_id"]),
        role=doc["role"],
        content=doc["content"],
        sources=doc.get("sources", []),
        sourceReferences=parsed_refs,
        createdAt=doc.get("createdAt", datetime.now(timezone.utc))
    )


class ChatService:
    """
    Manages persistent product-specific multi-turn AI conversations,
    synthesizing rich product context with Ollama inference.
    """

    @property
    def collection(self):
        return db_manager.get_collection("chat_messages")

    @property
    def documents_collection(self):
        return db_manager.get_collection("documents")

    @property
    def maintenance_collection(self):
        return db_manager.get_collection("maintenance_records")

    @property
    def service_records_collection(self):
        return db_manager.get_collection("service_records")

    async def ensure_indexes(self):
        try:
            col = self.collection
            await col.create_index(
                [("productId", ASCENDING), ("userId", ASCENDING), ("createdAt", ASCENDING)],
                name="idx_chat_product_user_created"
            )
            logger.info("Chat messages indexes ensured in MongoDB.")
        except Exception as e:
            logger.warning("Could not create chat messages indexes: %s", e)

    async def get_chat_history(self, product_id: str, user_id: str) -> ChatHistoryResponse:
        """
        Retrieves all persistent chat messages for a product scoped to the owner user.
        """
        product = await product_service.get_product_by_id(product_id, user_id)

        cursor = self.collection.find({
            "productId": product_id,
            "userId": user_id
        }).sort("createdAt", ASCENDING)

        messages = []
        async for doc in cursor:
            messages.append(format_chat_message(doc))

        return ChatHistoryResponse(
            productId=product.id,
            productName=product.name,
            messages=messages,
            totalMessages=len(messages)
        )

    async def clear_chat_history(self, product_id: str, user_id: str) -> bool:
        """
        Clears chat history for a product.
        """
        await product_service.get_product_by_id(product_id, user_id)
        result = await self.collection.delete_many({
            "productId": product_id,
            "userId": user_id
        })
        logger.info("Cleared %s chat messages for product %s", result.deleted_count, product_id)
        return True

    async def send_message(self, user_id: str, data: ChatSendRequest) -> ChatResponse:
        """
        Processes a multi-turn conversation turn:
        1. Verifies product ownership.
        2. Retrieves all relevant context (warranties, documents, maintenance, recommendations).
        3. Retrieves previous message history to maintain conversational continuity.
        4. Synthesizes system prompt and multi-turn prompt.
        5. Calls local AI service (Ollama).
        6. Persists both user message and assistant reply with cited source references in MongoDB.
        """
        product = await product_service.get_product_by_id(data.productId, user_id)

        # Retrieve warranties, documents, maintenance, recommendations in parallel
        warranties = await warranty_service.get_warranties_by_product(data.productId, user_id)

        doc_cursor = self.documents_collection.find({"productId": data.productId, "userId": user_id})
        documents = [d async for d in doc_cursor]

        maint_cursor = self.maintenance_collection.find({"productId": data.productId, "userId": user_id})
        maintenance_records = [m async for m in maint_cursor]

        service_records = []
        if self.service_records_collection is not None:
            srv_cursor = self.service_records_collection.find({"productId": data.productId, "userId": user_id})
            service_records = [s async for s in srv_cursor]

        recommendations = await maintenance_service.get_preventive_recommendations(data.productId, user_id)
        rec_dicts = [r.model_dump() for r in recommendations]

        # Determine user preferred language
        user_lang = "en"
        try:
            user_profile = await user_service.get_by_id(user_id)
            if user_profile and user_profile.get("preferredLanguage"):
                user_lang = user_profile.get("preferredLanguage", "en")
        except Exception as e:
            logger.debug("Could not lookup user preferredLanguage for AI chat: %s", e)

        # Build comprehensive system context & available sources with user's preferred language
        system_prompt, all_sources = build_product_system_context(
            product=product,
            warranties=warranties,
            documents=documents,
            maintenance_records=maintenance_records,
            recommendations=rec_dicts,
            service_records=service_records,
            language=user_lang
        )

        # Retrieve last 10 messages for multi-turn history context
        history_cursor = self.collection.find({
            "productId": data.productId,
            "userId": user_id
        }).sort("createdAt", DESCENDING).limit(10)

        history_docs = [doc async for doc in history_cursor]
        history_docs.reverse()  # chronological order

        # Format conversation transcript for model
        conversation_history_lines = []
        for h in history_docs:
            speaker = "User" if h["role"] == "user" else "Assistant"
            conversation_history_lines.append(f"{speaker}: {h['content']}")

        # Add current user prompt
        conversation_history_lines.append(f"User: {data.message.strip()}")
        full_user_prompt = "\n\n".join(conversation_history_lines) + "\n\nAssistant:"

        # Persist user message
        user_now = datetime.now(timezone.utc)
        user_doc = {
            "productId": data.productId,
            "userId": user_id,
            "role": "user",
            "content": data.message.strip(),
            "sources": [],
            "createdAt": user_now
        }
        u_res = await self.collection.insert_one(user_doc)
        user_doc["_id"] = u_res.inserted_id

        # Generate local AI response
        ai_res = await ai_service.generate_text(
            prompt=full_user_prompt,
            system_prompt=system_prompt,
            temperature=0.6
        )

        # If Ollama is offline or errored, generate friendly graceful response in user's language
        if ai_res.success and ai_res.response:
            ai_reply_text = ai_res.response
        else:
            ai_reply_text = translation_service.translate_explanation(
                template_key="offline_ai_fallback",
                target_lang=user_lang,
                product_name=product.name,
                purchase_date=product.purchaseDate,
                warranty_count=len(warranties)
            )
        # Identify which sources are relevant to the query based on hierarchy
        cited_sources_str = []
        cited_source_refs = []

        for s in all_sources:
            # Match keywords from title, domain, or details in reply or query
            if (
                any(kw.lower() in ai_reply_text.lower() for kw in s.title.split() if len(kw) > 3)
                or (s.domain and s.domain.lower() in ai_reply_text.lower())
                or (s.sourceType in ["user_document", "official_manufacturer"] and len(cited_source_refs) < 2)
            ):
                cited_sources_str.append(s.title)
                cited_source_refs.append(s.model_dump())

        if not cited_source_refs and all_sources:
            # Fallback to top priority source
            top_s = all_sources[0]
            cited_sources_str = [top_s.title]
            cited_source_refs = [top_s.model_dump()]

        # Persist assistant reply
        assistant_now = datetime.now(timezone.utc)
        assistant_doc = {
            "productId": data.productId,
            "userId": user_id,
            "role": "assistant",
            "content": ai_reply_text,
            "sources": cited_sources_str[:4],
            "sourceReferences": cited_source_refs[:4],
            "createdAt": assistant_now
        }
        a_res = await self.collection.insert_one(assistant_doc)
        assistant_doc["_id"] = a_res.inserted_id

        return ChatResponse(
            productId=product.id,
            productName=product.name,
            userMessage=format_chat_message(user_doc),
            assistantMessage=format_chat_message(assistant_doc),
            model=ai_res.model,
            durationMs=ai_res.durationMs
        )


chat_service = ChatService()
