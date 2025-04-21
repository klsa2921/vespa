import requests
import json
# from properties.constants import env
# MODEL_API_URL=env.CHAT_MODEL_API_URL+"/v1/chat/completions"
MODEL_API_URL="http://192.168.1.6:3009/v1/chat/completions"
# MODEL_NAME=env.CHAT_MODEL_NAME
MODEL_NAME="llama3.2:1b"

class ChatModel:
    def __init__(self, api_url, model):
        self.api_url = api_url
        self.model = model

    def chat_with_model(self, content):
        try:
            # logger.info("Sending request to model for product ID: %s", product_id)
            prompt = f"""
Generate as many questions and answers as possible based on the following text:

\"\"\"{content}\"\"\"

Provide the response in **JSON format** only, like this:

[
    {{
        "question": "What is the main topic?",
        "answer": "The main topic is..."
    }},
    {{
        "question": "What are the key points?",
        "answer": "The key points are..."
    }}
]

- All answers must be based solely on the provided text.
- Do not include any explanations or text not found in the original content.
- Only output the JSON array.
"""
                        
            content_list = [{"type": "text", "text": prompt}]
            
            payload = {
                "model": self.model,
                "messages": [{"role": "user", "content": content_list}],
                "stream": False
            }

            response = requests.post(self.api_url, headers={"Content-Type": "application/json"}, data=json.dumps(payload))

            if response.status_code == 200:
                response_json = response.json()
                return response_json.get('choices', [{}])[0].get('message', {}).get('content', '')
            else:
                return f"Error: {response.status_code}, {response.text}"
        except Exception as e:
            return f"Error processing image: {str(e)}"

class QaGenerator:

    def __init__(self, model):
        self.model = model

    def generate_qa(self, text):
        # Placeholder for the actual implementation
        # This should call the model to generate questions and answers based on the text
        chatModel = ChatModel(MODEL_API_URL, MODEL_NAME)
        response = chatModel.chat_with_model(text)
        print("Response from model:", response)
        return response
    



if __name__ == "__main__":
    #  Example usage
    responses=[]
    qa_generator = QaGenerator(MODEL_NAME)
    text = """If deforestation continues at its current rate, the future consequences will be dire. One of the 
most immediate and severe impacts will be the loss of biodiversity. Forests are home to more 
than half of the world’s terrestrial species, and their destruction leads to the extinction of 
countless plants, animals, and insects. As forests vanish, entire ecosystems collapse, disrupting 
the delicate web of life that relies on them. This will have cascading effects on food chains, 
potentially leading to the collapse of vital species that humans rely on for food, medicine, and 
raw materials"""
    
    qa_response = qa_generator.generate_qa(text)
    responses.append(qa_response)
    # print(qa_response)