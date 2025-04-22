from .regex_text_chunker import RegexTextChunker
from .semantic_sentence_chunker import SemanticSentenceChunker
# from .langchain_chunker import LangChainChunker
# from .llama_chunker import LlamaChunker

class TextChunkingManager:
    def __init__(self):
        self.chunkers = {
            "regex": RegexTextChunker(),
            "semantic": SemanticSentenceChunker(),
            # "langchain_chars": LangChainChunker(),
            # "langchain_rec": LangChainChunker(),
            # "langchain_tokens": LangChainChunker(),
            # "langchain_md": LangChainChunker(),
            # "llama_rec": LlamaChunker(),
            # "llama_tokens": LlamaChunker(),
            # "llama_words": LlamaChunker(),
        }

    def chunk_text(self, mech: str, text: str, **kwargs):
        if mech == "regex":
            return self.chunkers[mech].chunk_text(
                text,
                kwargs["pattern"],
                int(kwargs.get("max_tokens")),
                int(kwargs.get("overlap")),
            )
        
        if mech == "semantic":
            return self.chunkers[mech].chunk_by_sentences(
                text,
                int(kwargs.get("max_tokens")),
                float(kwargs.get("sim_threshold")),
                int(kwargs.get("overlap")),
            )
        
        # if mech.startswith("langchain_"):
        #     method = mech.split("_", 1)[1]
        #     return self.chunkers[mech].chunk(text, method)
        
        # if mech.startswith("llama_"):
        #     method = mech.split("_", 1)[1]
        #     if method not in ["rec", "tokens"]:
        #         raise ValueError(f"Unknown Llama method: {method}")
        #     return self.chunkers[mech].chunk(text, method)

        raise ValueError(f"Unsupported mechanism: {mech}")