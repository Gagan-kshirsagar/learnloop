import uuid
from datetime import UTC, datetime
from typing import Any
from uuid import UUID

from sqlalchemy import delete, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.tutor.internal.models import ChatMessage, ChatSession, LessonChunk


class TutorRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    # ── Chunk Data Access ──

    async def delete_chunks_by_lesson(self, lesson_id: UUID) -> int:
        stmt = delete(LessonChunk).where(LessonChunk.lesson_id == lesson_id)
        result = await self.session.execute(stmt)
        count = getattr(result, "rowcount", 0)
        return int(count) if count is not None else 0

    async def bulk_insert_chunks(self, chunks: list[LessonChunk]) -> None:
        self.session.add_all(chunks)
        await self.session.flush()

    async def search_similar_chunks(
        self,
        embedding: list[float],
        top_k: int = 5,
        lesson_id: UUID | None = None,
        score_threshold: float = 0.05,
    ) -> list[tuple[LessonChunk, float]]:
        dist_expr = LessonChunk.embedding.cosine_distance(embedding)
        score_expr = (1.0 - dist_expr).label("score")

        query = select(LessonChunk, score_expr)
        if lesson_id is not None:
            query = query.where(LessonChunk.lesson_id == lesson_id)

        query = query.order_by(dist_expr.asc()).limit(top_k)

        result = await self.session.execute(query)
        rows = result.all()

        scored_chunks: list[tuple[LessonChunk, float]] = []
        for chunk, score in rows:
            float_score = float(score)
            if score_threshold <= 0.0 or float_score >= score_threshold:
                scored_chunks.append((chunk, float_score))

        return scored_chunks

    # ── Chat Session Data Access ──

    async def create_session(
        self,
        tenant_id: UUID,
        user_id: UUID,
        title: str,
        lesson_id: UUID | None = None,
    ) -> ChatSession:
        chat_session = ChatSession(
            id=uuid.uuid4(),
            tenant_id=tenant_id,
            user_id=user_id,
            lesson_id=lesson_id,
            title=title,
            created_at=datetime.now(UTC),
            updated_at=datetime.now(UTC),
        )
        self.session.add(chat_session)
        await self.session.flush()
        return chat_session

    async def get_session(self, session_id: UUID) -> ChatSession | None:
        query = select(ChatSession).where(ChatSession.id == session_id)
        result = await self.session.execute(query)
        return result.scalar_one_or_none()

    async def list_user_sessions(
        self,
        user_id: UUID,
        lesson_id: UUID | None = None,
        limit: int = 50,
    ) -> list[ChatSession]:
        query = (
            select(ChatSession)
            .where(ChatSession.user_id == user_id)
            .order_by(ChatSession.updated_at.desc())
            .limit(limit)
        )
        if lesson_id is not None:
            query = query.where(ChatSession.lesson_id == lesson_id)

        result = await self.session.execute(query)
        return list(result.scalars().all())

    async def delete_session(self, session_id: UUID) -> int:
        stmt = delete(ChatSession).where(ChatSession.id == session_id)
        result = await self.session.execute(stmt)
        count = getattr(result, "rowcount", 0)
        return int(count) if count is not None else 0

    async def touch_session(self, session_id: UUID) -> None:
        stmt = (
            update(ChatSession)
            .where(ChatSession.id == session_id)
            .values(updated_at=datetime.now(UTC))
        )
        await self.session.execute(stmt)

    # ── Chat Message Data Access ──

    async def save_message(
        self,
        tenant_id: UUID,
        session_id: UUID,
        role: str,
        content: str,
        citations: list[dict[str, Any]] | None = None,
    ) -> ChatMessage:
        msg = ChatMessage(
            id=uuid.uuid4(),
            tenant_id=tenant_id,
            session_id=session_id,
            role=role,
            content=content,
            citations=citations,
            created_at=datetime.now(UTC),
        )
        self.session.add(msg)
        await self.session.flush()
        return msg

    async def get_session_messages(
        self,
        session_id: UUID,
        limit: int = 50,
    ) -> list[ChatMessage]:
        query = (
            select(ChatMessage)
            .where(ChatMessage.session_id == session_id)
            .order_by(ChatMessage.created_at.asc())
            .limit(limit)
        )
        result = await self.session.execute(query)
        return list(result.scalars().all())

    async def get_recent_messages(
        self,
        session_id: UUID,
        limit: int = 8,
    ) -> list[ChatMessage]:
        """Fetch latest N messages in chronological order for prompt memory context."""
        query = (
            select(ChatMessage)
            .where(ChatMessage.session_id == session_id)
            .order_by(ChatMessage.created_at.desc())
            .limit(limit)
        )
        result = await self.session.execute(query)
        recent_desc = list(result.scalars().all())
        return list(reversed(recent_desc))
