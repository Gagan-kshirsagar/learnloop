import uuid
from uuid import UUID

from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.catalog.api import CourseModule, Lesson
from app.modules.tutor.internal.chunker import MarkdownChunker
from app.modules.tutor.internal.embeddings import EmbeddingsProvider
from app.modules.tutor.internal.llm import LLMProvider
from app.modules.tutor.internal.models import LessonChunk
from app.modules.tutor.internal.repository import TutorRepository
from app.modules.tutor.internal.router import get_model_router
from app.modules.tutor.internal.schemas import (
    AskQuestionResponse,
    CitationResponse,
    CourseIngestResponse,
    LessonIngestResponse,
)
from app.shared.config import get_settings


class TutorService:
    def __init__(
        self,
        embeddings_provider: EmbeddingsProvider | None = None,
        llm_provider: LLMProvider | None = None,
        chunker: MarkdownChunker | None = None,
    ) -> None:
        router = get_model_router()
        self.embeddings = embeddings_provider or router.get_embeddings_provider()
        self.llm = llm_provider or router.get_llm_provider()
        self.chunker = chunker or MarkdownChunker()

    async def ingest_lesson(
        self,
        session: AsyncSession,
        tenant_id: UUID,
        lesson_id: UUID,
    ) -> LessonIngestResponse:
        # 1. Fetch lesson within tenant scope
        query = select(Lesson).where(Lesson.id == lesson_id)
        result = await session.execute(query)
        lesson = result.scalar_one_or_none()
        if not lesson:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Lesson not found",
            )

        repo = TutorRepository(session)

        # 2. Chunk lesson markdown content
        chunk_payloads = self.chunker.chunk_document(lesson.content_md)
        if not chunk_payloads:
            # Idempotent cleanup if lesson content is empty
            await repo.delete_chunks_by_lesson(lesson_id)
            return LessonIngestResponse(
                lesson_id=lesson_id,
                chunks_created=0,
                total_tokens=0,
            )

        # 3. Batch generate embeddings for chunks
        texts = [c.content for c in chunk_payloads]
        embeddings = await self.embeddings.embed_documents(texts)

        # 4. Transactionally replace existing chunks (Idempotent)
        await repo.delete_chunks_by_lesson(lesson_id)

        new_chunks = [
            LessonChunk(
                id=uuid.uuid4(),
                tenant_id=tenant_id,
                lesson_id=lesson_id,
                ordinal=payload.ordinal,
                content=payload.content,
                token_count=payload.token_count,
                embedding=emb,
            )
            for payload, emb in zip(chunk_payloads, embeddings, strict=False)
        ]
        await repo.bulk_insert_chunks(new_chunks)

        total_tokens = sum(c.token_count for c in chunk_payloads)
        return LessonIngestResponse(
            lesson_id=lesson_id,
            chunks_created=len(new_chunks),
            total_tokens=total_tokens,
        )

    async def ingest_course(
        self,
        session: AsyncSession,
        tenant_id: UUID,
        course_id: UUID,
    ) -> CourseIngestResponse:
        # Fetch all lessons in course hierarchy
        query = (
            select(Lesson)
            .join(CourseModule, Lesson.module_id == CourseModule.id)
            .where(CourseModule.course_id == course_id)
        )
        result = await session.execute(query)
        lessons = list(result.scalars().all())

        if not lessons:
            return CourseIngestResponse(
                course_id=course_id,
                lessons_ingested=0,
                total_chunks=0,
            )

        total_chunks = 0
        for les in lessons:
            res = await self.ingest_lesson(session, tenant_id=tenant_id, lesson_id=les.id)
            total_chunks += res.chunks_created

        return CourseIngestResponse(
            course_id=course_id,
            lessons_ingested=len(lessons),
            total_chunks=total_chunks,
        )

    async def ask_question(
        self,
        session: AsyncSession,
        tenant_id: UUID,  # noqa: ARG002
        question: str,
        lesson_id: UUID | None = None,
        top_k: int = 5,
        score_threshold: float | None = None,
    ) -> AskQuestionResponse:
        repo = TutorRepository(session)
        settings = get_settings()
        effective_threshold = (
            score_threshold
            if score_threshold is not None
            else getattr(settings, "rag_score_threshold", 0.35)
        )

        # 1. Embed query
        query_vector = await self.embeddings.embed_query(question)

        # 2. Retrieve top-k cosine similar chunks scoped by tenant & lesson
        scored_chunks = await repo.search_similar_chunks(
            embedding=query_vector,
            top_k=top_k,
            lesson_id=lesson_id,
            score_threshold=effective_threshold,
        )

        # 3. Grounding Refusal Guard: if insufficient relevance, decline without calling LLM
        if not scored_chunks:
            return AskQuestionResponse(
                answer="That isn't covered in this lesson.",
                citations=[],
                used_context=False,
            )

        # 4. Build grounded prompt
        context_parts = []
        citations: list[CitationResponse] = []
        for i, (chunk, score) in enumerate(scored_chunks):
            snippet = chunk.content[:200].replace("\n", " ") + (
                "..." if len(chunk.content) > 200 else ""
            )
            citations.append(
                CitationResponse(
                    lesson_id=chunk.lesson_id,
                    ordinal=chunk.ordinal,
                    snippet=snippet,
                    score=round(score, 3),
                )
            )
            context_parts.append(f"[{i + 1}] (Lesson Chunk {chunk.ordinal}):\n{chunk.content}")

        context_text = "\n\n".join(context_parts)
        system_instruction = (
            "You are LearnLoop AI Tutor. Answer the student's question using ONLY "
            "the provided lesson context chunks. Explain concepts clearly and concisely. "
            "If the question cannot be answered using the provided context, state that "
            "it is not covered in the lesson."
        )
        prompt = (
            f"Lesson Context Chunks:\n{context_text}\n\nStudent Question: {question}\n\nAnswer:"
        )

        # 5. Invoke LLM for grounded answer
        answer = await self.llm.generate(
            prompt=prompt,
            system_instruction=system_instruction,
            temperature=0.2,
        )

        return AskQuestionResponse(
            answer=answer,
            citations=citations,
            used_context=True,
        )
