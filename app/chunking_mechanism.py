import re
import nltk
from sentence_transformers import SentenceTransformer, util


class RegexTextChunker:
    def __init__(self):
        pass

    def chunk_text(self, text, pattern, max_tokens=100, overlap_tokens=2):
        chunks = []
        chunk_index = 0
        try:
            regex = re.compile(pattern)
        except re.error as e:
            print(f"Invalid regex pattern: {pattern}")
            raise ValueError(f"Invalid regex pattern: {pattern}") from e

        try:
            matches = list(regex.finditer(text))
        except Exception as e:
            print(f"Error while finding matches with the regex: {e}")
            raise RuntimeError("Failed to find matches with the provided regex.") from e

        current_pos = 0
        previous_chunk = ""
        try:
            for i, match in enumerate(matches + [None]):
                if match:
                    start, end = match.start(), match.end()
                else:
                    start, end = len(text), len(text)

                segment = text[current_pos:start].strip()

                if segment:
                    try:
                        token_count = TextChunkResizer().count_tokens(segment)
                    except Exception as e:
                        print(f"Error while counting tokens in segment: {e}")
                        raise RuntimeError("Failed to count tokens in the segment.") from e

                    if token_count <= max_tokens:
                        try:
                            chunk_content = (previous_chunk + " ." + segment).strip()
                            chunk_tokens = TextChunkResizer().count_tokens(chunk_content)
                        except Exception as e:
                            print(f"Error while preparing chunk content: {e}")
                            raise RuntimeError("Failed to prepare chunk content.") from e

                        chunks.append({
                            "content": chunk_content,
                            "tokens": chunk_tokens,
                            "index": chunk_index
                        })
                        chunk_index += 1

                        previous_chunk = ' '.join(segment.split()[-overlap_tokens:])
                    else:
                        try:
                            sub_chunks = TextChunkResizer().split_large_chunk(segment, max_tokens, chunk_index, overlap_tokens)
                        except Exception as e:
                            print(f"Error while splitting large chunk: {e}")
                            raise RuntimeError("Failed to split large chunk.") from e

                        chunks.extend(sub_chunks)
                        chunk_index += len(sub_chunks)

                        previous_chunk = ' '.join(sub_chunks[-1]["content"].split()[-overlap_tokens:])

                current_pos = end
        except Exception as e:
            print(f"Unexpected error during chunking: {e}")
            raise RuntimeError("An unexpected error occurred during chunking.") from e

        return chunks


class SemanticSentenceChunker:
    def __init__(self):
        try:
            self.model = SentenceTransformer("sentence-transformers/all-mpnet-base-v2")
            self.tokenizer = self.model.tokenizer
        except Exception as e:
            print(f"Error initializing SentenceTransformer model: {e}")
            raise RuntimeError("Failed to initialize SentenceTransformer model.") from e

    def split_into_sentences(self, text):
        try:
            return nltk.sent_tokenize(text)
        except Exception as e:
            print(f"Error splitting text into sentences: {e}")
            raise RuntimeError("Failed to split text into sentences.") from e

    def count_tokens(self, text):
        try:
            return len(self.tokenizer.tokenize(text))
        except Exception as e:
            print(f"Error counting tokens: {e}")
            raise RuntimeError("Failed to count tokens.") from e

    def chunk_by_sentences(self, file_content, max_tokens=384, sim_threshold=0.7, overlap=2):
        try:
            sentences = self.split_into_sentences(file_content)
            print(f"Total sentences: {len(sentences)}")
            if len(sentences) == 0:
                print("No sentences found in the provided text.")
            chunks = self.merge_sentences_with_overlap(sentences, max_tokens=max_tokens,
                                                       sim_threshold=sim_threshold, overlap=overlap)
            return chunks
        except Exception as e:
            print(f"Error during sentence chunking: {e}")
            raise RuntimeError("Failed to chunk sentences.") from e

    def merge_sentences_with_overlap(self, sentences, max_tokens=384, sim_threshold=0.7, overlap=1):
        try:
            embeddings = self.model.encode(sentences, convert_to_tensor=True)
        except Exception as e:
            print(f"Error encoding sentences: {e}")
            raise RuntimeError("Failed to encode sentences.") from e

        chunks = []
        current_chunk = [sentences[0]]
        try:
            current_tokens = self.count_tokens(sentences[0])
        except Exception as e:
            print(f"Error counting tokens for the first sentence: {e}")
            raise RuntimeError("Failed to count tokens for the first sentence.") from e

        chunk_index = 0
        print(f"max_tokens: {max_tokens}, sim_threshold: {sim_threshold}, overlap: {overlap}")
        try:
            for i in range(1, len(sentences)):
                try:
                    similarity = util.cos_sim(embeddings[i - 1], embeddings[i]).item()
                except Exception as e:
                    print(f"Error calculating similarity: {e}")
                    raise RuntimeError("Failed to calculate similarity.") from e

                sentence = sentences[i]
                try:
                    sentence_tokens = self.count_tokens(sentence)
                except Exception as e:
                    print(f"Error counting tokens for sentence: {e}")
                    raise RuntimeError("Failed to count tokens for sentence.") from e

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
                    current_chunk = current_chunk[-overlap:] + [sentence] if overlap > 0 else [sentence]
                    current_tokens = sum(self.count_tokens(s) for s in current_chunk)

            if current_chunk:
                chunks.append({
                    "content": " ".join(current_chunk),
                    "tokens": current_tokens,
                    "index": chunk_index
                })
        except Exception as e:
            print(f"Error during sentence merging: {e}")
            raise RuntimeError("Failed to merge sentences.") from e

        return chunks


class TextChunkResizer:
    def __init__(self):
        pass

    def count_tokens(self, text):
        try:
            return len(re.findall(r'\w+|[^\w\s]', text))
        except Exception as e:
            print(f"Error counting tokens in text: {e}")
            raise RuntimeError("Failed to count tokens in text.") from e

    def split_large_chunk(self, text, max_tokens, start_index, overlap_tokens):
        try:
            words = text.split()
        except Exception as e:
            print(f"Error splitting text into words: {e}")
            raise RuntimeError("Failed to split text into words.") from e

        chunks = []
        current_chunk = []
        current_token_count = 0

        try:
            for word in words:
                try:
                    word_token_count = self.count_tokens(word)
                except Exception as e:
                    print(f"Error counting tokens for word: {e}")
                    raise RuntimeError("Failed to count tokens for word.") from e

                if current_token_count + word_token_count > max_tokens:
                    chunks.append({
                        "content": ' '.join(current_chunk),
                        "tokens": current_token_count,
                        "index": start_index
                    })
                    start_index += 1
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
        except Exception as e:
            print(f"Error during large chunk splitting: {e}")
            raise RuntimeError("Failed to split large chunk.") from e

        return chunks


class TextChunkingManager:
    def __init__(self):
        self.chunkers = {
            "regex": RegexTextChunker,
            "semantic": SemanticSentenceChunker
        }

    def chunk_text(self, mechanism_type, parameters):
        if mechanism_type not in self.chunkers:
            raise ValueError(f"Unsupported mechanism type: {mechanism_type}")

        chunker_class = self.chunkers[mechanism_type]
        try:
            chunker = chunker_class()
        except Exception as e:
            print(f"Error initializing chunker: {e}")
            raise RuntimeError("Failed to initialize chunker.") from e

        try:
            if mechanism_type == "regex":
                text = parameters.get("file_content", "")
                pattern = parameters.get("pattern", "")
                max_tokens = int(parameters.get("max_tokens", 1000))
                overlap_tokens = int(parameters.get("overlap_tokens", 100))
                return chunker.chunk_text(text, pattern, max_tokens, overlap_tokens)

            elif mechanism_type == "semantic":
                file_content = parameters.get("file_content", "")
                max_tokens = int(parameters.get("max_tokens", 384))
                sim_threshold = float(parameters.get("sim_threshold", 0.7))
                overlap = int(parameters.get("overlap", 2))
                return chunker.chunk_by_sentences(file_content, max_tokens, sim_threshold, overlap)
        except Exception as e:
            print(f"Error during text chunking: {e}")
            raise RuntimeError("Failed to chunk text.") from e

    @staticmethod
    def main():
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
        except Exception as e:
            print(f"Unexpected error: {e}")


if __name__ == "__main__":
    TextChunkingManager.main()