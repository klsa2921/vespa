import os
import requests
from sentence_transformers import SentenceTransformer


model = SentenceTransformer('all-mpnet-base-v2')  # Uncomment if you prefer this model


def generate_query_embedding(query_text):
    """Generate embedding for the query text."""
    embedding = model.encode(query_text, convert_to_tensor=False).tolist()
    return embedding

def execute_search(api_url,payload):
    """Execute the search request and return results."""
    print(f"Payload: {payload}")
    print(f"Search endpoint: {api_url}")
    api_url = f"{api_url}/search/"
    response = requests.post(api_url, json=payload, headers={"Content-Type": "application/json"})

    if response.status_code == 200:
        return response.json()
    else:
        print(f"Search failed: {response.text}")
        return None

def text_search_index_name(vespa_search_url,index_name,query_text, embedding_field,hits=5):
    """Perform a text-based search using YQL."""

    yql = f'select * from sources {index_name} where userQuery()'
    payload = {
        "yql": yql,
        "query": query_text,
        "type":"phrase",
        "hits": hits,
        "ranking.profile": "default"
    }
    return execute_search(vespa_search_url,payload)

def semantic_search_from_index(vespa_search_url,index_name,query_text, hits=5):
    """Perform a semantic search using embedding similarity."""
    query_embedding = generate_query_embedding(query_text)
    yql = f'select * from sources {index_name} where ([{{"targetHits": {hits}}}]nearestNeighbor({embedding_field}, query_embedding)) '
    payload = {
        "yql": yql,
        "hits": hits,
        "ranking.profile": "semantic",
        "input.query(query_embedding)": query_embedding

    }
    return execute_search(vespa_search_url,payload)

def hybrid_search_with_index_name(vespa_search_url,index_name,query_text, hits=5):
    """Perform a hybrid search combining text and semantic search."""
    query_embedding = generate_query_embedding(query_text)
    yql = f'select * from sources {index_name} where ( userQuery() or ([{{"targetHits": {hits}}}]nearestNeighbor(embedding, query_embedding)) )'
    payload = {
        "yql": yql,
        "query": query_text,
        "hits": hits,
        "ranking.profile": "hybrid",
        "input.query(query_embedding)": query_embedding
    }
    return execute_search(vespa_search_url,payload)

def search_api(data):
    """Search API to handle different ranking profiles."""
    vespa_config = data["vespaConfig"]
    index_name = vespa_config["index_name"]
    vespa_search_url = vespa_config["vespa_index_url"]
    embedding_field = vespa_config["embedding_field_name"]
    query = data["query"]
    ranking_profiles = data["ranking_profiles"]


    results = {}
    totalHits = {}
    for ranking_profile in ranking_profiles:
        if ranking_profile == "similarity":

            data = text_search_index_name(vespa_search_url,index_name=index_name,query_text= query,embedding_field=embedding_field)
            if data is None:
                results["similarity"] = "No results found"
                continue
            similarity_results = data.get("root", {}).get("children", [])

            total_hits = data.get("root", {}).get("fields", {}).get("totalCount", 0)
            totalHits[ranking_profile] = total_hits

            if not similarity_results:
                results["similarity"] = "No results found"
            else:
                results["similarity"] = similarity_results

        elif ranking_profile == "semantic":
            data = semantic_search_from_index(vespa_search_url,index_name,query)
            semantic_results = data.get("root", {}).get("children", [])

            total_hits = data.get("root", {}).get("fields", {}).get("totalCount", 0)
            totalHits[ranking_profile] = total_hits

            if not semantic_results:
                results["semantic"] = "No results found"
            else:
                results["semantic"] = semantic_results

        elif ranking_profile == "hybrid":

            data = hybrid_search_with_index_name(vespa_search_url,index_name,query)
            hybrid_results = data.get("root", {}).get("children", [])

            total_hits = data.get("root", {}).get("fields", {}).get("totalCount", 0)
            totalHits[ranking_profile] = total_hits

            if not hybrid_results:
                results["hybrid"] = "No results found"
            else:
                results["hybrid"] = hybrid_results

    return results, totalHits