import requests
import json
from sentence_transformers import SentenceTransformer
from properties.constants import env

# Configuration
# VESPA_URL = env.VESPA_INDEX_SEARCH_URL
# VESPA_URL="http://192.168.1.27:11302"
VESPA_URL="http://192.168.1.98:8081"
# VESPA_URL = config['vespa']['vespaUrl']
SEARCH_ENDPOINT = f"{VESPA_URL}/search/"

model_name= env.MODEL_NAME
# Initialize the embedding model
# model = SentenceTransformer(model_name)

model = SentenceTransformer('all-mpnet-base-v2')  # Uncomment if you prefer this model


def generate_query_embedding(query_text):
    """Generate embedding for the query text."""
    embedding = model.encode(query_text, convert_to_tensor=False).tolist()
    return embedding


def execute_search(payload):
    """Execute the search request and return results."""
    print(f"Payload: {payload}")
    print(f"Search endpoint: {SEARCH_ENDPOINT}")
    response = requests.post(SEARCH_ENDPOINT, json=payload, headers={"Content-Type": "application/json"})

    if response.status_code == 200:
        return response.json()
    else:
        print(f"Search failed: {response.text}")
        return None


def hybrid_search(query_text, user, hits=5):
    """Perform a hybrid search combining text and semantic search."""
    query_embedding = generate_query_embedding(query_text)
    yql = f'select * from sources celebrity_news where username matches @input_username and ( userQuery() or ([{{"targetHits": {hits}}}]nearestNeighbor(content_embd, query_embedding)) )'
    payload = {
        "yql": yql,
        "query": query_text,
        "hits": hits,
        "input_username": user,  
        "ranking.profile": "hybrid",
        "input.query(query_embedding)": query_embedding
    }
    return execute_search(payload)


def hybrid_search_with_index_name(index_name,query_text, hits=5):
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
    return execute_search(payload)

def text_search(query_text, user, hits=5):
    """Perform a text-based search using YQL."""

    yql = f'select * from sources celebrity_news where username matches @input_username and userQuery()'
    payload = {
        "yql": yql,
        "query": query_text,
        "input_username": user,
        "hits": hits,
        "ranking.profile": "default"
    }
    return execute_search(payload)


def text_search_index_name(index_name,query_text, hits=5):
    """Perform a text-based search using YQL."""

    yql = f'select * from sources {index_name} where userQuery()'
    payload = {
        "yql": yql,
        "query": query_text,
        "hits": hits,
        "ranking.profile": "default"
    }
    return execute_search(payload)

def get_all_documents_from_index(index_name, hits=400):
    """Retrieve all documents from the Vespa index."""

    yql = f'select * from sources {index_name} where true'
    # yql = f'select * from sources danswer_index where true'
    payload = {
        "yql": yql,
        "hits": hits,
        "ranking.profile": "default"
    }
    return execute_search(payload)

def semantic_search_from_index(index_name,query_text, hits=5):
    """Perform a semantic search using embedding similarity."""
    query_embedding = generate_query_embedding(query_text)
    yql = f'select * from sources {index_name} where ([{{"targetHits": {hits}}}]nearestNeighbor(embedding, query_embedding)) '
    payload = {
        "yql": yql,
        "hits": hits,
        "ranking.profile": "semantic",
        "input.query(query_embedding)": query_embedding

    }
    return execute_search(payload)


def semantic_search(query_text, user, hits=5):
    """Perform a semantic search using embedding similarity."""
    query_embedding = generate_query_embedding(query_text)
    yql = f'select * from sources celebrity_news where ([{{"targetHits": {hits}}}]nearestNeighbor(content_embd, query_embedding)) and username matches @input_username'
    payload = {
        "yql": yql,
        "hits": hits,
        "input_username": user,
        "ranking.profile": "semantic",
        "input.query(query_embedding)": query_embedding

    }
    return execute_search(payload)


def search_api(ranking_profiles, query, username):
    results = {}
    totalHits = {}
    for ranking_profile in ranking_profiles:
        if ranking_profile == "similarity":

            data = text_search(query, username)
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
            data = semantic_search(query, username)
            semantic_results = data.get("root", {}).get("children", [])

            total_hits = data.get("root", {}).get("fields", {}).get("totalCount", 0)
            totalHits[ranking_profile] = total_hits

            if not semantic_results:
                results["semantic"] = "No results found"
            else:
                results["semantic"] = semantic_results

        elif ranking_profile == "hybrid":

            data = hybrid_search(query, username)
            hybrid_results = data.get("root", {}).get("children", [])

            total_hits = data.get("root", {}).get("fields", {}).get("totalCount", 0)
            totalHits[ranking_profile] = total_hits

            if not hybrid_results:
                results["hybrid"] = "No results found"
            else:
                results["hybrid"] = hybrid_results

    return results, totalHits


def search_api_with_index_name(index_name,ranking_profiles, query):
    results = {}
    totalHits = {}
    for ranking_profile in ranking_profiles:
        if ranking_profile == "similarity":

            data = text_search_index_name(index_name=index_name,query_text= query)
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
            data = semantic_search_from_index(index_name,query)
            semantic_results = data.get("root", {}).get("children", [])

            total_hits = data.get("root", {}).get("fields", {}).get("totalCount", 0)
            totalHits[ranking_profile] = total_hits

            if not semantic_results:
                results["semantic"] = "No results found"
            else:
                results["semantic"] = semantic_results

        elif ranking_profile == "hybrid":

            data = hybrid_search_with_index_name(index_name,query)
            hybrid_results = data.get("root", {}).get("children", [])

            total_hits = data.get("root", {}).get("fields", {}).get("totalCount", 0)
            totalHits[ranking_profile] = total_hits

            if not hybrid_results:
                results["hybrid"] = "No results found"
            else:
                results["hybrid"] = hybrid_results

    return results, totalHits

if __name__ == "__main__":
# Configuration
# VESPA_URL = "http://192.168.1.27:2923"
    VESPA_URL1 = env.VESPA_INDEX_SEARCH_URL
    print(VESPA_URL1)

    # Example usage
    # query = "deforestation"
    # username = "envi"
    # index_name = "general_embed"
    # query = "mumbai"
    # ranking_profiles = ["similarity", "semantic", "hybrid"]
    # search_results, total_hits = search_api_with_index_name(index_name,ranking_profiles, query)
    # print(search_results, total_hits) 
    # results=get_all_documents_from_index("general_embed")
    # results=semantic_search_from_index("general_embed","mumbai")
    
    results=get_all_documents_from_index("danswer_index")
    print(results)