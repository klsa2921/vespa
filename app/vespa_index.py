import json
import requests
from sentence_transformers import SentenceTransformer
import csv
from vespa_chunk import generate_chunks,chunk_pdf
import fitz
from docx import Document
import os
from properties.constants import env
from PyPDF2 import PdfReader
from qa_service.qa_genarator import QaGenerator

# Configuration
# VESPA_URL = "http://localhost:8080" 
VESPA_URL = env.VESPA_INDEX_SEARCH_URL
model_name= env.MODEL_NAME
CHAT_MODEL_NAME=env.CHAT_MODEL_NAME
QA_INDEX_NAME=env.QA_INDEX_NAME
# Initialize the embedding model 
# model = SentenceTransformer(model_name)  # Produces 384-dimensional embeddings


model = SentenceTransformer('all-mpnet-base-v2')  # Produces 768-dimensional embeddings

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

def prepare_despa_document_chunks(text_data, username):
    """Prepare document in Vespa format."""
    # Generate embedding for description

    # Vespa document format
    document = {
        "put": f"id:celebrity_news:celebrity_news::{text_data['id']}",
        "fields": {
            "id": (username + "_" + str(text_data["id"])),
            "username": username,
            "title": text_data["title"],
            "content": text_data["content"],
            "content_embd": {
                "values": text_data["embedding"]
            }
        }
    }
    return document


def prepare_despa_document_chunks_with_index_name(index_name,text_data, username):
    """Prepare document in Vespa format."""
    # Generate embedding for description
    
    fields = {
        "id": (username + "_" + str(text_data["id"]))
                }

    for key, value in text_data.items():
        if key not in ["id"]:
            fields[key] = value
    # Vespa document format
    document = {
        "put": f"id:{index_name}:{index_name}::{text_data['id']}",
        "fields": fields
    }
    return document

def send_text_document_vespa_with_index_name(index_name,document):
    """Send document to Vespa document API."""
    endpoint = f"{VESPA_URL}/document/v1/{index_name}/{index_name}/docid/{document['fields']['id']}"
    response = requests.post(endpoint, json=document, headers={"Content-Type": "application/json"})

    if response.status_code == 200:
        print(f"Successfully indexed text {document['fields']['id']}")
    else:
        print(f"Failed to index text {document['fields']['id']}: {response.text}")



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
    print(f"Processing file: {file_name}")
    try:
        content = read_file(file_name)
        # print(f"File content: {content}")
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


def ingest_chunk_array(chunks, username):
    """
    Ingest an array of text chunks into Vespa.
    :param chunks: list, array of text chunks
    :param username: str, username for the documents
    """
    try:
        for i, chunk in enumerate(chunks):
            try:
                # Prepare the document for Vespa
                id=chunk["index"]
                text_data = {
                    "id": f"chunk_{id}",
                    "title": f"Chunk {id + 1}",
                    "content": chunk["content"],
                    "embedding": generate_embedding(chunk["content"])
                }

                vespa_doc = prepare_despa_document_chunks(text_data, username)
                send_text_document_vespa(vespa_doc)
            except Exception as e:
                print(f"Error processing chunk {i}: {e}")
    except Exception as e:
        print(f"Error ingesting chunks: {e}")




def read_file(file_name):
    try:
        print(f"Reading file: {file_name}")
        file_extension = os.path.splitext(file_name)[1].lower()
        
        if file_extension == '.pdf':
            print("Reading PDF file")
            return read_pdf(file_name)

        elif file_extension == '.docx':
            print("Reading DOCX file")
            return read_docx(file_name)

        elif file_extension == '.txt':
            return read_text_file(file_name)

        else:
            raise ValueError(f"Unsupported file type: {file_extension}")
    except Exception as e:
        print(f"Error reading file in read file method {file_name}: {e}")
        raise


def read_pdf(file_name):
    print(f"Reading PDF file read_pdf method: {file_name}")
    print(f"Resolved file path: {os.path.abspath(file_name)}")
    doc = PdfReader(file_name)
    text = ""
    for page in doc.pages:
        text += page.extract_text()
    return text
    # text = ""
    
    # for page in doc:
    #     text += page.get_text()
    # return text


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


# def ingest_chunks(chunks, username):
#     try:
#         for i, chunk in enumerate(chunks):
#             try:
#                 # Prepare the document for Vespa
#                 text_data = {
#                     "id": chunk["id"],
#                     "title": chunk["id"],
#                     "content": chunk["text"],
#                     "embedding": chunk["embedding"]
#                 }

#                 vespa_doc = prepare_despa_document_chunks(text_data, username)
#                 send_text_document_vespa(vespa_doc)
#             except Exception as e:
#                 print(f"Error processing chunk {i}: {e}")
#     except Exception as e:
#         print(f"Error ingesting chunks: {e}")


def ingest_text_data_with_index_name(data):
    """
    Ingest text data from a JSONL file into Vespa.
    :param file_name: str, path to the JSONL file
    :param username: str, username for the documents
    """
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
                    "id": f"{file_name}_chunk_{i}",
                    "title": f"Chunk {i + 1}",
                    "content": chunk
                }

                vespa_doc = prepare_despa_document_chunks_with_index_name(QA_INDEX_NAME,text_data, username)
                send_text_document_vespa_with_index_name(QA_INDEX_NAME,vespa_doc)
            except Exception as e:
                print(f"Error processing chunk {i}: {e}")
        return chunks
    except Exception as e:
        print(f"Error reading file {file_name}: {e}")

def ingest_qa_data(chunks, username):
    """
    Ingest question-answer data into Vespa.
    :param chunks: list of strings (text chunks)
    """
    try:
        for i, chunk in enumerate(chunks):
            try:
                print(f"Processing chunk {i}...")

                # Step 1: Generate QA
                try:
                    qa_generator = QaGenerator(CHAT_MODEL_NAME)
                    qa_response = qa_generator.generate_qa(chunk)
                    print(f"QA response for chunk {i}: {qa_response}")
                except Exception as e:
                    print(f"Error generating QA for chunk {i}: {e}")
                    continue

                # Step 2: Parse QA response
                if qa_response:
                    try:
                        qa_data = json.loads(qa_response)
                    except Exception as e:
                        print(f"Error parsing QA response JSON for chunk {i}: {e}")
                        continue

                    for qa in qa_data:
                        try:
                            question = qa.get("question")
                            answer = qa.get("answer")

                            if question and answer:
                                try:
                                    embedding = generate_embedding(question)
                                except Exception as e:
                                    print(f"Error generating embedding for question in chunk {i}: {e}")
                                    continue

                                text_data = {
                                    "id": f"qa_chunk_{i}",
                                    "chunkid": f"QA Chunk {i + 1}",
                                    "question": question,
                                    "answer": answer,
                                    "quest_embedding": embedding
                                }

                                try:
                                    vespa_doc = prepare_despa_document_chunks_with_index_name(QA_INDEX_NAME, text_data, username)
                                    send_text_document_vespa_with_index_name(QA_INDEX_NAME, vespa_doc)
                                    print(f"Successfully ingested chunk {i}, question: {question}")
                                except Exception as e:
                                    print(f"Error sending document to Vespa for chunk {i}: {e}")
                        except Exception as e:
                            print(f"Error processing QA pair in chunk {i}: {e}")
            except Exception as e:
                print(f"Unexpected error in processing chunk {i}: {e}")
    except Exception as e:
        print(f"Error ingesting QA data: {e}")


if __name__ == "__main__":
    # content=read_file("C:/Users/mmallikanti/Documents/GitHub/vespa/app/uploads/environment.pdf")
    # doc = fitz.open("C:/Users/mmallikanti/Documents/GitHub/vespa/app/uploads/environment.pdf")
    # chunks = chunk_pdf("C:/Users/mmallikanti/Documents/GitHub/vespa/app/uploads/environment.pdf")
    # print(f"Total chunks: {len(chunks)}")
    # for i, chunk in enumerate(chunks):
        # print(f"\n🔹 Chunk {i + 1}:\n{chunk}")
    chunks=get_chunks("C:/Users/mmallikanti/Documents/GitHub/vespa/app/uploads/environment.pdf")
    print(f"Total chunks: {len(chunks)}")
    # print(f"Chunks: {chunks}")
    ingest_qa_data(chunks,"testuser")
