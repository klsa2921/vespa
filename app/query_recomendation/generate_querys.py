import json

class QueryGenerator:
    def __init__(self, model):
        """
        Initialize the QueryGenerator with a model function.
        :param model: A callable that takes a chunk and returns a list of question-answer pairs.
        """
        self.model = model

    def generate_questions_and_answers(self, chunks):
        """
        Generate a JSON array of questions and answers for each chunk.
        :param chunks: A list of text chunks.
        :return: A list of chunks with appended question-answer pairs.
        """
        result = []
        for chunk in chunks:
            # Get the suggested questions and answers from the model
            qa_pairs = self.model(chunk)
            
            # Append the questions and answers to the chunk
            chunk_with_qa = {
                "chunk": chunk,
                "questions_and_answers": qa_pairs
            }
            result.append(chunk_with_qa)
        
        return result

# Example usage
def mock_model(chunk):
    """
    Mock model function for demonstration purposes.
    :param chunk: A text chunk.
    :return: A list of question-answer pairs.
    """
    return [
        {"question": f"What is the main idea of: {chunk[:30]}?", "answer": "This is a mock answer."},
        {"question": f"Can you summarize: {chunk[:30]}?", "answer": "This is another mock answer."}
    ]

if __name__ == "__main__":
    chunks = [
        "This is the first chunk of text.",
        "Here is another chunk of text for testing."
    ]
    
    generator = QueryGenerator(mock_model)
    result = generator.generate_questions_and_answers(chunks)
    
    # Print the result as a JSON string
    print(json.dumps(result, indent=2))