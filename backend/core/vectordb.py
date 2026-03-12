"""
Simple keyword-based vector DB replacement.
Uses TF-IDF-style scoring with stdlib only — no ML dependencies.
"""
import os
import json
import math
import re
from typing import List, Dict
from collections import Counter


class MUNVectorDB:
    """Lightweight text search over MUN book content"""

    def __init__(self, persist_directory="./data/chromadb"):
        self.persist_directory = persist_directory
        os.makedirs(persist_directory, exist_ok=True)
        self._index_path = os.path.join(persist_directory, "index.json")
        self._chunks: List[Dict] = []
        self._idf: Dict[str, float] = {}
        self._load()

    # ── persistence ──────────────────────────────────────────────────────────

    def _load(self):
        if os.path.exists(self._index_path):
            with open(self._index_path) as f:
                data = json.load(f)
            self._chunks = data.get("chunks", [])
            self._idf = data.get("idf", {})
            print(f"Loaded existing MUN book collection ({len(self._chunks)} chunks)")
        else:
            print("Created new MUN book collection")

    def _save(self):
        tmp = self._index_path + ".tmp"
        with open(tmp, "w") as f:
            json.dump({"chunks": self._chunks, "idf": self._idf}, f)
        os.replace(tmp, self._index_path)

    # ── tokenisation ─────────────────────────────────────────────────────────

    @staticmethod
    def _tokenize(text: str) -> List[str]:
        return re.findall(r"[a-z]+", text.lower())

    def _build_idf(self):
        N = len(self._chunks)
        if N == 0:
            return
        df: Dict[str, int] = {}
        for chunk in self._chunks:
            for token in set(self._tokenize(chunk["content"])):
                df[token] = df.get(token, 0) + 1
        self._idf = {t: math.log(N / (c + 1)) for t, c in df.items()}

    def _tfidf_score(self, tokens: List[str], chunk: Dict) -> float:
        chunk_tokens = self._tokenize(chunk["content"])
        tf = Counter(chunk_tokens)
        total = len(chunk_tokens) or 1
        return sum(
            (tf[t] / total) * self._idf.get(t, 0)
            for t in tokens
        )

    # ── ingestion ─────────────────────────────────────────────────────────────

    def chunk_text(self, text: str, chunk_size: int = 500, overlap: int = 50) -> List[str]:
        words = text.split()
        chunks = []
        for i in range(0, len(words), chunk_size - overlap):
            chunk = " ".join(words[i:i + chunk_size])
            if chunk:
                chunks.append(chunk)
        return chunks

    def parse_mun_book(self, book_path: str) -> List[Dict]:
        with open(book_path, "r", encoding="utf-8") as f:
            content = f.read()

        sections, section_id = [], 0
        current_section, current_content = "", []

        for line in content.split("\n"):
            line = line.strip()
            if not line:
                continue
            if (line.isupper() and len(line) > 5) or \
               line.startswith("What is") or line.startswith("How to") or \
               line.startswith("Rules of") or \
               line in ["Introduction", "Research 101", "Lobbying", "Foreign Policy",
                        "Documentation", "Voting Procedure", "Attire"]:
                if current_section and current_content:
                    chunks = self.chunk_text("\n".join(current_content), 400, 50)
                    for i, chunk in enumerate(chunks):
                        sections.append({
                            "id": f"section_{section_id}_{i}",
                            "section": current_section,
                            "content": chunk,
                            "metadata": {
                                "section_title": current_section,
                                "chunk_index": i,
                                "total_chunks": len(chunks)
                            }
                        })
                    section_id += 1
                current_section = line
                current_content = []
            else:
                current_content.append(line)

        if current_section and current_content:
            chunks = self.chunk_text("\n".join(current_content), 400, 50)
            for i, chunk in enumerate(chunks):
                sections.append({
                    "id": f"section_{section_id}_{i}",
                    "section": current_section,
                    "content": chunk,
                    "metadata": {"section_title": current_section, "chunk_index": i, "total_chunks": len(chunks)}
                })
        return sections

    def vectorize_book(self, book_path: str):
        print("Parsing MUN book...")
        sections = self.parse_mun_book(book_path)
        print(f"Found {len(sections)} text chunks")
        self._chunks = sections
        self._build_idf()
        self._save()
        print(f"Successfully indexed {len(sections)} chunks from MUN book")

    # ── search ────────────────────────────────────────────────────────────────

    def search(self, query: str, n_results: int = 5) -> List[Dict]:
        if not self._chunks:
            return []
        tokens = self._tokenize(query)
        scored = sorted(
            self._chunks,
            key=lambda c: self._tfidf_score(tokens, c),
            reverse=True
        )
        return [
            {
                "content": c["content"],
                "metadata": c.get("metadata", {}),
                "distance": 0.0
            }
            for c in scored[:n_results]
        ]

    def get_context_for_query(self, query: str, max_context_length: int = 2000) -> str:
        results = self.search(query, n_results=5)
        parts, length = [], 0
        for r in results:
            content = r["content"]
            if length + len(content) > max_context_length:
                break
            section = r["metadata"].get("section_title", "Unknown")
            parts.append(f"[From {section}]\n{content}")
            length += len(content)
        return "\n\n".join(parts)

    # ── ChromaDB compat stubs (used by active_memory.py) ─────────────────────

    def add(self, documents, metadatas=None, ids=None):
        for i, doc in enumerate(documents):
            self._chunks.append({
                "id": ids[i] if ids else str(len(self._chunks)),
                "content": doc,
                "metadata": metadatas[i] if metadatas else {}
            })
        self._build_idf()
        self._save()

    def query(self, query_texts, n_results=5, **kwargs):
        results = self.search(query_texts[0], n_results)
        return {
            "documents": [[r["content"] for r in results]],
            "metadatas": [[r["metadata"] for r in results]],
            "distances": [[r["distance"] for r in results]],
            "ids": [[r["metadata"].get("id", str(i)) for i, r in enumerate(results)]]
        }

    @property
    def collection(self):
        return self


def initialize_vector_db():
    db = MUNVectorDB()
    if db._chunks:
        print("Vector database already initialized")
        return db

    book_path = os.path.join(os.path.dirname(__file__), "..", "..", "MUN Book .txt")
    if not os.path.exists(book_path):
        book_path = os.path.join(os.path.dirname(__file__), "..", "MUN Book .txt")
    if os.path.exists(book_path):
        db.vectorize_book(book_path)
    else:
        print("Warning: MUN Book not found — vector search will be empty")
    return db
