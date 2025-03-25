# Retrievvy

Retrievvy is a **hybrid retrieval system** that blends modern embedding similarity search with classic textual search methods, designed explicitly for speed, efficiency, and reliability.

---

## 🚀 Philosophy

The core philosophy behind Retrievvy is straightforward:

- **Speed First:** Lightweight libraries and methods that ensure quick retrieval.
- **Reliability:** Proven, classic methods combined with modern embeddings.
- **Minimal Footprint:** Tools selected for minimal resource usage without sacrificing quality.

You can effortlessly switch to heavier embedding models, but the default setup prioritizes practical, everyday efficiency.

---

## 🧩 Basic Concepts

### Bundles

- A **bundle** is the fundamental unit of indexing in Retrievvy. Think of it as an individual document or a complete piece of content you want to index.
- Each bundle is uniquely identified and processed independently.

### Blocks

- Every bundle is composed of multiple **blocks**, which represent logical partitions of the original content (e.g., pages of a PDF, sections of a document).
- Blocks are the base unit for indexing and retrieval references.
- Retrievvy internally combines these blocks into larger chunks for optimized indexing and retrieval, but references provided in search results always link back to specific blocks.

#### Example:

If you're indexing PDF documents:

- Each PDF file becomes a single bundle.
- Each page within the PDF becomes a block.
- Search results reference these specific blocks (pages), providing precise navigation.

### Example: Indexing a Bundle via API

You can easily send bundles to Retrievvy via a straightforward HTTP request:

```bash
curl -X POST http://0.0.0.0:7300/bundle \
     -H "Content-Type: application/json" \
     -d '{
           "id": "unique_bundle_id",
           "index": "my_index",
           "source": "custom_loader",
           "name": "Example Document",
           "blocks": [
             "First block of text content.",
             "Second block of text content.",
             "Third block of text content."
           ]
         }'
```

This sends a bundle to Retrievvy, which then fully processes and indexes the content (both in dense embeddings and sparse textual indexes).

### Example: Searching Information via API

You can search indexed bundles using a simple HTTP GET request:

```bash
curl "http://0.0.0.0:7300/query?q=how%20to%20deploy%20a%20docker%20app&index=my_index&limit=10"
```

- `q`: Your query in natural language.
- `index`: The specific index you wish to search.
- `limit`: The number of search results to retrieve.

---

## 🛠️ What's Inside?

- **Hybrid Retrieval:**
  - **Dense Embeddings:** Fast and lightweight using [FastEmbed](https://github.com/qdrant/fastembed) indexed in [Qdrant](https://qdrant.tech/).
  - **Sparse Textual Search:** Classic, reliable BM25 via [Xapian](https://xapian.org/).

- **Adaptive Fusion Reranking:**
  - Statistically smart evaluation to fuse embedding and textual scores.
  - Dynamic weighting, linear transformations, interaction terms, and normalization for optimized results.

- **Fully Async Design:**
  - Built with [Starlette](https://www.starlette.io/) to ensure rapid, non-blocking responses.
  - Embedding computations run separately, keeping the webserver highly responsive.

- **Optimized Data Handling:**
  - **Database:** SQLite3—perfectly suited for single-writer, multiple-reader use cases.
  - **Serialization & Validation:** High-performance [msgspec](https://github.com/jcrist/msgspec).
  - **NLP Efficiency:** Fast and lightweight [NLTK](https://www.nltk.org/) instead of heavier alternatives.

---

## 📦 Tech Stack

- **Webserver:** Starlette (Async Python)
- **Embeddings:** FastEmbed
- **Vector Database:** Qdrant
- **Text Search:** Xapian BM25
- **Database:** SQLite3
- **Serialization:** msgspec
- **NLP:** NLTK
- **Logging:** loguru
- **Retry Handling:** tenacity
- **Tokenization:** tiktoken
- **Deployment:** Uvicorn
- **Additional Tools:** chonkie, numpy, yake

---

## 🧑‍💻 Quick Start

Clone and launch quickly using Docker:

```bash
git clone https://github.com/arvesx/retrievvy.git
cd retrievvy
docker compose up --build
```

That's it—you're up and running!

---

## 🌟 Contribute

Contributions are always welcome. Please contact me before submitting a PR to ensure alignment and efficiency.
