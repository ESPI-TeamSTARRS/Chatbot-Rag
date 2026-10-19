import re
from dataclasses import dataclass
from pathlib import Path

import snowballstemmer
from rank_bm25 import BM25Okapi

from chatbot_rag.domain import SearchHit
from chatbot_rag.ports import DocSearchPort

EXCLUDED_DIR = "actions-taken"
EXTENSIONS = frozenset({".md", ".txt"})
STOP_WORDS = frozenset(
    "a an and are as at be but by for from has have if in into is it its of on or "
    "that the their then there these they this to was were will with".split()
)


class Tokenizer:
    """Lowercases, drops stop words and stems, so that 'timed' and 'timeout' share a root."""

    def __init__(self):
        self._stemmer = snowballstemmer.stemmer("english")

    def tokenize(self, text: str) -> list[str]:
        words = re.findall(r"[a-z0-9]+", text.lower())
        return self._stemmer.stemWords([word for word in words if word not in STOP_WORDS])


@dataclass(frozen=True)
class Document:
    path: str
    text: str


class DocLoader:
    """Reads the documentation folder: one Document per file."""

    def __init__(self, docs_path: Path, excluded_dir: str = EXCLUDED_DIR):
        self._docs_path = docs_path
        self._excluded_dir = excluded_dir

    def fingerprint(self) -> tuple:
        """Cheap summary of the indexable files; it changes whenever the documentation does."""
        return tuple(
            (file.as_posix(), file.stat().st_mtime_ns, file.stat().st_size)
            for file in self._indexable_files()
        )

    def load(self) -> list[Document]:
        documents = []
        for file in self._indexable_files():
            text = file.read_text(encoding="utf-8").strip()
            if text:
                documents.append(Document(file.relative_to(self._docs_path).as_posix(), text))
        return documents

    def _indexable_files(self) -> list[Path]:
        return [file for file in sorted(self._docs_path.rglob("*")) if self._is_indexable(file)]

    def _is_indexable(self, file: Path) -> bool:
        relative = file.relative_to(self._docs_path)
        return (
            file.is_file()
            and file.suffix in EXTENSIONS
            and self._excluded_dir not in relative.parts
        )


class Bm25DocSearch(DocSearchPort):
    """Keyword search (BM25) ranking whole documents; the index follows the files on disk."""

    def __init__(self, docs_path: Path, excluded_dir: str = EXCLUDED_DIR):
        self._tokenizer = Tokenizer()
        self._loader = DocLoader(docs_path, excluded_dir)
        self._fingerprint: tuple | None = None
        self._refresh_index()

    def search(self, query: str, limit: int) -> list[SearchHit]:
        self._refresh_index()
        query_tokens = self._tokenizer.tokenize(query)
        if self._bm25 is None or not query_tokens:
            return []
        scores = self._bm25.get_scores(query_tokens)
        matching = self._documents_sharing_a_word_with(query_tokens)
        best_first = sorted(matching, key=lambda index: scores[index], reverse=True)
        return [self._to_hit(index, scores[index]) for index in best_first[:limit]]

    def _refresh_index(self) -> None:
        """Rebuild the index when a document was added, edited or removed since the last build."""
        fingerprint = self._loader.fingerprint()
        if fingerprint == self._fingerprint:
            return
        self._documents = self._loader.load()
        self._document_tokens = [
            self._tokenizer.tokenize(document.text) for document in self._documents
        ]
        self._bm25 = BM25Okapi(self._document_tokens) if self._document_tokens else None
        self._fingerprint = fingerprint

    def _documents_sharing_a_word_with(self, query_tokens: list[str]) -> list[int]:
        wanted = set(query_tokens)
        return [i for i, tokens in enumerate(self._document_tokens) if wanted & set(tokens)]

    def _to_hit(self, index: int, score: float) -> SearchHit:
        document = self._documents[index]
        return SearchHit(document.path, document.text, float(score))
