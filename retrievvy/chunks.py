from typing import Literal
from chonkie import RecursiveChunker, RecursiveRules
import tiktoken

# Tokenizer
# ---------

enc = tiktoken.get_encoding("cl100k_base")


# Chunking
# --------


def get(text: str, chunker: Literal["recursive"], chunk_size: int) -> list[str]:
    match chunker:
        case "recursive":
            chonker = RecursiveChunker(
                tokenizer_or_token_counter=enc,
                chunk_size=chunk_size,
                rules=RecursiveRules(),
                min_characters_per_chunk=12,
                return_type="texts",
            )

            chunks = chonker.chunk(text)
            return [chunk.text for chunk in chunks]
        case _:
            raise ValueError(f"Unknown chunker type: {chunker}")
