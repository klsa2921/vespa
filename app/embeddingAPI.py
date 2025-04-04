from flask import Flask, request, jsonify
from sentence_transformers import SentenceTransformer
import logging


class EmbeddingAPI:
    def __init__(self, model_name='all-MiniLM-L6-v2', host='0.0.0.0', port=5000):
        """Initialize the Embedding API with a specified model."""
        self.app = Flask(__name__)
        self.model = SentenceTransformer(model_name)
        self.host = host
        self.port = port

        # Set up logging
        logging.basicConfig(level=logging.INFO)
        self.logger = logging.getLogger(__name__)

        # Register API routes
        self._setup_routes()

    def _setup_routes(self):
        """Set up API endpoints."""

        @self.app.route('/embed', methods=['POST'])
        def get_embedding():
            try:
                # Expect JSON data with 'text' field
                data = request.get_json()
                if not data or 'text' not in data:
                    return jsonify({
                        'error': 'Missing "text" field in JSON request'
                    }), 400

                text = data['text']
                embedding = self.model.encode(text, convert_to_tensor=False).tolist()

                return jsonify({
                    'embedding': embedding,
                    'dimensions': len(embedding),
                    'status': 'success'
                })

            except Exception as e:
                self.logger.error(f"Error processing request: {str(e)}")
                return jsonify({
                    'error': str(e),
                    'status': 'error'
                }), 500

    def run(self):
        """Start the Flask server."""
        self.logger.info(f"Starting Embedding API on {self.host}:{self.port}")
        self.app.run(host=self.host, port=self.port, debug=False)


# Example usage
if __name__ == "__main__":
    # Create and run the API server
    embedding_api = EmbeddingAPI(
        model_name='all-MiniLM-L6-v2',  # or 'all-mpnet-base-v2' for 768-dim
        host='0.0.0.0',
        port=5000
    )
    embedding_api.run()
