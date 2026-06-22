from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import re
from typing import Any

BASE_DIR = Path(__file__).resolve().parents[2]
DOC_DIR = BASE_DIR / "data" / "docs"


@dataclass
class Chunk:
    title: str
    source_type: str
    path: str
    content: str


def _normalize(text: str) -> list[str]:
    tokens = re.findall(r"[A-Za-z0-9가-힣_.:/-]+", text.lower())
    stop = {"the", "a", "an", "and", "or", "to", "is", "는", "은", "이", "가", "을", "를", "및"}
    return [t for t in tokens if t not in stop and len(t) > 1]


class RagService:
    def __init__(self) -> None:
        self.chunks = self._load_chunks()

    def _load_chunks(self) -> list[Chunk]:
        chunks: list[Chunk] = []
        for path in sorted(DOC_DIR.glob("*.md")):
            text = path.read_text(encoding="utf-8")
            title = text.splitlines()[0].lstrip("# ").strip() if text.splitlines() else path.stem
            parts = [p.strip() for p in re.split(r"\n## ", text) if p.strip()]
            for index, part in enumerate(parts):
                chunks.append(Chunk(title=title, source_type="rag-document", path=path.name, content=part[:2500]))
        return chunks

    def search(self, query: str, top_k: int = 5) -> list[dict[str, Any]]:
        q_tokens = set(_normalize(query))
        scored: list[tuple[float, Chunk]] = []
        for chunk in self.chunks:
            c_tokens = set(_normalize(chunk.content + " " + chunk.title + " " + chunk.path))
            lexical_overlap = len(q_tokens & c_tokens)
            boost = 0
            lower = (chunk.content + chunk.title).lower()
            for keyword in ["502", "tomcat", "hikaripool", "connection", "upstream", "nginx", "timeout", "was", "db"]:
                if keyword in query.lower() and keyword in lower:
                    boost += 2
            score = lexical_overlap + boost
            if score > 0:
                scored.append((score, chunk))
        scored.sort(key=lambda x: x[0], reverse=True)
        return [
            {
                "title": chunk.title,
                "source_type": chunk.source_type,
                "path": chunk.path,
                "score": round(float(score), 3),
                "content": chunk.content[:700],
            }
            for score, chunk in scored[:top_k]
        ]


rag_service = RagService()
