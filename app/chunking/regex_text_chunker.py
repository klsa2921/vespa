import re
from .text_chunk_resizer import TextChunkResizer

class RegexTextChunker:
    def __init__(self):
        self.resizer = TextChunkResizer()

    def chunk_text(self, text: str, pattern: str, max_tokens=100, overlap=2):
        regex = re.compile(pattern)
        matches = list(regex.finditer(text)) + [None]

        chunks, prev_overlap, idx, pos = [], "", 0, 0
        for match in matches:
            start = match.start() if match else len(text)
            segment = text[pos:start].strip()
            pos = match.end() if match else start

            if not segment:
                continue

            combined = f"{prev_overlap} {segment}".strip()
            tok_count = self.resizer.count_tokens(combined)

            if tok_count <= max_tokens:
                chunks.append({"content": combined, "tokens": tok_count, "index": idx})
                prev_overlap = " ".join(segment.split()[-overlap:])
                idx += 1
            else:
                sub = self.resizer.split_large_chunk(segment, max_tokens, idx, overlap)
                chunks.extend(sub)
                idx += len(sub)
                prev_overlap = " ".join(sub[-1]["content"].split()[-overlap:])

        return chunks
