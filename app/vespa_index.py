import json
import requests
from sentence_transformers import SentenceTransformer
import csv
# Configuration
# VESPA_URL = "http://localhost:8080" 
VESPA_URL = "http://192.168.1.27:2923" 
JSONL_FILE = "employees.jsonl"       
TEXT_JSONL_FILE = "app/data/test-search.jsonl"

# Initialize the embedding model 
model = SentenceTransformer('all-MiniLM-L6-v2') # Produces 384-dimensional embeddings
# model = SentenceTransformer('all-mpnet-base-v2')  # Produces 768-dimensional embeddings

def generate_embedding(text):
    """Generate embedding for a given text."""
    embedding = model.encode(text, convert_to_tensor=False).tolist()
    return embedding


def prepare_despa_document_text(text_data,username):
    """Prepare document in Vespa format."""
    # Generate embedding for description
    embedding = generate_embedding(text_data["content"])
    
    # Vespa document format
    document = {
        "put": f"id:celebrity_news:celebrity_news::{text_data['id']}",
        "fields": {
            "id": (username + "_"+str(text_data["id"])), 
            "username": username,
            "title": text_data["title"],
            "content": text_data["content"],
            "embedding": {
                "values": embedding  
            }
        }
    }
    return document


def send_text_document_vespa(document):
    """Send document to Vespa document API."""
    endpoint = f"{VESPA_URL}/document/v1/celebrity_news/celebrity_news/docid/{document['fields']['id']}"
    response = requests.post(endpoint, json=document, headers={"Content-Type": "application/json"})
    
    if response.status_code == 200:
        print(f"Successfully indexed text {document['fields']['id']}")
    else:
        print(f"Failed to index text {document['fields']['id']}: {response.text}")

def ingest_csv(csv_file,username):
    with open(csv_file, mode='r', encoding='utf-8', errors='ignore') as file:
        reader = csv.DictReader(file)
        for row in reader:
            try:
                vespa_doc = prepare_despa_document_text(row,username)  
                send_text_document_vespa(vespa_doc)
            except Exception as e:
                print(f"Error processing row: {e}")