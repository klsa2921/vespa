# Celebrity News Schema

This document describes the `celebrity_news` schema, designed for storing and searching celebrity-related news articles. The schema supports both traditional text-based search (using BM25 ranking) and semantic search (using embeddings), with hybrid options for combining both approaches.

## Schema Structure

### Document Definition
- **Type**: `celebrity_news`
- **Fields**:
  - **`id`** (string)
    - Unique identifier for each news article.
    - Indexing: `summary | attribute`
    - Matching: `exact`
  - **`title`** (string)
    - Title of the news article.
    - Indexing: `summary | index`
  - **`content`** (string)
    - Main body of the news article.
    - Indexing: `summary | index`
    - Ranking: `enable-bm25` (enables BM25 scoring for text search)
  - **`embedding`** (tensor<float>(d0[384]))
    - 384-dimensional vector representing the semantic embedding of the article.
    - Indexing: `attribute`
    - Distance Metric: `euclidean` (used for semantic similarity calculations)

### Fieldset
- **`default`**
  - Groups fields `id`, `title`, and `content` for default querying.

### Rank Profiles
The schema provides three ranking profiles to support different search use cases:

1. **`default`**
   - **First Phase**: `bm25(title) + bm25(content)`
   - A text-based ranking using BM25 scores on the `title` and `content` fields.
   - Suitable for keyword-based searches.

2. **`semantic`** (inherits `default`)
   - **Inputs**: `query(query_embedding)` (tensor<float>(d0[384]))
   - **First Phase**: `closeness(embedding)`
     - Ranks documents based on the Euclidean distance between the query embedding and document embedding.
   - **Second Phase**: `bm25(title) + bm25(content) + 10 * closeness(embedding)`
     - Combines BM25 text scoring with semantic similarity (weighted 10x for embeddings).
   - Ideal for semantic search with some text relevance.

3. **`hybrid`**
   - **Inputs**: `query(query_embedding)` (tensor<float>(d0[384]))
   - **First Phase**: `bm25(title) + bm25(content) + closeness(embedding)`
     - Combines text and semantic scoring in the initial ranking.
   - **Second Phase**: `2 * bm25(title) + 2 * bm25(content) + 5 * closeness(embedding)`
     - Boosts BM25 scores (2x) and semantic closeness (5x) for refined ranking.
   - Best for hybrid search combining keyword and semantic relevance.

## Usage

### Indexing Data
- Store news articles with an `id`, `title`, `content`, and an optional `embedding` (e.g., generated from a model like BERT).
- Example document:
  ```json
  {
    "id": "news_001",
    "title": "Celebrity X Wins Award",
    "content": "Celebrity X received a prestigious award at the gala last night...",
    "embedding": [0.12, -0.34, ..., 0.56] // 384 floats
  }