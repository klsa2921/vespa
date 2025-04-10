import nltk
from sentence_transformers import SentenceTransformer, util
from transformers import BertTokenizer
import pdfplumber


nltk.download('punkt')
nltk.download('punkt_tab')


# model = SentenceTransformer("sentence-transformers/all-MiniLM-L6-v2")
model = SentenceTransformer("sentence-transformers/all-mpnet-base-v2")
max_tokens = 784
similarity_threshold = 0.7
tokenizer = model.tokenizer


def split_sentences(text):
    return nltk.sent_tokenize(text)


def token_len(text):
    return len(tokenizer.tokenize(text))


def semantic_merge(sentences, max_tokens=384, sim_threshold=0.7):
    embeddings = model.encode(sentences, convert_to_tensor=True)
    chunks = []
    current_chunk = [sentences[0]]
    current_tokens = token_len(sentences[0])

    for i in range(1, len(sentences)):
        similarity = util.cos_sim(embeddings[i - 1], embeddings[i]).item()
        sentence = sentences[i]
        sentence_tokens = token_len(sentence)

        if (similarity > sim_threshold and current_tokens + sentence_tokens <= max_tokens):
            current_chunk.append(sentence)
            current_tokens += sentence_tokens
        else:
            chunks.append(" ".join(current_chunk))
            current_chunk = [sentence]
            current_tokens = sentence_tokens

    if current_chunk:
        chunks.append(" ".join(current_chunk))

    return chunks


def semantic_merge_with_overlap(sentences, max_tokens=384, sim_threshold=0.7, overlap=1):
    embeddings = model.encode(sentences, convert_to_tensor=True)
    chunks = []
    current_chunk = [sentences[0]]
    current_tokens = token_len(sentences[0])

    for i in range(1, len(sentences)):
        similarity = util.cos_sim(embeddings[i - 1], embeddings[i]).item()
        sentence = sentences[i]
        sentence_tokens = token_len(sentence)

        if similarity > sim_threshold and current_tokens + sentence_tokens <= max_tokens:
            current_chunk.append(sentence)
            current_tokens += sentence_tokens
        else:
            chunks.append(" ".join(current_chunk))
            # Add overlap (last N sentences from current chunk)
            current_chunk = current_chunk[-overlap:] + [sentence] if overlap > 0 else [sentence]
            current_tokens = sum(token_len(s) for s in current_chunk)

    if current_chunk:
        chunks.append(" ".join(current_chunk))

    return chunks


def main():
    long_text = """
        Amazon is a global e-commerce company. It was founded by Jeff Bezos. 
        The company started as an online bookstore. It later expanded to sell electronics and other goods. 
        Amazon Web Services is its cloud arm. AWS dominates cloud computing globally.
        """

    sentences = split_sentences(long_text)
    chunks = semantic_merge_with_overlap(sentences, max_tokens=max_tokens, sim_threshold=similarity_threshold,
                                         overlap=2)

    for i, chunk in enumerate(chunks):
        print(f"\n🔹 Chunk {i + 1}:\n{chunk}")


if __name__ == "__main__":
    main()


def generate_chunks(file_content):
    """
    Generate semantic chunks from the file content.
    :param file_content: str, the content of the file to be chunked
    :return: list of semantic chunks
    """
    sentences = split_sentences(file_content)
    print(f"Total sentences: {len(sentences)}")
    if len(sentences) == 0:
        print("No sentences found in the provided text.")
    chunks = semantic_merge_with_overlap(sentences, max_tokens=max_tokens, sim_threshold=similarity_threshold,
                                         overlap=2)

    return chunks


def is_title(text_block):
    """Identify if a text block is a title based on font size and position."""
    return text_block["size"] > 16  # Example: Titles have larger font size

def is_heading(text_block):
    """Identify if a text block is a heading based on font size and boldness."""
    return text_block["size"] > 12 and "bold" in text_block["fontname"].lower()

def extract_structured_content(pdf_path):
    """Extract titles, headings, and paragraphs from a PDF."""
    structured_content = []
    current_section = {"title": None, "heading": None, "paragraphs": []}

    with pdfplumber.open(pdf_path) as pdf:
        for page in pdf.pages:
            # Extract text with character-level details
            chars = page.chars
            # Group characters into text blocks (approximating lines)
            text_blocks = page.extract_text_lines(return_chars=False)

            for block in text_blocks:
                print(block)
                # Create a simplified text block dictionary
                text_block = {
                    "text": block["text"].strip(),
                    "size": block["size"],  # Font size
                    "fontname": block["fontname"],  # Font name for boldness check
                }

                if is_title(text_block):
                    # Save the previous section if it has content
                    if current_section["paragraphs"] or current_section["heading"]:
                        structured_content.append(current_section)
                    # Start a new section with the title
                    current_section = {"title": text_block["text"], "heading": None, "paragraphs": []}
                elif is_heading(text_block):
                    # Save paragraphs under the previous heading, if any
                    if current_section["paragraphs"]:
                        structured_content.append(current_section)
                        current_section = {
                            "title": current_section["title"],
                            "heading": text_block["text"],
                            "paragraphs": []
                        }
                    else:
                        current_section["heading"] = text_block["text"]
                else:
                    # Treat as paragraph
                    if text_block["text"]:  # Ignore empty lines
                        current_section["paragraphs"].append(text_block["text"])

        # Append the final section
        if current_section["paragraphs"] or current_section["heading"]:
            structured_content.append(current_section)

    return structured_content

def chunk_large_section(title, heading, paragraphs):
    """Chunk a section into smaller parts if it exceeds max_tokens."""
    chunks = []
    
    # Combine title and heading for context
    context = ""
    if title:
        context += title + "\n"
    if heading:
        context += heading + "\n"
    
    context_tokens = len(tokenizer.tokenize(context))
    remaining_budget = max_tokens - context_tokens

    current_chunk = [context]
    current_tokens = context_tokens

    for paragraph in paragraphs:
        para_tokens = len(tokenizer.tokenize(paragraph))
        if current_tokens + para_tokens <= max_tokens:
            current_chunk.append(paragraph)
            current_tokens += para_tokens
        else:
            # Save the current chunk and start a new one
            chunks.append("\n".join(current_chunk))
            current_chunk = [context, paragraph]
            current_tokens = context_tokens + para_tokens

    # Append the last chunk
    if current_chunk:
        chunks.append("\n".join(current_chunk))

    return chunks

def chunk_pdf(pdf_path):
    """Main function to chunk the PDF into token-limited sections."""
    all_chunks = []
    
    # Step 1: Extract structured content
    structured_content = extract_structured_content(pdf_path)
    
    # Step 2: Chunk each section
    for section in structured_content:
        title = section["title"]
        heading = section["heading"]
        paragraphs = section["paragraphs"]

        # If no paragraphs, just add the title/heading as a chunk
        if not paragraphs:
            chunk = (title or "") + "\n" + (heading or "")
            if chunk.strip() and len(tokenizer.tokenize(chunk)) <= max_tokens:
                all_chunks.append(chunk.strip())
            continue

        # Chunk the section with paragraphs
        chunks = chunk_large_section(title, heading, paragraphs)
        all_chunks.extend(chunks)

    return all_chunks