import json
import uuid
from collections.abc import AsyncIterator
from uuid import UUID

from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.catalog.api import CourseModule, Lesson
from app.modules.tutor.internal.chunker import MarkdownChunker
from app.modules.tutor.internal.embeddings import EmbeddingsProvider
from app.modules.tutor.internal.graph import SocraticTutorAgent, TutorAgentState
from app.modules.tutor.internal.llm import LLMProvider
from app.modules.tutor.internal.models import LessonChunk
from app.modules.tutor.internal.repository import TutorRepository
from app.modules.tutor.internal.router import get_model_router
from app.modules.tutor.internal.schemas import (
    AskQuestionResponse,
    ChatMessageResponse,
    ChatSessionDetailResponse,
    ChatSessionResponse,
    CitationResponse,
    CourseIngestResponse,
    LessonIngestResponse,
    StreamQuestionRequest,
)
from app.modules.tutor.internal.tools import TutorTools
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

    # ── Ingestion Pipeline ──

    async def ingest_lesson(
        self,
        session: AsyncSession,
        tenant_id: UUID,
        lesson_id: UUID,
    ) -> LessonIngestResponse:
        query = select(Lesson).where(Lesson.id == lesson_id)
        result = await session.execute(query)
        lesson = result.scalar_one_or_none()
        if not lesson:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Lesson not found",
            )

        repo = TutorRepository(session)
        chunk_payloads = self.chunker.chunk_document(lesson.content_md)
        if not chunk_payloads:
            await repo.delete_chunks_by_lesson(lesson_id)
            return LessonIngestResponse(
                lesson_id=lesson_id,
                chunks_created=0,
                total_tokens=0,
            )

        texts = [c.content for c in chunk_payloads]
        embeddings = await self.embeddings.embed_documents(texts)

        # Idempotently replace existing chunks
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

    # ── Non-Streaming Q&A (Slice 4 Compatibility) ──

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
            else getattr(settings, "rag_score_threshold", 0.05)
        )

        query_vector = await self.embeddings.embed_query(question)
        scored_chunks = await repo.search_similar_chunks(
            embedding=query_vector,
            top_k=top_k,
            lesson_id=lesson_id,
            score_threshold=effective_threshold,
        )

        if not scored_chunks:
            return AskQuestionResponse(
                answer="That isn't covered in this lesson.",
                citations=[],
                used_context=False,
            )

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

    # ── Socratic LangGraph ReAct Agent Streaming (Slice 6) ──

    async def stream_question(
        self,
        session: AsyncSession,
        tenant_id: UUID,
        user_id: UUID,
        req: StreamQuestionRequest,
    ) -> AsyncIterator[str]:
        repo = TutorRepository(session)

        # 1. Resolve or create chat session
        if req.session_id:
            chat_session = await repo.get_session(req.session_id)
            if not chat_session:
                yield f"event: error\ndata: {json.dumps({'message': 'Chat session not found'})}\n\n"
                return
            if chat_session.user_id != user_id:
                err_payload = json.dumps({"message": "Access forbidden to session"})
                yield f"event: error\ndata: {err_payload}\n\n"
                return
            active_session_id = chat_session.id
        else:
            title = req.question.strip()[:50] + ("..." if len(req.question.strip()) > 50 else "")
            chat_session = await repo.create_session(
                tenant_id=tenant_id,
                user_id=user_id,
                title=title,
                lesson_id=req.lesson_id,
            )
            active_session_id = chat_session.id

        # 2. Fetch prior conversation turns for prompt memory
        recent_history = await repo.get_recent_messages(active_session_id, limit=8)
        prior_messages = [{"role": m.role, "content": m.content} for m in recent_history]

        # 3. Persist incoming user message
        await repo.save_message(
            tenant_id=tenant_id,
            session_id=active_session_id,
            role="user",
            content=req.question.strip(),
        )
        await repo.touch_session(active_session_id)
        await session.flush()

        # 4. Instantiate Socratic Agent and execute graph
        tools = TutorTools(
            session=session,
            tenant_id=tenant_id,
            user_id=user_id,
            embeddings_provider=self.embeddings,
        )

        progress_info = await tools.get_progress(
            lesson_id=req.lesson_id, exercise_id=req.exercise_id
        )
        attempt_count = progress_info.get("attempts", 0)

        agent_state = TutorAgentState(
            question=req.question.strip(),
            user_id=user_id,
            tenant_id=tenant_id,
            session_id=active_session_id,
            lesson_id=req.lesson_id,
            exercise_id=req.exercise_id,
            submission_id=req.submission_id,
            attempt_count=attempt_count,
            prior_messages=prior_messages,
        )

        agent = SocraticTutorAgent(
            tools=tools,
            llm=self.llm,
            max_iterations=4,
        )

        try:
            async for sse_chunk in agent.execute_stream(agent_state):
                yield sse_chunk

            # 5. Persist complete assistant response and citations
            final_text = (
                agent_state.final_answer
                if agent_state.final_answer
                else (
                    "That isn't covered in this lesson."
                    if agent_state.is_out_of_scope
                    else "I couldn't find a solution for that."
                )
            )

            asst_msg = await repo.save_message(
                tenant_id=tenant_id,
                session_id=active_session_id,
                role="assistant",
                content=final_text,
                citations=agent_state.citations,
            )
            await session.flush()

            # 6. Emit done event
            done_event = json.dumps(
                {
                    "session_id": str(active_session_id),
                    "message_id": str(asst_msg.id),
                }
            )
            yield f"event: done\ndata: {done_event}\n\n"

        except Exception as exc:
            yield f"event: error\ndata: {json.dumps({'message': str(exc)})}\n\n"

    # ── Session Management Endpoints ──

    async def list_sessions(
        self,
        session: AsyncSession,
        user_id: UUID,
        lesson_id: UUID | None = None,
    ) -> list[ChatSessionResponse]:
        repo = TutorRepository(session)
        sessions = await repo.list_user_sessions(user_id=user_id, lesson_id=lesson_id)
        return [
            ChatSessionResponse(
                id=s.id,
                lesson_id=s.lesson_id,
                title=s.title,
                created_at=s.created_at,
                updated_at=s.updated_at,
            )
            for s in sessions
        ]

    async def get_session_detail(
        self,
        session: AsyncSession,
        user_id: UUID,
        session_id: UUID,
    ) -> ChatSessionDetailResponse:
        repo = TutorRepository(session)
        chat_session = await repo.get_session(session_id)
        if not chat_session:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Chat session not found",
            )
        if chat_session.user_id != user_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access forbidden to this session",
            )

        messages = await repo.get_session_messages(session_id)
        msg_responses = []
        for m in messages:
            citations_obj = None
            if m.citations:
                citations_obj = [
                    CitationResponse(
                        lesson_id=UUID(c["lesson_id"])
                        if isinstance(c["lesson_id"], str)
                        else c["lesson_id"],
                        ordinal=c["ordinal"],
                        snippet=c["snippet"],
                        score=c["score"],
                    )
                    for c in m.citations
                ]
            msg_responses.append(
                ChatMessageResponse(
                    id=m.id,
                    role=m.role,
                    content=m.content,
                    citations=citations_obj,
                    created_at=m.created_at,
                )
            )

        return ChatSessionDetailResponse(
            session=ChatSessionResponse(
                id=chat_session.id,
                lesson_id=chat_session.lesson_id,
                title=chat_session.title,
                created_at=chat_session.created_at,
                updated_at=chat_session.updated_at,
            ),
            messages=msg_responses,
        )

    async def delete_session(
        self,
        session: AsyncSession,
        user_id: UUID,
        session_id: UUID,
    ) -> None:
        repo = TutorRepository(session)
        chat_session = await repo.get_session(session_id)
        if not chat_session:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Chat session not found",
            )
        if chat_session.user_id != user_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access forbidden to this session",
            )
        await repo.delete_session(session_id)
        await session.flush()
