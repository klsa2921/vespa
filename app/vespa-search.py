import requests
import json
from sentence_transformers import SentenceTransformer

# Configuration
VESPA_URL = "http://localhost:8080"
SEARCH_ENDPOINT = f"{VESPA_URL}/search/"

# Initialize the embedding model
model = SentenceTransformer('all-MiniLM-L6-v2')


# model = SentenceTransformer('all-mpnet-base-v2')

def generate_query_embedding(query_text):
    """Generate embedding for the query text."""
    embedding = model.encode(query_text, convert_to_tensor=False).tolist()
    return embedding


def text_search(query_text, hits=5):
    """Perform a text-based search using YQL."""
    yql = f'select * from sources employee where userQuery()'
    payload = {
        "yql": yql,
        "query": query_text,
        "hits": hits,
        "ranking.profile": "default"
    }
    return execute_search(payload)


def semantic_search(query_text, hits=5):
    """Perform a semantic search using embedding similarity."""
    query_embedding = generate_query_embedding(query_text)
    yql = f'select * from sources employee where ([{{"targetHits": {hits}}}]nearestNeighbor(embedding, query_embedding))'
    payload = {
        "yql": yql,
        "hits": hits,
        "ranking.profile": "semantic",
        "input.query(query_embedding)": f"{{'values': {query_embedding}}}"
    }
    return execute_search(payload)


def execute_search(payload):
    """Execute the search request and return results."""
    response = requests.post(SEARCH_ENDPOINT, json=payload, headers={"Content-Type": "application/json"})

    if response.status_code == 200:
        return response.json()
    else:
        print(f"Search failed: {response.text}")
        return None


def print_results(results):
    """Print search results in a readable format."""
    if not results or "root" not in results or "children" not in results["root"]:
        print("No results found.")
        return

    for hit in results["root"]["children"]:
        fields = hit["fields"]
        print(f"\nEmployee ID: {fields['empid']}")
        print(f"Name: {fields['firstname']} {fields['lastname']}")
        print(f"Department: {fields['department']}")
        print(f"Description: {fields['description']}")
        print(f"Relevance: {hit['relevance']}")


def hybrid_search(query_text, hits=5):
    query_embedding = generate_query_embedding(query_text)
    yql = f'select * from sources employee where userQuery() or ([{{"targetHits": {hits}}}]nearestNeighbor(embedding, query_embedding))'
    payload = {
        "yql": yql,
        "query": query_text,
        "hits": hits,
        "ranking.profile": "semantic",
        "input.query(query_embedding)": f"{{'values': {query_embedding}}}"
    }
    return execute_search(payload)


def main():
    # Example text search
    print("=== Text Search: 'software engineer' ===")
    text_results = text_search("specialized cloud engineer")
    print_results(text_results)

    # Example semantic search
    print("=== Semantic Search: 'experienced engineer specializing in cloud' ===")
    semantic_results = semantic_search("specialized cloud engineer")
    print_results(semantic_results)


if __name__ == "__main__":
    # main()
    results = hybrid_search("specialized cloud engineer")
    print_results(results)
