import re
import nltk
from sentence_transformers import SentenceTransformer, util


class RegexTextChunker:
    def __init__(self):
        pass

    def chunk_text(self, text, pattern, max_tokens=100, overlap_tokens=2):
        """
        Chunk text based on a regex pattern, ensuring chunks do not exceed max_tokens,
        and include overlap between chunks.

        Parameters:
        - text: The full text that needs to be chunked.
        - pattern: Regex pattern to match the section or article boundaries.
        - max_tokens: Maximum number of tokens allowed in each chunk (default: 1000).
        - overlap_tokens: Number of tokens to overlap between consecutive chunks (default: 100).

        Returns:
        - A list of dictionaries where each dictionary represents a chunk with 'content', 'tokens', and 'index'.
        """
        chunks = []
        chunk_index = 0

        regex = re.compile(pattern)

        matches = list(regex.finditer(text))

        current_pos = 0
        previous_chunk = ""

        for i, match in enumerate(matches + [None]):  
            if match:
                start, end = match.start(), match.end()
            else:
                start, end = len(text), len(text)  

            segment = text[current_pos:start].strip()

            if segment:
                token_count = TextChunkResizer().count_tokens(segment)

                if token_count <= max_tokens:
                    chunk_content = (previous_chunk + " ." + segment).strip()
                    chunk_tokens = TextChunkResizer().count_tokens(chunk_content)

                    chunks.append({
                        "content": chunk_content,
                        "tokens": chunk_tokens,
                        "index": chunk_index
                    })
                    chunk_index += 1

                    previous_chunk = ' '.join(segment.split()[-overlap_tokens:])
                else:
                    sub_chunks = TextChunkResizer().split_large_chunk(segment, max_tokens, chunk_index, overlap_tokens)
                    chunks.extend(sub_chunks)
                    chunk_index += len(sub_chunks)

                    previous_chunk = ' '.join(sub_chunks[-1]["content"].split()[-overlap_tokens:])

            current_pos = end

        return chunks


class SemanticSentenceChunker:
    def __init__(self):
        self.model = SentenceTransformer("sentence-transformers/all-mpnet-base-v2")
        self.tokenizer = self.model.tokenizer

    def split_into_sentences(self, text):
        return nltk.sent_tokenize(text)

    def count_tokens(self, text):
        return len(self.tokenizer.tokenize(text))

    def chunk_by_sentences(self, file_content, max_tokens=384, sim_threshold=0.7,overlap=2):
        """
        Generate semantic chunks from the file content.
        :param file_content: str, the content of the file to be chunked
        :return: list of semantic chunks
        """
        sentences = self.split_into_sentences(file_content)
        print(f"Total sentences: {len(sentences)}")
        if len(sentences) == 0:
            print("No sentences found in the provided text.")
        chunks = self.merge_sentences_with_overlap(sentences, max_tokens=max_tokens,
                                                   sim_threshold=sim_threshold, overlap=overlap)

        return chunks

    def merge_sentences_with_overlap(self, sentences, max_tokens=384, sim_threshold=0.7, overlap=1):
        embeddings = self.model.encode(sentences, convert_to_tensor=True)
        chunks = []
        current_chunk = [sentences[0]]
        current_tokens = self.count_tokens(sentences[0])
        chunk_index = 0
        print(f"max_tokens: {max_tokens}, sim_threshold: {sim_threshold}, overlap: {overlap}")
        for i in range(1, len(sentences)):
            similarity = util.cos_sim(embeddings[i - 1], embeddings[i]).item()
            sentence = sentences[i]
            sentence_tokens = self.count_tokens(sentence)

            if similarity > sim_threshold and current_tokens + sentence_tokens <= max_tokens:
                current_chunk.append(sentence)
                current_tokens += sentence_tokens
            else:
                chunks.append({
                    "content": " ".join(current_chunk),
                    "tokens": current_tokens,
                    "index": chunk_index
                })
                chunk_index += 1
                # Add overlap (last N sentences from current chunk)
                current_chunk = current_chunk[-overlap:] + [sentence] if overlap > 0 else [sentence]
                current_tokens = sum(self.count_tokens(s) for s in current_chunk)

        if current_chunk:
            chunks.append({
                "content": " ".join(current_chunk),
                "tokens": current_tokens,
                "index": chunk_index
            })

        return chunks


class TextChunkResizer:
    def __init__(self):
        pass

    def count_tokens(self, text):
        """
        Count the number of tokens in the text.
        """
        return len(re.findall(r'\w+|[^\w\s]', text))

    def split_large_chunk(self, text, max_tokens, start_index, overlap_tokens):
        """
        Split a chunk that exceeds the max_tokens limit into smaller chunks with overlap.

        Parameters:
        - text: The text to split.
        - max_tokens: Maximum number of tokens allowed in each chunk.
        - start_index: The starting index for the chunks.
        - overlap_tokens: Number of tokens to overlap between consecutive chunks.

        Returns:
        - A list of dictionaries where each dictionary represents a chunk with 'content', 'tokens', and 'index'.
        """
        words = text.split()
        chunks = []
        current_chunk = []
        current_token_count = 0

        for word in words:
            word_token_count = self.count_tokens(word)
            if current_token_count + word_token_count > max_tokens:
                # If the current chunk exceeds max_tokens, store the current chunk and start a new one
                chunks.append({
                    "content": ' '.join(current_chunk),
                    "tokens": current_token_count,
                    "index": start_index
                })
                start_index += 1

                # Start a new chunk with overlap
                current_chunk = current_chunk[-overlap_tokens:] + [word]
                current_token_count = self.count_tokens(' '.join(current_chunk))
            else:
                current_chunk.append(word)
                current_token_count += word_token_count

        if current_chunk:
            chunks.append({
                "content": ' '.join(current_chunk),
                "tokens": current_token_count,
                "index": start_index
            })

        return chunks


class TextChunkingManager:
    def __init__(self):
        self.chunkers = {
            "regex": RegexTextChunker,
            "semantic": SemanticSentenceChunker
        }

    def chunk_text(self, mechanism_type, parameters):
        """
        Chunk text based on the specified mechanism type and parameters.

        Parameters:
        - mechanism_type: str, the type of chunking mechanism ("regex" or "semantic").
        - parameters: dict, parameters required for the chunking mechanism.

        Returns:
        - A list of chunks generated by the specified chunking mechanism.
        """
        if mechanism_type not in self.chunkers:
            raise ValueError(f"Unsupported mechanism type: {mechanism_type}")

        chunker_class = self.chunkers[mechanism_type]
        chunker = chunker_class()


        if mechanism_type == "regex":
            text = parameters.get("file_content", "")
            pattern = parameters.get("pattern", "")
            max_tokens = parameters.get("max_tokens", 1000)
            overlap_tokens = parameters.get("overlap_tokens", 100)
            return chunker.chunk_text(text, pattern, max_tokens, overlap_tokens)

        elif mechanism_type == "semantic":
            file_content = parameters.get("file_content", "")
            max_tokens = parameters.get("max_tokens", 384)
            sim_threshold = parameters.get("sim_threshold", 0.7)
            overlap = parameters.get("overlap", 2)
            # print(f"max_tokens: {max_tokens}, sim_threshold: {sim_threshold}, overlap: {overlap}")
            return chunker.chunk_by_sentences(file_content, max_tokens, sim_threshold, overlap)

    @staticmethod
    def main():
        # Example JSON-like input
        # input_data = {
        #     "mechanism_type": "regex",
        #     "parameters": {
        #         "text": "This is a sample text. Section 1: Content of section 1. Section 2: Content of section 2.",
        #         "pattern": r"Section \d+:",
        #         "max_tokens": 50,
        #         "overlap_tokens": 5
        #     }
        # }

        input_data = {
            "mechanism_type": "semantic",
            "parameters": {
                "file_content": """
                    Deforestation is driven by a complex mix of agricultural expansion, urbanization, logging, and 
                    climate change. If left unaddressed, the consequences of this environmental crisis will be 
                    devastating, resulting in the loss of biodiversity, accelerating climate change, and disrupting 
                    ecosystems that are crucial for human survival. To prevent these future calamities, urgent action 
                    is needed to promote sustainable land-use practices, strengthen legal frameworks to prevent 
                    illegal logging, and implement large-scale reforestation projects to restore ecosystems. Only 
                    through collective global efforts can we mitigate the effects of deforestation and secure a more 
                    sustainable future for all
                    """,
                "max_tokens": 10,
                "sim_threshold": 0.7,
                "overlap": 2
            }
        }

        manager = TextChunkingManager()
        mechanism_type = input_data["mechanism_type"]
        parameters = input_data["parameters"]

        try:
            chunks = manager.chunk_text(mechanism_type, parameters)
            print("Generated Chunks:")
            for chunk in chunks:
                print(chunk)
        except ValueError as e:
            print(f"Error: {e}")


# Run the main method
if __name__ == "__main__":
    TextChunkingManager.main()