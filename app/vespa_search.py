import requests
import json
from sentence_transformers import SentenceTransformer

# Configuration
VESPA_URL = "http://192.168.1.27:2923" 
SEARCH_ENDPOINT = f"{VESPA_URL}/search/"

# Initialize the embedding model
model = SentenceTransformer('all-MiniLM-L6-v2')
# model = SentenceTransformer('all-mpnet-base-v2')  # Uncomment if you prefer this model


def generate_query_embedding(query_text):
    """Generate embedding for the query text."""
    embedding = model.encode(query_text, convert_to_tensor=False).tolist()
    return embedding

def execute_search(payload):
    """Execute the search request and return results."""
    response = requests.post(SEARCH_ENDPOINT, json=payload, headers={"Content-Type": "application/json"})
    
    if response.status_code == 200:
        return response.json()
    else:
        print(f"Search failed: {response.text}")
        return None
    
def hybrid_search(query_text,username, hits=5):
    """Perform a hybrid search combining text and semantic search."""
    query_embedding = generate_query_embedding(query_text)
    yql = f'select * from sources celebrity_news where userQuery() or ([{{"targetHits": {hits}}}]nearestNeighbor(embedding, query_embedding)) and username matches "{username}"'
    payload = {
        "yql": yql,
        "query": query_text,
        "hits": hits,
        "ranking.profile": "hybrid",
        "input.query(query_embedding)": query_embedding
    }
    return execute_search(payload)



def text_search(query_text,username, hits=5):
    """Perform a text-based search using YQL."""
    # yql = f'''
    #         select * from sources celebrity_news where 
    #         (userQuery()) and (user_id = "{username}")
    #     '''
    yql = f'select * from sources celebrity_news where username matches "{username}" and userQuery()'
    payload = {
        "yql": yql,
        "query": query_text,
        "hits": hits,
        "ranking.profile": "default"  
    }
    return execute_search(payload)

def semantic_search(query_text, username,hits=5):
    """Perform a semantic search using embedding similarity."""
    query_embedding = generate_query_embedding(query_text)
    yql = f'select * from sources celebrity_news where ([{{"targetHits": {hits}}}]nearestNeighbor(embedding, query_embedding)) and username matches "{username}"'
    payload = {
        "yql": yql,
        "hits": hits,
        "ranking.profile": "semantic",  
        "input.query(query_embedding)": query_embedding

    }
    return execute_search(payload)



def search_api(ranking_profiles, query,username):
    results = {}
    totalHits={}
    for ranking_profile in ranking_profiles:
        if ranking_profile == "similarity":

            data=text_search(query,username)
            similarity_results = data.get("root", {}).get("children", [])

            total_hits=data.get("root", {}).get("fields", {}).get("totalCount",0) 
            totalHits[ranking_profile] = total_hits  

            if not similarity_results:  
                results["similarity"] = "No results found"
            else:
                results["similarity"] = similarity_results

        elif ranking_profile == "semantic":
            data=semantic_search(query,username)  
            semantic_results = data.get("root", {}).get("children", [])

            total_hits=data.get("root", {}).get("fields", {}).get("totalCount",0)
            totalHits[ranking_profile] = total_hits

            if not semantic_results:
                results["semantic"] = "No results found"
            else:
                results["semantic"] = semantic_results

        elif ranking_profile == "hybrid":

            data=hybrid_search(query,username)
            hybrid_results = data.get("root", {}).get("children", [])

            total_hits=data.get("root", {}).get("fields", {}).get("totalCount",0) 
            totalHits[ranking_profile] = total_hits

            if not hybrid_results:
                results["hybrid"] = "No results found"
            else:
                results["hybrid"] = hybrid_results
                
    return results,totalHits