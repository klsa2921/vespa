# Vespa Schema

This document describes the `celebrity_news` schema, designed for storing and searching celebrity-related news articles. The schema supports both traditional text-based search (using BM25 ranking) and semantic search (using embeddings), with hybrid options for combining both approaches.

## Schema Structure

### Document Definition
- **Type**: `celebrity_news`
- **Fields**:
  - **`id`** (string)
    - Indexing: `summary | attribute`
    - Matching: `exact`
  - **`title`** (string)
    - Indexing: `summary | index`
  - **`content`** (string)
    - Indexing: `summary | index`
    - Ranking: `enable-bm25` (enables BM25 scoring for text search)
  - **`embedding`** (tensor<float>(d0[384]))
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
     - Combines BM25 text scoring with semantic similarity (weighted 10x for embeddings). In second phase results 
   - Ideal for semantic search with some text relevance.

3. **`hybrid`**
   - **Inputs**: `query(query_embedding)` (tensor<float>(d0[384]))
   - **First Phase**: `bm25(title) + bm25(content) + closeness(embedding)`
     - Combines text and semantic scoring in the initial ranking.
   - **Second Phase**: `2 * bm25(title) + 2 * bm25(content) + 5 * closeness(embedding)`
     - Boosts BM25 scores (2x) and semantic closeness (5x) for refined ranking.
   - Best for hybrid search combining keyword and semantic relevance.

## Field Indexing Terms
- **`summary`**: Indicates the field is included in a summary of the document, typically for quick retrieval or display.
- **`index`**: Marks the field as searchable, enabling it to be queried using text-based search algorithms like BM25.
- **`attribute`**: Denotes the field is stored as a raw value for exact matching or fast retrieval, often used for filtering or semantic operations. And fields are stored in memory for fast retriveal.
- **`enable-bm25`**: Activates BM25 ranking for the field, a scoring algorithm that ranks documents based on term frequency and document length.
- **`exact`**: Specifies that matching on this field requires an exact string match, without partial or fuzzy matching.
- **`euclidean`**: Refers to the Euclidean distance metric used to measure similarity between embeddings in semantic search.

## Dependencies

To run the application, ensure the following dependencies are installed:

- **Python**: Version 3.8 or higher.
- **Flask**: A lightweight WSGI web application framework.
- **NumPy**: For numerical operations, including handling embeddings.
- **Pandas**: For data manipulation and CSV file handling.
- **Vespa**: For interacting with the Vespa engine.


You can install the dependencies using the following command:

```bash
pip install -r requirements.txt
```


## Running the Application

To start the application, navigate to the `app/` directory and run the following command in your terminal:

```bash
python app.py
```

Ensure that all dependencies are installed and the required environment variables are configured before starting the application.


## Ingestion Data

The schema supports data ingestion through CSV files. From the web page, you can upload only CSV files. Each CSV file must contain the following fields:

- **`id`**: A unique identifier for the data.
- **`title`**: The title of the data.
- **`content`**: The full text content .

Ensure that the CSV file adheres to this structure for successful ingestion.

## Local Access
When running the application locally, it can be accessed at the following port:

- **Port**: `5000`

Ensure that your local environment is configured to allow access to this port.
