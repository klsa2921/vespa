import nltk
from sentence_transformers import SentenceTransformer, util

class SemanticSentenceChunker:
    def __init__(self):
        self.model = SentenceTransformer("sentence-transformers/all-mpnet-base-v2")

    def chunk_by_sentences(self, text: str, max_tokens=384, sim_threshold=0.7, overlap=2):
        sentences = nltk.sent_tokenize(text)
        if not sentences:
            return []

        embeddings = self.model.encode(sentences, convert_to_tensor=True)
        chunks, current = [], [sentences[0]]
        tok_count = len(self.model.tokenizer.tokenize(sentences[0]))
        idx = 0

        for i in range(1, len(sentences)):
            sim = util.cos_sim(embeddings[i-1], embeddings[i]).item()
            sent = sentences[i]
            s_tok = len(self.model.tokenizer.tokenize(sent))

            if sim > sim_threshold and tok_count + s_tok <= max_tokens:
                current.append(sent)
                tok_count += s_tok
            else:
                chunks.append({"content": " ".join(current), "tokens": tok_count, "index": idx})
                idx += 1
                current = (current[-overlap:] if overlap else []) + [sent]
                tok_count = sum(len(self.model.tokenizer.tokenize(s)) for s in current)

        if current:
            chunks.append({"content": " ".join(current), "tokens": tok_count, "index": idx})

        return chunks
