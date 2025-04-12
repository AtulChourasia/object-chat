# Object Chat - Talk to Inanimate Objects

This application allows users to chat with inanimate objects as if they have their own personalities and characteristics. The chatbot dynamically creates personas for objects and responds in character using Google's Vertex AI with the Gemini model.

## Features

- **Dynamic Object Personas**: Chat with any inanimate object and experience a unique personality
- **Conversational Interface**: Simple and intuitive UI for engaging with object personas
- **Uncensored Responses**: Uses Google's powerful Gemini model for creative, free-flowing conversations
- **Persona Consistency**: Objects maintain consistent personalities throughout conversations
- **Enterprise-Grade AI**: Uses Google Vertex AI for reliable, high-quality responses
- **Fallback Mechanism**: Includes template responses as backup

## Setup Instructions

### Prerequisites

- Python 3.7 or higher
- Google Cloud account with Vertex AI API enabled
- Internet connection for API access

### Installation

1. Clone this repository or download the files
2. Install the required dependencies:

```bash
pip install -r requirements.txt
```

3. Configure your Google Cloud credentials:
   - Set up a Google Cloud project with Vertex AI API enabled
   - Open the `.env` file and update the following values:
     ```
     GCP_PROJECT_ID=your-project-id
     GCP_LOCATION=us-central1  # or your preferred region
     ```
   - Authentication options:
     - Option 1: Use [Application Default Credentials](https://cloud.google.com/docs/authentication/application-default-credentials)
     - Option 2: Create a service account key and set the path in `.env`:
       ```
       GOOGLE_APPLICATION_CREDENTIALS=path/to/your/service-account-key.json
       ```

### Running the Application

1. Start the Flask server:

```bash
python app.py
```

2. Open your web browser and navigate to:

```
http://127.0.0.1:5000
```

## How to Use

1. Start a conversation with an object by typing: `Chat with [object name]`
   - For example: "Chat with a book" or "Chat with a lamp"
2. Continue the conversation by asking questions or making statements
3. Switch to a different object at any time by typing: `Chat with [new object name]`

## Customization

You can extend the application by:

- Adding predefined personas in the `object_personas` dictionary in `app.py`
- Modifying the UI in `templates/index.html`
- Implementing additional content filtering if needed

## Technical Details

- **Frontend**: HTML, CSS, JavaScript
- **Backend**: Flask (Python)
- **LLM Integration**: Hugging Face Inference API
- **Models Used**:
  - Persona Generation: `mistralai/Mistral-7B-Instruct-v0.2`
  - Chat Responses: `NousResearch/Nous-Hermes-2-Mixtral-8x7B-DPO` (uncensored model)
- **Fallback System**: Pre-written templates when API is unavailable

## Notes

- The application requires an internet connection to communicate with the Hugging Face API
- Response quality is excellent due to the use of large language models
- The application includes fallback template responses if the API is unavailable
- Using your own Hugging Face API key is recommended for higher rate limits
