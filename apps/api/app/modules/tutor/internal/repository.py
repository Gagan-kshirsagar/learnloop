from uuid import UUID

from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.tutor.internal.models import LessonChunk


class TutorRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

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
        score_threshold: float = 0.65,
    ) -> list[tuple[LessonChunk, float]]:
        # Cosine distance operator (<=>): 0 is identical, 2 is opposite
        # Cosine similarity score = 1.0 - cosine_distance
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
            if float_score >= score_threshold:
                scored_chunks.append((chunk, float_score))

        return scored_chunks
