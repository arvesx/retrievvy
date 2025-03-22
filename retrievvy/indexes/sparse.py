import shutil
from dataclasses import dataclass
from enum import Enum
from typing import Optional

import xapian

from retrievvy.config import DIR_SPARSE


# Type Definitions
# ----------------


@dataclass
class Doc:
    id: int
    content: str


@dataclass
class Hit:
    id: int
    score: float


# Index management
# ----------------


def create(name: str) -> None:
    path = DIR_SPARSE / name
    if path.exists():
        raise FileExistsError(f"Sparse index '{name}' already exists at {path}")

    path.mkdir(parents=True, exist_ok=True)
    db = xapian.WritableDatabase(str(path), xapian.DB_CREATE_OR_OPEN)
    db.close()


def delete(name: str) -> None:
    path = DIR_SPARSE / name
    if path.exists():
        shutil.rmtree(path)


# Document management
# -------------------


def doc_add(idx_name: str, docs: list[Doc], lang: str = "en") -> None:
    path = DIR_SPARSE / idx_name
    db = xapian.WritableDatabase(str(path), xapian.DB_CREATE_OR_OPEN)

    try:
        for doc in docs:
            xap_doc = xapian.Document()
            xap_doc.set_data(str(doc.id))
            term_generator = xapian.TermGenerator()
            if lang.lower() != "none":
                stemmer = xapian.Stem(lang)
                term_generator.set_stemmer(stemmer)

            term_generator.set_document(xap_doc)
            term_generator.index_text(doc.content)

            # Prefix the id to make sure it never conflicts with any terms in the content.
            xap_doc.add_boolean_term(f"Q{doc.id}")
            db.replace_document(f"Q{doc.id}", xap_doc)

        db.commit()
    finally:
        db.close()


def doc_del(idx_name: str, ids: list[int]) -> None:
    path = DIR_SPARSE / idx_name
    db = xapian.WritableDatabase(str(path), xapian.DB_OPEN)
    try:
        for doc_id in ids:
            db.delete_document(f"Q{doc_id}")

        db.commit()
    finally:
        db.close()


# Query
# -----


class QueryOp(Enum):
    OR = xapian.Query.OP_OR
    AND = xapian.Query.OP_AND


def query(
    idx_name: str,
    query: str,
    limit: int = 10,
    filter_ids: Optional[list[int]] = None,
    op: QueryOp = QueryOp.OR,
    lang: str = "en",
) -> list[Hit]:
    path = DIR_SPARSE / idx_name
    db = xapian.Database(str(path))
    try:
        qp = xapian.QueryParser()
        qp.set_default_op(op)

        stemmer = xapian.Stem(lang)
        qp.set_stemmer(stemmer)
        qp.set_stemming_strategy(qp.STEM_SOME)
        parsed_query = qp.parse_query(query)

        if filter_ids is not None:
            filter_queries = [xapian.Query(f"Q{id_}") for id_ in filter_ids]
            filter_query = xapian.Query(xapian.Query.OP_OR, filter_queries)
            parsed_query = xapian.Query(
                xapian.Query.OP_FILTER, parsed_query, filter_query
            )

        enquire = xapian.Enquire(db)
        enquire.set_query(parsed_query)

        mset = enquire.get_mset(0, limit)
        hits: list[Hit] = []

        for match in mset:
            doc_id = int(match.document.get_data())
            score = match.percent
            hits.append(Hit(id=doc_id, score=score / 100))
        return hits

    finally:
        db.close()
