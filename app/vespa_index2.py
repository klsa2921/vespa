import requests
from sentence_transformers import SentenceTransformer

model = SentenceTransformer('all-mpnet-base-v2')

def generate_embedding(text):
    """Generate embedding for a given text."""
    content_embd = model.encode(text, convert_to_tensor=False).tolist()
    return content_embd

def send_text_document_vespa_with_index_name(index_name,vespa_index_url,document):
    """Send document to Vespa document API."""
    endpoint = f"{vespa_index_url}/document/v1/{index_name}/{index_name}/docid/{document['fields']['id']}"
    response = requests.post(endpoint, json=document, headers={"Content-Type": "application/json"})

    if response.status_code == 200:
        print(f"Successfully indexed text {document['fields']['id']}")
    else:
        print(f"Failed to index text {document['fields']['id']}: {response.text}")


def prepare_vespa_document_chunks_with_index_name(index_name,text_data, username):
    """Prepare document in Vespa format."""
    # Generate embedding for description
    
    fields = {}

    for key, value in text_data.items():
        if key not in ["id"]:
            fields[key] = value
    # Vespa document format
    document = {
        "put": f"id:{index_name}:{index_name}::{text_data['id']}",
        "fields": fields
    }
    return document


def ingest_text_data_with_index_name(data):

    chunks = data["chunks"]
    username = data["username"]
    index_name= data["index_name"]
    vespa_index_url= data["vespa_index_url"]
    file_name = data["file_name"]
    
    try:
        # print(f"File content: {content}")
        for i, chunk in enumerate(chunks):
            try:
                # Prepare the document for Vespa
                text_data = {
                    "id": f"{username}_{file_name}_chunk_{i}",
                    "chunkid": f"Chunk {i + 1}",
                    "content": chunk,
                    "username": username,
                    "content_embd": generate_embedding(chunk)
                }

                vespa_doc = prepare_vespa_document_chunks_with_index_name(index_name,text_data,username)
                send_text_document_vespa_with_index_name(index_name,vespa_index_url,vespa_doc)
            except Exception as e:
                print(f"Error processing chunk {i}: {e}")
        return chunks
    except Exception as e:
        print(f"Error reading file {file_name}: {e}")