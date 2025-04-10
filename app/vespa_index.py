import json
import requests
from sentence_transformers import SentenceTransformer
import csv
from vespa_chunk import generate_chunks,chunk_pdf
import fitz
from docx import Document
import os
from properties.constants import docker,local

# Configuration
# VESPA_URL = "http://localhost:8080" 
VESPA_URL = docker.VESPA_INDEX_SEARCH_URL
model_name= docker.MODEL_NAME
# Initialize the embedding model 
model = SentenceTransformer(model_name)  # Produces 384-dimensional embeddings


# model = SentenceTransformer('all-mpnet-base-v2')  # Produces 768-dimensional embeddings

def generate_embedding(text):
    """Generate embedding for a given text."""
    content_embd = model.encode(text, convert_to_tensor=False).tolist()
    return content_embd


def prepare_despa_document_text(text_data, username):
    """Prepare document in Vespa format."""
    # Generate embedding for description
    content_embd = generate_embedding(text_data["content"])

    # Vespa document format
    document = {
        "put": f"id:celebrity_news:celebrity_news::{text_data['id']}",
        "fields": {
            "id": (username + "_" + str(text_data["id"])),
            "username": username,
            "title": text_data["title"],
            "content": text_data["content"],
            "content_embd": {
                "values": content_embd
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


def ingest_csv(csv_file, username):
    with open(csv_file, mode='r', encoding='utf-8', errors='ignore') as file:
        reader = csv.DictReader(file)
        for row in reader:
            try:
                vespa_doc = prepare_despa_document_text(row, username)
                send_text_document_vespa(vespa_doc)
            except Exception as e:
                print(f"Error processing row: {e}")


def ingest_text_data(file_name, username):
    """
    Ingest text data from a JSONL file into Vespa.
    :param file_name: str, path to the JSONL file
    :param username: str, username for the documents
    """
    try:
        content = read_file(file_name)
        chunks = generate_chunks(content)
        for i, chunk in enumerate(chunks):
            try:
                # Prepare the document for Vespa
                text_data = {
                    "id": f"{file_name}_chunk_{i}",
                    "title": f"Chunk {i + 1}",
                    "content": chunk
                }

                vespa_doc = prepare_despa_document_text(text_data, username)
                send_text_document_vespa(vespa_doc)
            except Exception as e:
                print(f"Error processing chunk {i}: {e}")
        return chunks
    except Exception as e:
        print(f"Error reading file {file_name}: {e}")




def read_file(file_name):
    file_extension = os.path.splitext(file_name)[1].lower()

    if file_extension == '.pdf':
        return read_pdf(file_name)

    elif file_extension == '.docx':
        return read_docx(file_name)

    elif file_extension == '.txt':
        return read_text_file(file_name)

    else:
        raise ValueError(f"Unsupported file type: {file_extension}")


def read_pdf(file_name):
    doc = fitz.open(file_name)
    text = ""
    for page in doc:
        text += page.get_text()
    return text


def read_docx(file_name):
    doc = Document(file_name)
    text = ""
    for para in doc.paragraphs:
        text += para.text + "\n"
    return text


def read_text_file(file_name):
    with open(file_name, 'r', encoding='utf-8', errors='ignore') as f:
        return f.read()


def get_chunks(file_path):
    content = read_file(file_path)
    return generate_chunks(content)


def ingest_chunks(chunks, username):
    try:
        for i, chunk in enumerate(chunks):
            try:
                # Prepare the document for Vespa
                text_data = {
                    "id": chunk["id"],
                    "title": chunk["title"],
                    "content": chunk["text"]
                }

                vespa_doc = prepare_despa_document_text(text_data, username)
                send_text_document_vespa(vespa_doc)
            except Exception as e:
                print(f"Error processing chunk {i}: {e}")
    except Exception as e:
        print(f"Error ingesting chunks: {e}")


if __name__ == "__main__":
    # content=read_file("C:/Users/mmallikanti/Documents/GitHub/vespa/app/uploads/environment.pdf")
    # doc = fitz.open("C:/Users/mmallikanti/Documents/GitHub/vespa/app/uploads/environment.pdf")
    chunks = chunk_pdf("C:/Users/mmallikanti/Documents/GitHub/vespa/app/uploads/environment.pdf")
    print(f"Total chunks: {len(chunks)}")
    for i, chunk in enumerate(chunks):
        print(f"\n🔹 Chunk {i + 1}:\n{chunk}")
