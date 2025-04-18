import re

class TextChunkResizer:
    def count_tokens(self, text: str) -> int:
        return len(re.findall(r'\w+|[^\w\s]', text))

    def split_large_chunk(self, text: str, max_tokens: int, start_index: int, overlap: int):
        words = text.split()
        chunks, current, count, idx = [], [], 0, start_index

        for w in words:
            w_count = self.count_tokens(w)
            if count + w_count > max_tokens:
                chunks.append({"content": " ".join(current), "tokens": count, "index": idx})
                idx += 1
                current = current[-overlap:] + [w]
                count = sum(self.count_tokens(t) for t in current)
            else:
                current.append(w)
                count += w_count

        if current:
            chunks.append({"content": " ".join(current), "tokens": count, "index": idx})
        return chunks
