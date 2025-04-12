import os
import vertexai
from vertexai.generative_models import GenerativeModel

# Initialize Vertex AI
project_id = os.getenv("GCP_PROJECT_ID")
location = os.getenv("GCP_LOCATION", "us-central1")
vertexai.init(project=project_id, location=location)

# Test with a simple prompt
model = GenerativeModel("gemini-2.0-flash-lite-001")
response = model.generate_content("Hello, world!")
print(response.text)
