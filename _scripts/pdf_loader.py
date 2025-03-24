import mimetypes
import argparse
import asyncio
import hashlib
import re

import fitz
import httpx
import msgspec

from pathlib import Path
from msgspec import Struct

# Constants
# ---------

RETRIEVVY_URL = "http://0.0.0.0:7300"


# Types
# -----


class Bundle(Struct):
    id: str
    index: str
    source: str
    name: str
    blocks: list[str]


# Note
# --------------------------------------------------------------------------------
# We consider each pdf document to be one bundle. So the mapping is pdf -> bundle.
# Each page of the pdf is a block. So pdf page -> block. So when Retrievvy gives
# us results with references, the references (which are based on blocks) are going
# to refer to specific pdf pages.
# --------------------------------------------------------------------------------


# Text Extractors
# ---------------


async def get_text(path, mimetype: str) -> tuple[str, list[str]]:
    if mimetype == "application/pdf":
        return "application/pdf", _pdf(path)

    raise ValueError("Unable to parse document: Only pdf are supporeted by this script")


def _pdf(path: str) -> list[str]:
    doc = fitz.open(path)
    pages_text = []
    for page_num in range(doc.page_count):
        page = doc.load_page(page_num)
        page_text = join_broken_words(cleanup(page.get_text("text")))
        pages_text.append(page_text.strip())
    doc.close()
    return pages_text


# Helpers
# -------


def file_to_sha256(path):
    h = hashlib.sha256()

    with open(path, "rb") as f:
        while True:
            data = f.read(2048)
            if not data:
                break
            h.update(data)

    return h.hexdigest()


def cleanup(text):
    text = text.replace("\n", " ")
    return re.sub(r"\s+", " ", text)


def join_broken_words(text):
    return re.sub(r"(\w+)- (\w+)", r"\1\2", text)


# File parsing
# ------------


async def read_docs(folder_path: str, index: str) -> list[Bundle]:
    docs = []
    seen_docs = set()
    all_files = Path(folder_path).rglob("*")

    for file_path in all_files:
        # Skip directories
        if file_path.is_dir():
            continue

        mimetype, _ = mimetypes.guess_type(file_path)

        # If mimetype can't be determined, skip this file
        if not mimetype:
            print(f"Could not determine mimetype for {file_path}. Skipping.")
            continue

        # Generate SHA-256 hash as document ID
        doc_id = file_to_sha256(file_path)
        if doc_id in seen_docs:
            print(f"Document {doc_id} already seen. Skipping.")
            continue

        seen_docs.add(doc_id)

        title = file_path.stem
        print(f"Processing file: {file_path}, doc_id: {doc_id}, mimetype: {mimetype}")

        try:
            extracted_mimetype, content_list = await get_text(file_path, mimetype)
            if extracted_mimetype == "error":
                print(f"Failed to process {file_path}")
                continue
        except Exception as e:
            print(f"Error extracting text from {file_path}: {e}")
            continue

        document = Bundle(
            id=doc_id,
            index=index,
            source="pdf_loader",
            name=title,
            blocks=content_list,
        )
        docs.append(document)

    return docs


# Feed documents to Retrievvy
# ---------------------------


async def send_doc(doc: list[Bundle], url: str, token: str | None):
    headers = {}
    if token:
        headers["Authorization"] = f"Bearer {token}"

    doc_encoded = msgspec.json.encode(doc)
    async with httpx.AsyncClient(timeout=None) as client:
        response = await client.post(
            f"{url}/bundle",
            content=doc_encoded,
            headers=headers,
        )
    if response.status_code == 201:
        print("Documents successfully ingested!")
        print(response.json())
    else:
        print(f"Failed to ingest documents. Status code: {response.status_code}")
        print(response.text)


#
# ----- Main function ---------------------------------------------------------


async def main(
    index: str, folder_path: str, send_flag: bool, url: str, token: str | None
):
    documents = await read_docs(folder_path, index)
    if send_flag:
        for i, doc in enumerate(documents, start=1):
            print(f"Sending {i}/{len(documents)} (ID={doc.id})…")
            await send_doc(doc, url, token)
            print("Sent.\n")
    else:
        print_summary(documents)


def print_summary(documents: list[Bundle]):
    print("\nParsed Documents Summary:")
    print("=" * 120)
    ids = [doc.id for doc in documents]
    names = [doc.name for doc in documents]
    snippets = [
        " ".join(doc.blocks[:1]).replace("\n", " ").replace("\r", "")[:50]
        for doc in documents
    ]

    id_w = min(max(len("Document ID"), max(map(len, ids))), 32)
    name_w = min(max(len("Name"), max(map(len, names))), 30)

    header = f"{'Document ID':<{id_w}} | {'Name':<{name_w}} | Content Snippet"
    print(header)
    print("-" * 120)

    for doc_id, name, snippet in zip(ids, names, snippets):
        print(f"{doc_id:<{id_w}} | {name:<{name_w}} | {snippet}")
    print("=" * 120)
    print(f"\nTotal Documents Parsed: {len(documents)}")
    print("To send these documents to the API, use the '--send' flag.")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(prog="uv run pdf_loader.py")
    parser.add_argument("index")
    parser.add_argument("folder_path")
    parser.add_argument("--send", action="store_true")
    parser.add_argument("--url", default=RETRIEVVY_URL, help="Retrievvy base URL")
    parser.add_argument("--token", default=None, help="Optional API bearer token")
    args = parser.parse_args()

    asyncio.run(main(args.index, args.folder_path, args.send, args.url, args.token))
