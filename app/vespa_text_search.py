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

def text_search(query_text, hits=5):
    """Perform a text-based search using YQL."""
    yql = f'select * from sources celebrity_news where userQuery()'
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
    yql = f'select * from sources celebrity_news where ([{{"targetHits": {hits}}}]nearestNeighbor(embedding, query_embedding))'
    payload = {
        "yql": yql,
        "hits": hits,
        "ranking.profile": "semantic",  
        # "input.query(query_embedding)": f"{{'values': {query_embedding}}}"
        "input.query(query_embedding)": query_embedding

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
    # print("\nSearch Results:")
    # print(results.get("root", {}).get("children", []))  # Print the raw children for debugging
    for hit in results["root"]["children"]:
        fields = hit["fields"]
        print(f"\nNews ID: {fields['id']}")
        print(f"Title: {fields['title']}")
        print(f"Content: {fields['content']}")
        print(f"Relevance: {hit['relevance']}")

def hybrid_search(query_text, hits=5):
    """Perform a hybrid search combining text and semantic search."""
    query_embedding = generate_query_embedding(query_text)
    # yql = f'select * from sources celebrity_news where userQuery() or ([{{"targetHits": {hits}}}]nearestNeighbor(embedding, query_embedding))'
    # yql = f'select * from sources celebrity_news where userQuery() and ([{{"targetHits": {hits}}}]nearestNeighbor(embedding, query_embedding))'
    yql = f'select * from sources celebrity_news where userQuery() or ([{{"targetHits": {hits}}}]nearestNeighbor(embedding, query_embedding))'
    payload = {
        "yql": yql,
        "query": query_text,
        "hits": hits,
        "ranking.profile": "hybrid",
        # "input.query(query_embedding)": f"{{'values': {query_embedding}}}"
        "input.query(query_embedding)": query_embedding
    }
    return execute_search(payload)

def hybrid_search_main(query_text):
    # query_text="little soreness"
    # print(f"=== Hybrid Search: '{query_text}' ===")
    hybrid_results = hybrid_search(query_text)
    # print_results(hybrid_results)
    return hybrid_results

def text_search_main(query_text,username):
    # query_text="little soreness"
    # print(f"=== Text Search: '{query_text}' ===")
    text_results = text_search(query_text,username)
    # print_results(text_results)
    return text_results

def semantic_search_main(query_text):
    # query_text="little soreness"
    # print(f"=== Semantic Search: '{query_text}' ===")
    semantic_results = semantic_search(query_text)
    # print_results(semantic_results)
    return semantic_results

# search_query_texts=["doctor prescribed paracetamol","How can I boost my immune system?","What is the difference between cold and flu?"]
# search_query_texts=["What medicine should I take for body pain?","Why do kids get fevers?"]
# search_query_texts=["antibiotics","antibiotics are used for?","medicine for Allergies"]

search_query_texts=["minor discomfort","Vascular health","Oxygen delivery efficiency"]

if __name__ == "__main__":

    for query_text in search_query_texts:
        # print(f"=== Search Query: '{query_text}' ===")
        text_search_main(query_text)
        print("\n")
        semantic_search_main(query_text)
        print("\n")
        hybrid_search_main(query_text)

    # hybrid_search_main("doctor prescribed paracetamol")
    
def search_api(ranking_profiles, query,username="anonymous"):
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

    # results["totalHits"] = totalHits
    # print(f"Final Search Results for query '{query}': {results}")
    return results,totalHits