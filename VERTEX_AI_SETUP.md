# Setting Up Google Vertex AI for Object Chat

This guide provides detailed instructions for setting up Google Vertex AI to work with the Object Chat application.

## Prerequisites

1. A Google Cloud Platform (GCP) account
2. The `gcloud` CLI tool installed on your computer
3. Python 3.7 or higher
4. The required Python packages installed (see requirements.txt)

## Step 1: Create a Google Cloud Project

If you don't already have a GCP project:

1. Go to the [Google Cloud Console](https://console.cloud.google.com/)
2. Click on the project dropdown at the top of the page
3. Click "New Project"
4. Enter a name for your project and click "Create"
5. Note your Project ID, which you'll need later

## Step 2: Enable the Vertex AI API

1. In the Google Cloud Console, go to "APIs & Services" > "Library"
2. Search for "Vertex AI API"
3. Click on "Vertex AI API" in the results
4. Click "Enable"

## Step 3: Set Up Authentication

You have two options for authentication:

### Option A: Use Application Default Credentials (Recommended for Development)

1. Install the Google Cloud SDK if you haven't already: [https://cloud.google.com/sdk/docs/install](https://cloud.google.com/sdk/docs/install)
2. Open a terminal and run:

```bash
gcloud auth application-default login
```

3. Follow the prompts to log in with your Google account
4. This will create credentials that Vertex AI can use automatically

### Option B: Create a Service Account Key (Better for Production)

1. In the Google Cloud Console, go to "IAM & Admin" > "Service Accounts"
2. Click "Create Service Account"
3. Enter a name and description for the service account
4. Click "Create and Continue"
5. Add the "Vertex AI User" role to the service account
6. Click "Continue" and then "Done"
7. Find your new service account in the list, click the three dots menu, and select "Manage keys"
8. Click "Add Key" > "Create new key"
9. Choose JSON format and click "Create"
10. Save the downloaded key file to a secure location
11. Update your `.env` file with the path to this key file:

```
GOOGLE_APPLICATION_CREDENTIALS=/path/to/your-service-account-key.json
```

## Step 4: Configure Your Environment Variables

Update your `.env` file with the following:

```
# Google Cloud Project ID and Location
GCP_PROJECT_ID=your-project-id
GCP_LOCATION=us-central1

# Optional: Path to service account key file (if using Option B above)
# GOOGLE_APPLICATION_CREDENTIALS=/path/to/your-service-account-key.json

# Flask application secret key (used for sessions and CSRF protection)
SECRET_KEY=your-secret-key-change-this-in-production
```

Replace `your-project-id` with your actual GCP Project ID.

## Step 5: Verify Your Setup

1. Run the following Python code to verify your Vertex AI setup:

```python
import os
import vertexai
from vertexai.generative_models import GenerativeModel

# Initialize Vertex AI
project_id = os.getenv("GCP_PROJECT_ID")
location = os.getenv("GCP_LOCATION", "us-central1")
vertexai.init(project=project_id, location=location)

# Test with a simple prompt
model = GenerativeModel("gemini-1.0-pro")
response = model.generate_content("Hello, world!")
print(response.text)
```

If this works, your Vertex AI setup is correct.

## Troubleshooting

### Common Errors and Solutions

#### 1. Authentication Errors

**Error**: `google.auth.exceptions.DefaultCredentialsError: Could not automatically determine credentials.`

**Solution**: 
- Make sure you've run `gcloud auth application-default login`
- Or check that your `GOOGLE_APPLICATION_CREDENTIALS` environment variable is set correctly

#### 2. Permission Errors

**Error**: `google.api_core.exceptions.PermissionDenied: 403 Permission denied on resource project`

**Solution**:
- Ensure the Vertex AI API is enabled
- Check that your service account has the "Vertex AI User" role
- Verify you're using the correct project ID

#### 3. Quota or Billing Errors

**Error**: `google.api_core.exceptions.ResourceExhausted: 429 Quota exceeded for quota metric`

**Solution**:
- Make sure billing is enabled for your project
- Request a quota increase if needed

#### 4. Region Availability Errors

**Error**: `google.api_core.exceptions.InvalidArgument: 400 Model gemini-1.0-pro is not supported in location us-central1`

**Solution**:
- Change your `GCP_LOCATION` to a supported region (try "us-central1")
- Check the [Vertex AI documentation](https://cloud.google.com/vertex-ai/docs/generative-ai/learn/models) for model availability by region

#### 5. Module Import Errors

**Error**: `ImportError: No module named 'vertexai'`

**Solution**:
- Make sure you've installed the required packages: `pip install google-cloud-aiplatform`

## Additional Resources

- [Vertex AI Documentation](https://cloud.google.com/vertex-ai/docs)
- [Gemini API Documentation](https://cloud.google.com/vertex-ai/docs/generative-ai/model-reference/gemini)
- [Google Cloud Authentication Guide](https://cloud.google.com/docs/authentication)
