from langchain.text_splitter import (
    CharacterTextSplitter,
    RecursiveCharacterTextSplitter,
    TokenTextSplitter,
    MarkdownTextSplitter,
)

class LangChainChunker:
    def __init__(self, chunk_size=1000, chunk_overlap=200):
        self.splitters = {
            "chars": CharacterTextSplitter(chunk_size=chunk_size, chunk_overlap=chunk_overlap),
            "rec_chars": RecursiveCharacterTextSplitter(chunk_size=chunk_size, chunk_overlap=chunk_overlap),
            "tokens": TokenTextSplitter(chunk_size=chunk_size, chunk_overlap=chunk_overlap),
            "markdown": MarkdownTextSplitter(chunk_size=chunk_size, chunk_overlap=chunk_overlap),
        }

    def chunk(self, text: str, method: str):
        if method not in self.splitters:
            raise ValueError(f"Unknown LangChain method: {method}")
        return self.splitters[method].split_text(text)
