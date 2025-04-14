import pdfplumber
import re
import numpy as np
from sentence_transformers import SentenceTransformer
from sklearn.metrics.pairwise import cosine_similarity
from typing import List, Dict, Any
import uuid

class PDFChunker:
    def __init__(self, pdf_path: str):
        self.pdf_path = pdf_path
        self.model = SentenceTransformer('all-MiniLM-L6-v2')  # For semantic chunking

    def extract_elements(self) -> List[Dict[str, Any]]:
        """Extract text, tables, and metadata from PDF."""
        elements = []
        try:
            with pdfplumber.open(self.pdf_path) as pdf:
                for page_num, page in enumerate(pdf.pages):
                    # Extract text and metadata
                    text = page.extract_text() or ""
                    tables = page.extract_tables() or []
                    chars = page.chars or []  # For font-based heading detection

                    # Detect headings with stricter criteria
                    headings = []
                    for char in chars:
                        text = char.get('text', '').strip()
                        size = char.get('size', 0)
                        fontname = char.get('fontname', '')
                        if (size > 12 and 'Bold' in fontname and 
                            text and not re.match(r'^[\.\d\s]+$', text)):
                            headings.append({'text': text, 'y0': char['y0'], 'page': page_num})

                    # Extract paragraphs (split text into blocks)
                    paragraphs = []
                    if text:
                        para_blocks = text.split('\n\n')
                        for para in para_blocks:
                            cleaned_para = para.strip()
                            if cleaned_para and len(cleaned_para) > 10:
                                paragraphs.append(cleaned_para)

                    # Filter valid tables
                    valid_tables = []
                    for table in tables:
                        # Check if table has meaningful content
                        if table and any(row for row in table if any(cell for cell in row if cell)):
                            valid_tables.append(table)

                    # Store elements
                    elements.append({
                        'page': page_num,
                        'text': text,
                        'paragraphs': paragraphs,
                        'tables': valid_tables,
                        'headings': headings
                    })
        except Exception as e:
            print(f"Error extracting elements from PDF: {e}")
            return []
        return elements

    def semantic_section_based_chunking(self, max_chunk_size: int = 512) -> List[Dict[str, Any]]:
        """Chunk PDF by semantic sections (headings and their content)."""
        elements = self.extract_elements()
        chunks = []
        current_chunk = {
            'id': str(uuid.uuid4()), 
            'content': '', 
            'metadata': {'type': 'section', 'headings': [], 'pages': []}
        }
        current_size = 0

        for element in elements:
            page = element['page']
            headings = element['headings']
            paragraphs = element['paragraphs']
            tables = element['tables']

            for heading in headings:
                heading_text = heading['text'].strip()
                if len(heading_text) > 1 and not re.match(r'^[\.\d\s]+$', heading_text):
                    if current_chunk['content'] or current_size > 0:
                        chunks.append(current_chunk)
                        current_chunk = {
                            'id': str(uuid.uuid4()), 
                            'content': '', 
                            'metadata': {'type': 'section', 'headings': [], 'pages': []}
                        }
                        current_size = 0
                    current_chunk['metadata']['headings'].append(heading_text)
                    current_chunk['content'] += f"# {heading_text}\n"
                    current_size += len(heading_text.split())
                    if page not in current_chunk['metadata']['pages']:
                        current_chunk['metadata']['pages'].append(page)

            for para in paragraphs:
                para_size = len(para.split())
                if current_size + para_size > max_chunk_size:
                    if current_chunk['content']:
                        chunks.append(current_chunk)
                    current_chunk = {
                        'id': str(uuid.uuid4()), 
                        'content': '', 
                        'metadata': {
                            'type': 'section', 
                            'headings': current_chunk['metadata']['headings'], 
                            'pages': []
                        }
                    }
                    current_size = 0
                current_chunk['content'] += f"{para}\n\n"
                current_size += para_size
                if page not in current_chunk['metadata']['pages']:
                    current_chunk['metadata']['pages'].append(page)

            for table in tables:
                try:
                    table_text = "\n".join([" | ".join(str(cell or '') for cell in row) for row in table])
                    table_size = len(table_text.split())
                    if current_size + table_size > max_chunk_size:
                        if current_chunk['content']:
                            chunks.append(current_chunk)
                        current_chunk = {
                            'id': str(uuid.uuid4()), 
                            'content': '', 
                            'metadata': {
                                'type': 'section', 
                                'headings': current_chunk['metadata']['headings'], 
                                'pages': []
                            }
                        }
                        current_size = 0
                    current_chunk['content'] += f"\nTable:\n{table_text}\n\n"
                    current_size += table_size
                    if page not in current_chunk['metadata']['pages']:
                        current_chunk['metadata']['pages'].append(page)
                except Exception as e:
                    print(f"Error processing table on page {page}: {e}")
                    continue

        if current_chunk['content']:
            chunks.append(current_chunk)

        valid_chunks = [
            chunk for chunk in chunks 
            if chunk['content'].strip() and 
            (chunk['metadata']['headings'] or len(chunk['content']) > 50)
        ]

        return valid_chunks

    def element_based_chunking(self, max_chunk_size: int = 512) -> List[Dict[str, Any]]:
        """Chunk PDF by elements (paragraphs, tables, lists) with contextual grouping."""
        elements = self.extract_elements()
        chunks = []
        current_chunk = {
            'id': str(uuid.uuid4()), 
            'content': '', 
            'metadata': {'type': 'element', 'elements': [], 'pages': []}
        }
        current_size = 0

        for element in elements:
            page = element['page']
            paragraphs = element['paragraphs']
            tables = element['tables']

            # Process paragraphs and lists
            for para in paragraphs:
                # Broaden list detection
                is_list = bool(re.match(r'^\s*[-*•◦]|\d+\.|\([a-zA-Z0-9]+\)|\w+\)', para))
                element_type = 'list' if is_list else 'paragraph'
                para_size = len(para.split())

                # Start a new chunk if size exceeds limit
                if current_size + para_size > max_chunk_size and current_chunk['content']:
                    chunks.append(current_chunk)
                    current_chunk = {
                        'id': str(uuid.uuid4()), 
                        'content': '', 
                        'metadata': {'type': 'element', 'elements': [], 'pages': []}
                    }
                    current_size = 0

                current_chunk['content'] += f"{para}\n\n"
                current_size += para_size
                current_chunk['metadata']['elements'].append(element_type)
                if page not in current_chunk['metadata']['pages']:
                    current_chunk['metadata']['pages'].append(page)

            # Process tables
            for table in tables:
                try:
                    # Convert table to text
                    table_text = "\n".join([" | ".join(str(cell or '') for cell in row) for row in table])
                    table_size = len(table_text.split())

                    # Skip empty or near-empty tables
                    if not table_text.strip() or table_size < 5:
                        continue

                    # Start a new chunk if size exceeds limit
                    if current_size + table_size > max_chunk_size and current_chunk['content']:
                        chunks.append(current_chunk)
                        current_chunk = {
                            'id': str(uuid.uuid4()), 
                            'content': '', 
                            'metadata': {'type': 'element', 'elements': [], 'pages': []}
                        }
                        current_size = 0

                    # Look for preceding paragraph as context (e.g., caption)
                    context = ""
                    if paragraphs:
                        # Use the last paragraph as potential context
                        last_para = paragraphs[-1]
                        if len(last_para.split()) < 50:  # Assume short paragraph is a caption
                            context = f"{last_para}\n\n"
                            if context not in current_chunk['content']:
                                current_chunk['content'] += context
                                current_size += len(last_para.split())
                                current_chunk['metadata']['elements'].append('paragraph')
                                if page not in current_chunk['metadata']['pages']:
                                    current_chunk['metadata']['pages'].append(page)

                    current_chunk['content'] += f"Table:\n{table_text}\n\n"
                    current_size += table_size
                    current_chunk['metadata']['elements'].append('table')
                    if page not in current_chunk['metadata']['pages']:
                        current_chunk['metadata']['pages'].append(page)

                except Exception as e:
                    print(f"Error processing table on page {page}: {e}")
                    continue

            # Avoid overly large chunks
            if current_size > max_chunk_size * 1.5 and current_chunk['content']:
                chunks.append(current_chunk)
                current_chunk = {
                    'id': str(uuid.uuid4()), 
                    'content': '', 
                    'metadata': {'type': 'element', 'elements': [], 'pages': []}
                }
                current_size = 0

        if current_chunk['content']:
            chunks.append(current_chunk)

        # Filter out invalid chunks
        valid_chunks = [
            chunk for chunk in chunks 
            if chunk['content'].strip() and len(chunk['content']) > 20
        ]

        return valid_chunks

    def hybrid_chunking(self, max_chunk_size: int = 512, similarity_threshold: float = 0.7) -> List[Dict[str, Any]]:
        """Chunk PDF using structure and semantic similarity."""
        elements = self.extract_elements()
        chunks = []
        current_chunk = {'id': str(uuid.uuid4()), 'content': '', 'metadata': {'type': 'hybrid', 'elements': [], 'headings': [], 'pages': []}}
        current_size = 0
        sentences = []
        sentence_positions = []

        for element in elements:
            page = element['page']
            headings = element['headings']
            paragraphs = element['paragraphs']
            tables = element['tables']

            for heading in headings:
                heading_text = heading['text'].strip()
                if len(heading_text) > 1 and not re.match(r'^[\.\d\s]+$', heading_text):
                    if current_size > 0:
                        chunks.append(current_chunk)
                        current_chunk = {'id': str(uuid.uuid4()), 'content': '', 'metadata': {'type': 'hybrid', 'elements': [], 'headings': [], 'pages': []}}
                        current_size = 0
                    current_chunk['content'] += f"# {heading_text}\n"
                    current_size += len(heading_text.split())
                    current_chunk['metadata']['headings'].append(heading_text)
                    sentences.append(heading_text)
                    sentence_positions.append((page, 'heading', len(sentences) - 1))

            for para_idx, para in enumerate(paragraphs):
                para_sentences = re.split(r'(?<=[.!?])\s+', para.strip())
                for sent in para_sentences:
                    if sent.strip():
                        sentences.append(sent.strip())
                        sentence_positions.append((page, 'paragraph', para_idx))
                current_chunk['content'] += f"{para}\n\n"
                current_size += len(para.split())
                current_chunk['metadata']['elements'].append('paragraph')
                if page not in current_chunk['metadata']['pages']:
                    current_chunk['metadata']['pages'].append(page)

            for table_idx, table in enumerate(tables):
                try:
                    table_text = "\n".join([" | ".join(str(cell or '') for cell in row) for row in table])
                    table_size = len(table_text.split())
                    current_chunk['content'] += f"Table:\n{table_text}\n\n"
                    current_size += table_size
                    current_chunk['metadata']['elements'].append('table')
                    sentences.append(table_text[:100])
                    sentence_positions.append((page, 'table', table_idx))
                    if page not in current_chunk['metadata']['pages']:
                        current_chunk['metadata']['pages'].append(page)
                except Exception as e:
                    print(f"Error processing table on page {page}: {e}")
                    continue

            if current_size > max_chunk_size:
                chunks.append(current_chunk)
                current_chunk = {'id': str(uuid.uuid4()), 'content': '', 'metadata': {'type': 'hybrid', 'elements': [], 'headings': [], 'pages': []}}
                current_size = 0

        if sentences:
            try:
                embeddings = self.model.encode(sentences)
                similarity_matrix = cosine_similarity(embeddings)
                grouped_sentences = []
                current_group = [0]
                for i in range(1, len(sentences)):
                    if similarity_matrix[i-1][i] > similarity_threshold:
                        current_group.append(i)
                    else:
                        grouped_sentences.append(current_group)
                        current_group = [i]
                grouped_sentences.append(current_group)

                chunk_idx = 0
                for group in grouped_sentences:
                    chunk_content = ''
                    chunk_metadata = {'type': 'hybrid', 'elements': [], 'headings': [], 'pages': []}
                    for sent_idx in group:
                        page, elem_type, _ = sentence_positions[sent_idx]
                        chunk_content += f"{sentences[sent_idx]}\n"
                        chunk_metadata['elements'].append(elem_type)
                        if page not in chunk_metadata['pages']:
                            chunk_metadata['pages'].append(page)
                    if chunk_idx < len(chunks):
                        chunks[chunk_idx]['content'] += chunk_content
                        chunks[chunk_idx]['metadata']['elements'].extend(chunk_metadata['elements'])
                        chunks[chunk_idx]['metadata']['pages'].extend(chunk_metadata['pages'])
                    else:
                        chunks.append({
                            'id': str(uuid.uuid4()),
                            'content': chunk_content,
                            'metadata': chunk_metadata
                        })
                    chunk_idx += 1
            except Exception as e:
                print(f"Error in semantic grouping: {e}")

        if current_chunk['content']:
            chunks.append(current_chunk)

        return chunks

# Example usage
if __name__ == "__main__":
    chunker = PDFChunker("app\data\HR Law English.pdf")
    
    # Semantic Section-Based Chunking
    # semantic_chunks = chunker.semantic_section_based_chunking()
    semantic_chunks = chunker.element_based_chunking()
    print("Semantic Section-Based Chunks:")
    print(f"Total chunks: {len(semantic_chunks)}")
    # print(semantic_chunks)
    # Write chunks to a file
    with open("app/data/semantic_chunks_output.txt", "w", encoding="utf-8") as file:
        for chunk in semantic_chunks:
            file.write(f"ID: {chunk['id']}\n")
            file.write(f"Content:\n{chunk['content']}\n")
            file.write(f"Metadata: {chunk['metadata']}\n")
            file.write("\n" + "="*80 + "\n\n")
    # for chunk in semantic_chunks:
    #     print(f"ID: {chunk['id']}\nContent: {chunk['content'][:100]}...\nMetadata: {chunk['metadata']}\n")
    
    # Element-Based Chunking
    # element_chunks = chunker.element_based_chunking()
    # print("Element-Based Chunks:")
    # for chunk in element_chunks:
    #     print(f"ID: {chunk['id']}\nContent: {chunk['content'][:100]}...\nMetadata: {chunk['metadata']}\n")
    
    # # Hybrid Chunking
    # hybrid_chunks = chunker.hybrid_chunking()
    # print("Hybrid Chunks:")
    # for chunk in hybrid_chunks:
    #     print(f"ID: {chunk['id']}\nContent: {chunk['content'][:100]}...\nMetadata: {chunk['metadata']}\n")


    
    # Chunking mechanism types
    # ['sentencse based chunking','sentence based with overlaping','semantic section based chunking',
    #   'paragraph based chunking','fixed token sized chunking']
    # 
    #     
    ###