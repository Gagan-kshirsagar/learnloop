import re
from dataclasses import dataclass


@dataclass
class ChunkPayload:
    ordinal: int
    content: str
    token_count: int


def estimate_token_count(text: str) -> int:
    """Estimate token count based on whitespace and punctuation tokens."""
    # Approximate 1 token ~= 4 chars or 0.75 words
    words = re.findall(r"\w+|[^\w\s]", text, re.UNICODE)
    return max(1, int(len(words) * 1.1)) if text.strip() else 0


class MarkdownChunker:
    def __init__(self, target_tokens: int = 500, overlap_tokens: int = 60) -> None:
        self.target_tokens = target_tokens
        self.overlap_tokens = overlap_tokens

    def chunk_document(self, text: str) -> list[ChunkPayload]:
        clean_text = text.strip()
        if not clean_text:
            return []

        total_est = estimate_token_count(clean_text)
        if total_est <= self.target_tokens:
            return [
                ChunkPayload(
                    ordinal=0,
                    content=clean_text,
                    token_count=total_est,
                )
            ]

        # Split on markdown paragraph blocks first
        paragraphs = re.split(r"(\n\s*\n+)", clean_text)
        blocks: list[str] = []
        for p in paragraphs:
            if p.strip():
                blocks.append(p.strip())

        chunks: list[ChunkPayload] = []
        current_block: list[str] = []
        current_tokens = 0
        ordinal = 0

        for block in blocks:
            block_tokens = estimate_token_count(block)

            # If single block exceeds target, split it by lines or sentences
            if block_tokens > self.target_tokens:
                lines = [ln.strip() for ln in block.splitlines() if ln.strip()]
                for line in lines:
                    line_tokens = estimate_token_count(line)
                    if current_tokens + line_tokens > self.target_tokens and current_block:
                        chunk_text = "\n\n".join(current_block)
                        chunks.append(
                            ChunkPayload(
                                ordinal=ordinal,
                                content=chunk_text,
                                token_count=current_tokens,
                            )
                        )
                        ordinal += 1

                        # Carry over overlap
                        current_block = self._compute_overlap(current_block)
                        current_tokens = sum(estimate_token_count(b) for b in current_block)

                    current_block.append(line)
                    current_tokens += line_tokens
                continue

            if current_tokens + block_tokens > self.target_tokens and current_block:
                chunk_text = "\n\n".join(current_block)
                chunks.append(
                    ChunkPayload(
                        ordinal=ordinal,
                        content=chunk_text,
                        token_count=current_tokens,
                    )
                )
                ordinal += 1

                # Carry over overlap blocks
                current_block = self._compute_overlap(current_block)
                current_tokens = sum(estimate_token_count(b) for b in current_block)

            current_block.append(block)
            current_tokens += block_tokens

        if current_block:
            chunk_text = "\n\n".join(current_block)
            chunks.append(
                ChunkPayload(
                    ordinal=ordinal,
                    content=chunk_text,
                    token_count=current_tokens,
                )
            )

        return chunks

    def _compute_overlap(self, blocks: list[str]) -> list[str]:
        """Keep the trailing blocks whose token count is within overlap_tokens."""
        overlap: list[str] = []
        acc = 0
        for b in reversed(blocks):
            cnt = estimate_token_count(b)
            if acc + cnt <= self.overlap_tokens or not overlap:
                overlap.insert(0, b)
                acc += cnt
            else:
                break
        return overlap
