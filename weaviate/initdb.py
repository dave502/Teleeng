# pip install weaviate-client

import weaviate
import json
import os

WEAVIATE_URL = os.environ.get("WEAVIATE_URL") or "http://localhost:8081"
WEAVIATE_API_KEY = os.environ.get("WEAVIATE_API_KEY") or "key1"
OPEN_AI_KEY = os.environ.get("OPEN_AI_KEY")

class WeaviateDB():
    def __init__(self):

        self.client = weaviate.Client(
            url = WEAVIATE_URL,  # Replace with your endpoint
            auth_client_secret=weaviate.AuthApiKey(api_key=WEAVIATE_API_KEY),  # Replace w/ your Weaviate instance API key
            additional_headers = {
                "X-OpenAI-Api-Key": OPEN_AI_KEY  # Replace with your inference API key
            }
        )

        class_obj = {
            "class": "User",
            "vectorizer": "text2vec-openai",  # If set to "none" you must always provide vectors yourself. Could be any other "text2vec-*" also.
            "moduleConfig": {
                "text2vec-openai": {},
                "generative-openai": {}  # Ensure the `generative-openai` module is used for generative queries
            }
        }

        self.client.schema.create_class(class_obj)

    def add_user(self, user: dict):
        self.client.batch.configure(batch_size=100)  # Configure batch
        with  self.client.batch as batch:  # Initialize a batch process
        #    for i, d in enumerate(users):  # Batch import data
        #        print(f"importing question: {i+1}")
            properties = {
                "name": user["Name"],
                "age": user["Age"],
                "city": user["City"],
            }
            batch.add_data_object(
                data_object=properties,
                class_name="User"
            )


db = WeaviateDB()

resp = requests.get('https://raw.githubusercontent.com/weaviate-tutorials/quickstart/main/data/jeopardy_tiny.json')
user: dict = json.loads(resp.text)  # Load data

db.add_user(user)

