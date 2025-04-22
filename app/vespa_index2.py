from PyPDF2 import PdfReader
from docx import Document
import requests
from sentence_transformers import SentenceTransformer
from qa_service.qa_genarator import QaGenerator
import json
import os
try:
    model = SentenceTransformer('all-mpnet-base-v2')
except Exception as e:
    print(f"Error loading SentenceTransformer model: {e}")

def generate_embedding(text):
    """Generate embedding for a given text."""
    try:
        content_embd = model.encode(text, convert_to_tensor=False).tolist()
        return content_embd
    except Exception as e:
        print(f"Error generating embedding for text: {e}")
        return []

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


def send_text_document_vespa_with_index_name(index_name, vespa_index_url, document):
    """Send document to Vespa document API."""
    try:
        # print(f"Sending document to Vespa: {document}")
        endpoint = f"{vespa_index_url}/document/v1/{index_name}/{index_name}/docid/{document['fields']['id']}"
        response = requests.post(endpoint, json=document, headers={"Content-Type": "application/json"})
        if response.status_code == 200:
            print(f"Successfully indexed text {document['fields']['id']}")
        else:
            print(f"Failed to index text {document['fields']['id']}: {response.text}")
    except Exception as e:
        print(f"Error sending document to Vespa: {e}")

def prepare_vespa_document_chunks_with_index_name(index_name, text_data, username):
    """Prepare document in Vespa format."""
    try:
        fields = {}
        for key, value in text_data.items():
            fields[key] = value
        # Vespa document format
        document = {
            "put": f"id:{index_name}:{index_name}::{text_data['id']}",
            "fields": fields
        }
        return document
    except Exception as e:
        print(f"Error preparing Vespa document: {e}")
        return {}

def ingest_text_data_with_index_name(data):
    """Ingest text data into Vespa."""
    try:
        chunks = data["chunks"]
        username = data["username"]
        vespa_config = data["vespaConfig"]
        index_name = vespa_config["index_name"]
        vespa_index_url = vespa_config["vespa_index_url"]
        embedding_field = vespa_config["embedding_field_name"]
        file_name = data["file_name"]
        # print(chunks)
        for i, chunk in enumerate(chunks):
            # print(f"Processing chunk {i}: {chunk}")
            try:
                # Prepare the document for Vespa
                text_data = {
                    "id": f"{username}_{file_name}_chunk_{i}",
                    "chunkid": f"Chunk {chunk['index']}",
                    "content": chunk["content"],
                    "username": username,
                    f"{embedding_field}": generate_embedding(chunk["content"]),
                }
                vespa_doc = prepare_vespa_document_chunks_with_index_name(index_name, text_data, username)
                send_text_document_vespa_with_index_name(index_name, vespa_index_url, vespa_doc)
                
            except Exception as e:
                print(f"Error processing chunk {i}: {e}")
        return chunks
    except Exception as e:
        print(f"Error ingesting text data for file {data.get('file_name', 'unknown')}: {e}")
        return []

def ingest_qa_data(data):
    """
    Ingest question-answer data into Vespa.
    :param chunks: list of strings (text chunks)
    """
    try:
        chunks= data["chunks"]
        username = data["username"]
        vespa_config = data["vespaConfig"]
        vespa_index_url = vespa_config["vespa_index_url"]
        qa_index_name = vespa_config["qa_index_name"]
        chat_model_name = vespa_config["qa_index_name"]
        embedding_field = vespa_config["embedding_field_name"]
        file_name = data["file_name"]
    except KeyError as e:
        print(f"Missing configuration in data: {e}")
        return
    qa_data=[]
    try:
        for i, chunk in enumerate(chunks):
            try:
                print(f"Processing chunk {i}...")

                # Step 1: Generate QA
                try:
                    qa_generator = QaGenerator(chat_model_name)
                    qa_response = qa_generator.generate_qa(chunk)
                except Exception as e:
                    print(f"Error generating QA for chunk {i}: {e}")
                    continue

                # Step 2: Parse QA response
                if qa_response:
                    # try:
                    #     qa_data = json.loads(qa_response)
                    # except Exception as e:
                    #     print(f"Error parsing QA response JSON for chunk {i}: {e}")
                    #     continue

                    for qa in qa_response:
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
                                    "id": f"{username}_{file_name}_qa_chunk_{i}",
                                    "chunkid": f"QA Chunk {i + 1}",
                                    "question": question,
                                    "username": username,
                                    "answer": answer,
                                    "quest_embedding": embedding
                                }

                                try:
                                    vespa_doc = prepare_vespa_document_chunks_with_index_name(qa_index_name, text_data, username)
                                    send_text_document_vespa_with_index_name(qa_index_name, vespa_index_url, vespa_doc)
                                except Exception as e:
                                    print(f"Error sending document to Vespa for chunk {i}: {e}")
                        except Exception as e:
                            print(f"Error processing QA pair in chunk {i}: {e}")
                        qa_data.append({
                            "question": question,
                            "answer": answer
                        })
                # return qa_response   
            except Exception as e:
                print(f"Unexpected error in processing chunk {i}: {e}")
        return qa_data
    except Exception as e:
        print(f"Error ingesting QA data: {e}")