import logging
from datetime import datetime, timezone
from typing import List, Dict, Any, Optional
from bson import ObjectId
from pymongo import ASCENDING, DESCENDING
from app.core.database import db_manager
from app.core.exceptions import NotFoundException
from app.schemas.ai import (
    AIConversationResponse,
    AIMessageResponse,
    AIAction
)
from app.schemas.sources import SourceReference

logger = logging.getLogger("ownit.services.ai.conversations")


def format_conversation_doc(doc: Dict[str, Any], message_count: int = 0) -> AIConversationResponse:
    return AIConversationResponse(
        id=str(doc["_id"]),
        userId=doc["userId"],
        contextType=doc.get("contextType", "global"),
        productId=doc.get("productId"),
        productName=doc.get("productName"),
        title=doc.get("title", "Conversation"),
        createdAt=doc.get("createdAt", datetime.now(timezone.utc)),
        updatedAt=doc.get("updatedAt", datetime.now(timezone.utc)),
        lastMessage=doc.get("lastMessage"),
        messageCount=message_count
    )


def format_message_doc(doc: Dict[str, Any]) -> AIMessageResponse:
    raw_refs = doc.get("sourceReferences", [])
    parsed_refs = []
    for r in raw_refs:
        if isinstance(r, dict):
            try:
                parsed_refs.append(SourceReference(**r))
            except Exception:
                pass
        elif isinstance(r, SourceReference):
            parsed_refs.append(r)

    raw_actions = doc.get("actions", [])
    parsed_actions = []
    for a in raw_actions:
        if isinstance(a, dict):
            try:
                parsed_actions.append(AIAction(**a))
            except Exception:
                pass
        elif isinstance(a, AIAction):
            parsed_actions.append(a)

    return AIMessageResponse(
        id=str(doc["_id"]),
        conversationId=str(doc.get("conversationId", "")),
        role=doc["role"],
        content=doc["content"],
        sources=doc.get("sources", []),
        sourceReferences=parsed_refs,
        actions=parsed_actions,
        createdAt=doc.get("createdAt", datetime.now(timezone.utc)),
        model=doc.get("model"),
        durationMs=doc.get("durationMs")
    )


class ConversationService:
    """
    Manages multi-turn conversation threads and message persistence in MongoDB.
    """

    @property
    def conversations_collection(self):
        return db_manager.get_collection("ai_conversations")

    @property
    def messages_collection(self):
        return db_manager.get_collection("ai_messages")

    async def ensure_indexes(self):
        try:
            conv_col = self.conversations_collection
            if conv_col is not None:
                await conv_col.create_index([("userId", ASCENDING), ("updatedAt", DESCENDING)], name="idx_ai_conv_user_updated")
                await conv_col.create_index([("productId", ASCENDING), ("userId", ASCENDING)], name="idx_ai_conv_prod_user")

            msg_col = self.messages_collection
            if msg_col is not None:
                await msg_col.create_index([("conversationId", ASCENDING), ("createdAt", ASCENDING)], name="idx_ai_msg_conv_created")
                await msg_col.create_index([("userId", ASCENDING)], name="idx_ai_msg_user")
            logger.info("AI conversations indexes ensured.")
        except Exception as e:
            logger.warning("Could not create AI conversation indexes: %s", e)

    async def create_conversation(
        self,
        user_id: str,
        context_type: str = "global",
        product_id: Optional[str] = None,
        product_name: Optional[str] = None,
        title: Optional[str] = None
    ) -> Dict[str, Any]:
        now = datetime.now(timezone.utc)
        if not title:
            if context_type == "product" and product_name:
                title = f"{product_name} Chat"
            else:
                title = "Global OWNIT Assistant"

        conv_doc = {
            "userId": user_id,
            "contextType": context_type,
            "productId": product_id,
            "productName": product_name,
            "title": title,
            "createdAt": now,
            "updatedAt": now,
            "lastMessage": None
        }

        res = await self.conversations_collection.insert_one(conv_doc)
        conv_doc["_id"] = res.inserted_id
        return conv_doc

    async def list_conversations(self, user_id: str) -> List[Dict[str, Any]]:
        cursor = self.conversations_collection.find({"userId": user_id}).sort("updatedAt", DESCENDING)
        convs = [c async for c in cursor]
        return convs

    async def get_conversation(self, conversation_id: str, user_id: str) -> Dict[str, Any]:
        try:
            oid = ObjectId(conversation_id)
        except Exception:
            oid = None

        query = {"$or": [{"_id": oid}, {"_id": conversation_id}], "userId": user_id} if oid else {"_id": conversation_id, "userId": user_id}
        conv = await self.conversations_collection.find_one(query)
        if not conv:
            raise NotFoundException("AI Conversation", conversation_id)
        return conv

    async def delete_conversation(self, conversation_id: str, user_id: str) -> bool:
        conv = await self.get_conversation(conversation_id, user_id)
        c_id = str(conv["_id"])

        # Delete conversation
        await self.conversations_collection.delete_one({"_id": conv["_id"], "userId": user_id})

        # Delete all messages in thread
        await self.messages_collection.delete_many({"conversationId": c_id, "userId": user_id})
        return True

    async def add_message(
        self,
        conversation_id: str,
        user_id: str,
        role: str,
        content: str,
        sources: Optional[List[str]] = None,
        source_references: Optional[List[Dict[str, Any]]] = None,
        actions: Optional[List[Dict[str, Any]]] = None,
        model: Optional[str] = None,
        duration_ms: Optional[float] = None
    ) -> Dict[str, Any]:
        now = datetime.now(timezone.utc)
        msg_doc = {
            "conversationId": conversation_id,
            "userId": user_id,
            "role": role,
            "content": content,
            "sources": sources or [],
            "sourceReferences": source_references or [],
            "actions": actions or [],
            "model": model,
            "durationMs": duration_ms,
            "createdAt": now
        }

        res = await self.messages_collection.insert_one(msg_doc)
        msg_doc["_id"] = res.inserted_id

        # Update conversation lastMessage & updatedAt
        try:
            oid = ObjectId(conversation_id)
        except Exception:
            oid = None

        q = {"$or": [{"_id": oid}, {"_id": conversation_id}], "userId": user_id} if oid else {"_id": conversation_id, "userId": user_id}
        await self.conversations_collection.update_one(
            q,
            {"$set": {"updatedAt": now, "lastMessage": content[:120]}}
        )

        return msg_doc

    async def get_messages(self, conversation_id: str, user_id: str, limit: int = 50) -> List[Dict[str, Any]]:
        cursor = self.messages_collection.find({
            "conversationId": conversation_id,
            "userId": user_id
        }).sort("createdAt", ASCENDING).limit(limit)

        messages = [m async for m in cursor]
        return messages


conversation_service = ConversationService()
