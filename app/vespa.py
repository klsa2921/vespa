import json
import requests
from sentence_transformers import SentenceTransformer

# Configuration
# VESPA_URL = "http://localhost:8080" 
VESPA_URL = "http://192.168.1.27:2923" 
JSONL_FILE = "employees.jsonl"       
TEXT_JSONL_FILE = "app/data/test.jsonl"
# Initialize the embedding model 
model = SentenceTransformer('all-MiniLM-L6-v2') # Produces 384-dimensional embeddings
# model = SentenceTransformer('all-mpnet-base-v2')  # Produces 768-dimensional embeddings

def generate_embedding(text):
    """Generate embedding for a given text."""
    embedding = model.encode(text, convert_to_tensor=False).tolist()
    return embedding

def prepare_vespa_document(employee_data):
    """Prepare document in Vespa format."""
    # Generate embedding for description
    embedding = generate_embedding(employee_data["description"])
    
    # Vespa document format
    document = {
        "put": f"id:employee:employee::{employee_data['empid']}",
        "fields": {
            "empid": str(employee_data["empid"]), 
            "firstname": employee_data["firstname"],
            "lastname": employee_data["lastname"],
            "department": employee_data["department"],
            "description": employee_data["description"],
            "embedding": {
                "values": embedding  
            }
        }
    }
    return document

def prepare_despa_document_text(text_data):
    """Prepare document in Vespa format."""
    # Generate embedding for description
    embedding = generate_embedding(text_data["content"])
    
    # Vespa document format
    document = {
        "put": f"id:celebrity_news:celebrity_news::{text_data['id']}",
        "fields": {
            "id": str(text_data["id"]), 
            "title": text_data["title"],
            "content": text_data["content"],
            "embedding": {
                "values": embedding  
            }
        }
    }
    return document

def send_to_vespa(document):
    """Send document to Vespa document API."""
    endpoint = f"{VESPA_URL}/document/v1/employee/employee/docid/{document['fields']['empid']}"
    response = requests.post(endpoint, json=document, headers={"Content-Type": "application/json"})
    
    if response.status_code == 200:
        print(f"Successfully indexed employee {document['fields']['empid']}")
    else:
        print(f"Failed to index employee {document['fields']['empid']}: {response.text}")

def send_text_document_vespa(document):
    """Send document to Vespa document API."""
    endpoint = f"{VESPA_URL}/document/v1/celebrity_news/celebrity_news/docid/{document['fields']['id']}"
    response = requests.post(endpoint, json=document, headers={"Content-Type": "application/json"})
    
    if response.status_code == 200:
        print(f"Successfully indexed text {document['fields']['id']}")
    else:
        print(f"Failed to index text {document['fields']['id']}: {response.text}")

def main():
    # Read JSONL file and process each employee
    with open(JSONL_FILE, 'r') as file:
        for line in file:
            try:
                employee_data = json.loads(line.strip())
                vespa_doc = prepare_vespa_document(employee_data)
                # print(vespa_doc)
                send_to_vespa(vespa_doc)
            except Exception as e:
                print(f"Error processing line: {e}")

def main_text():
    # Read JSONL file and process each employee
    with open(TEXT_JSONL_FILE, 'r') as file:
        for line in file:
            try:
                text_data = json.loads(line.strip())
                vespa_doc = prepare_despa_document_text(text_data)
                # print(vespa_doc)
                send_text_document_vespa(vespa_doc)
            except Exception as e:
                print(f"Error processing line: {e}")

if __name__ == "__main__":
    main_text()