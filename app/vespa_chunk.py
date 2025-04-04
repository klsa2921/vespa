import nltk
from sentence_transformers import SentenceTransformer, util

# nltk.download('punkt')
# nltk.download('punkt_tab')


model = SentenceTransformer("sentence-transformers/all-MiniLM-L6-v2")
max_tokens = 384
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
