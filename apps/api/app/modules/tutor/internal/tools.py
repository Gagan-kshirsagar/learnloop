from typing import Any
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.learning.api import (
    check_code_safely,
    get_exercise_for_tutor,
    get_latest_submission_for_tutor,
    get_progress_for_tutor,
    get_submission_for_tutor,
)
from app.modules.tutor.internal.embeddings import EmbeddingsProvider
from app.modules.tutor.internal.repository import TutorRepository
from app.modules.tutor.internal.router import get_model_router


class TutorTools:
    """Read-only tools for Socratic Tutor agent reasoning and context gathering."""

    def __init__(
        self,
        session: AsyncSession,
        tenant_id: UUID,
        user_id: UUID,
        embeddings_provider: EmbeddingsProvider | None = None,
    ) -> None:
        self.session = session
        self.tenant_id = tenant_id
        self.user_id = user_id
        self.embeddings = embeddings_provider or get_model_router().get_embeddings_provider()

    async def retrieve_lesson(
        self,
        query: str,
        lesson_id: UUID | None = None,
        score_threshold: float = 0.04,
    ) -> list[dict[str, Any]]:
        """Search lesson chunks in vector store using cosine similarity."""
        repo = TutorRepository(self.session)
        query_vec = await self.embeddings.embed_query(query)
        scored = await repo.search_similar_chunks(
            embedding=query_vec,
            top_k=3,
            lesson_id=lesson_id,
            score_threshold=score_threshold,
        )
        return [
            {
                "lesson_id": str(ch.lesson_id),
                "ordinal": ch.ordinal,
                "snippet": ch.content[:350].replace("\n", " ")
                + ("..." if len(ch.content) > 350 else ""),
                "score": round(sc, 3),
            }
            for ch, sc in scored
        ]

    async def read_submission(
        self,
        exercise_id: UUID | None = None,
        submission_id: UUID | None = None,
    ) -> dict[str, Any]:
        """Read the learner's latest code submission and test execution failure output."""
        if submission_id:
            sub = await get_submission_for_tutor(self.session, submission_id)
        else:
            sub = await get_latest_submission_for_tutor(
                self.session, user_id=self.user_id, exercise_id=exercise_id
            )

        if not sub:
            return {"status": "none", "message": "No submissions found for this exercise"}

        return {
            "status": sub.status,
            "code": sub.code[:600] if sub.code else "",
            "tests_passed": sub.tests_passed,
            "tests_total": sub.tests_total,
            "stderr": sub.stderr[:300] if sub.stderr else "",
            "stdout": sub.stdout[:200] if sub.stdout else "",
        }

    async def get_exercise(self, exercise_id: UUID) -> dict[str, Any]:
        """Read the exercise prompt and starter code. Hidden tests_code is never exposed."""
        ex = await get_exercise_for_tutor(self.session, exercise_id)
        if not ex:
            return {"error": "Exercise not found"}
        return {
            "exercise_id": str(ex.id),
            "prompt_md": ex.prompt_md[:400] if ex.prompt_md else "",
            "starter_code": ex.starter_code or "",
            "language": ex.language,
        }

    async def check_code(self, exercise_id: UUID, code: str) -> dict[str, Any]:
        """Safely test candidate learner code in a sandboxed subprocess."""
        return await check_code_safely(
            session=self.session,
            exercise_id=exercise_id,
            student_code=code,
        )

    async def get_progress(
        self,
        lesson_id: UUID | None = None,
        exercise_id: UUID | None = None,
    ) -> dict[str, Any]:
        """Retrieve attempt count and completion status for adaptivity."""
        return await get_progress_for_tutor(
            session=self.session,
            user_id=self.user_id,
            lesson_id=lesson_id,
            exercise_id=exercise_id,
        )
