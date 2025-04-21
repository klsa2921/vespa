from llama_index.text_splitter import (
    # RecursiveCharacterTextSplitter as LlamaRecursiveSplitter,
    TokenTextSplitter as LlamaTokenSplitter,
)

# from llama_index.text_splitter import TokenTextSplitter as LlamaTokenSplitter

class LlamaChunker:
    def __init__(self, chunk_size=600, chunk_overlap=64):
        self.splitters = {
            # "rec_chars": LlamaRecursiveSplitter(chunk_size=chunk_size, chunk_overlap=chunk_overlap),
            "tokens": LlamaTokenSplitter(chunk_size=chunk_size, chunk_overlap=chunk_overlap),
        }

    def chunk(self, text: str, method: str):
        if method not in self.splitters:
            raise ValueError(f"Unknown Llama method: {method}")
        return self.splitters[method].split_text(text)
