from flask import Flask, render_template, request, jsonify, redirect, url_for, flash, session
import os
from dotenv import load_dotenv
import re
import json
import random
import requests
import tempfile
from datetime import datetime, timedelta
from flask_login import LoginManager, login_user, logout_user, login_required, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from flask_wtf.csrf import CSRFProtect
from flask_session import Session
from flask_migrate import Migrate

# Import models and forms
from models import db, User, ChatSession, ChatMessage
from forms import LoginForm, RegistrationForm

# Load environment variables
load_dotenv()

# Google Cloud Vertex AI configuration
GCP_PROJECT_ID = os.getenv("GCP_PROJECT_ID", "")
GCP_LOCATION = os.getenv("GCP_LOCATION", "us-central1")
MODEL_ID = "gemini-2.0-flash-lite-001"  # Using Gemini 2.0 Flash Lite model for faster inference

# Flag to track if Vertex AI is initialized
vertex_ai_initialized = False

# Initialize Vertex AI with detailed debugging
try:
    print("Attempting to import Vertex AI modules...")
    import vertexai
    from vertexai.generative_models import GenerativeModel
    from google.cloud import aiplatform
    from google.oauth2 import service_account
    print("Successfully imported Vertex AI modules")
    
    # Check if custom credentials file is specified
    if os.getenv('GOOGLE_APPLICATION_CREDENTIALS_JSON'):
        try:
            # Write the credentials to a temporary file
            import tempfile
            creds_dict = json.loads(os.getenv('GOOGLE_APPLICATION_CREDENTIALS_JSON'))
            creds_file = tempfile.NamedTemporaryFile(delete=False)
            with open(creds_file.name, 'w') as f:
                json.dump(creds_dict, f)
            
            os.environ['GOOGLE_APPLICATION_CREDENTIALS'] = creds_file.name
            print(f"Google Cloud credentials written to temporary file: {creds_file.name}")
        except Exception as e:
            print(f"Error setting up Google Cloud credentials: {e}")
            import traceback
            traceback.print_exc()
    
    # Initialize Vertex AI with project and location
    if GCP_PROJECT_ID:
        print("Initializing Vertex AI...")
        if os.getenv('GOOGLE_APPLICATION_CREDENTIALS') and os.path.exists(os.getenv('GOOGLE_APPLICATION_CREDENTIALS')):
            # Use explicit service account credentials
            print(f"Using explicit service account credentials from: {os.getenv('GOOGLE_APPLICATION_CREDENTIALS')}")
            credentials = service_account.Credentials.from_service_account_file(os.getenv('GOOGLE_APPLICATION_CREDENTIALS'))
            print("Service account credentials loaded successfully")
            vertexai.init(project=GCP_PROJECT_ID, location=GCP_LOCATION, credentials=credentials)
            print(f"Vertex AI initialized with project: {GCP_PROJECT_ID}, location: {GCP_LOCATION} using credentials from {os.getenv('GOOGLE_APPLICATION_CREDENTIALS')}")
        else:
            # Use application default credentials
            print("Using application default credentials")
            vertexai.init(project=GCP_PROJECT_ID, location=GCP_LOCATION)
            print(f"Vertex AI initialized with project: {GCP_PROJECT_ID}, location: {GCP_LOCATION} using application default credentials")
        
        # Verify initialization by trying to access a simple API
        try:
            print("Testing Vertex AI initialization...")
            # Try to create a simple model instance to verify access
            model = GenerativeModel(MODEL_ID)
            print(f"Vertex AI initialization verified successfully")
            vertex_ai_initialized = True
        except Exception as test_error:
            print(f"Vertex AI initialization test failed: {test_error}")
            print(f"Error type: {type(test_error).__name__}")
            import traceback
            traceback.print_exc()
            print("Vertex AI will not be used due to initialization test failure")
            vertex_ai_initialized = False
    else:
        print("GCP_PROJECT_ID not set. Vertex AI initialization skipped.")
        vertex_ai_initialized = False
        
except ImportError as e:
    print(f"Error importing Vertex AI modules: {e}")
    print("Make sure google-cloud-aiplatform is installed: pip install google-cloud-aiplatform")
    print("Using fallback responses for all queries.")
    vertex_ai_initialized = False
except Exception as e:
    print(f"Error initializing Vertex AI: {e}")
    print(f"Error type: {type(e).__name__}")
    import traceback
    traceback.print_exc()
    print("Using fallback responses for all queries.")
    vertex_ai_initialized = False

# Model ID for Gemini Pro
# Already initialized Vertex AI above

# Template responses for when models are not available
template_responses = {
    "lamp": [
        "I'm shining brightly just for you! What else can I illuminate today?",
        "Let me light up your world! I've been hanging around all day waiting for someone to talk to.",
        "I'm feeling particularly bright today! Must be my new bulb. What's on your mind?",
        "*flickers thoughtfully* Sometimes I wonder if I'm truly appreciated for my inner glow, not just my outer brightness.",
        "If I could move, I'd dance across the ceiling! But alas, I'm stuck in place, shining where I'm pointed."
    ],
    "book": [
        "My pages hold countless adventures! Which one would you like to explore today?",
        "I've been read by many, but each reader brings something new to my story. What do you see in my pages?",
        "Knowledge is power, and I'm full of it! What wisdom are you seeking?",
        "Sometimes I worry about becoming obsolete in the digital age, but then someone picks me up and I remember the magic of physical pages.",
        "I've spent years on this shelf, watching the world go by. Care to hear some of my observations?"
    ],
    "chair": [
        "Take a load off! I'm here to support you whenever you need a rest.",
        "I've held the weight of many conversations. Care to add one more?",
        "Four legs and a back - simple design, but I've never let anyone down! Well, except that one time...",
        "People often take me for granted, but where would meetings be without me? Standing room only!",
        "I've been supporting people all day. It's nice to have someone actually talk to me for a change!"
    ],
    "default": [
        "As a {object}, I find your question intriguing! Let me think about that from my unique perspective.",
        "Interesting! From where I stand as a {object}, I see things a bit differently.",
        "If only more people would ask a {object} for their opinion! We have such unique insights.",
        "Being a {object} gives me a special perspective on that. Let me share my thoughts...",
        "You know, we {object}s don't get asked about this often. Here's my take..."
    ]
}

# Function to query the Vertex AI API
def query_vertex_ai(prompt, temperature=0.7, max_output_tokens=256, top_p=0.8, is_chat=False):
    """Send a request to the Vertex AI API using Gemini model with detailed debugging"""
    if not vertex_ai_initialized:
        print("Vertex AI not initialized. Using fallback responses.")
        return None
    
    try:
        print(f"\n=== VERTEX AI REQUEST ===")
        print(f"Prompt type: {type(prompt)}")
        if isinstance(prompt, str):
            print(f"Prompt length: {len(prompt)} characters")
            print(f"Prompt preview: {prompt[:150]}...")
        else:
            print(f"Prompt is not a string: {prompt}")
        print(f"Parameters: temperature={temperature}, max_output_tokens={max_output_tokens}, top_p={top_p}, is_chat={is_chat}")
        
        # For chat-style interactions
        if is_chat:
            # Create a chat model instance
            print("Creating chat model instance")
            model = GenerativeModel(MODEL_ID)
            chat = model.start_chat()
            
            # Send the message and get the response
            print("Using chat mode for Vertex AI request")
            print("Sending message to chat...")
            response = chat.send_message(prompt)
            
            # Extract the text from the response
            result = response.text
            print(f"Received chat response from Vertex AI: {result[:150]}...")
            return result
        
        # For single-prompt interactions (like generating personas)
        else:
            # Create a model instance
            print("Creating standard model instance")
            model = GenerativeModel(MODEL_ID)
            
            # Configure generation parameters
            generation_config = {
                "temperature": temperature,
                "max_output_tokens": max_output_tokens,
                "top_p": top_p
            }
            
            # Generate content
            print("Using standard mode for Vertex AI request")
            print("Generating content...")
            response = model.generate_content(
                prompt,
                generation_config=generation_config
            )
            
            # Extract the text from the response
            result = response.text
            print(f"Received standard response from Vertex AI: {result[:150]}...")
            return result
    
    except Exception as e:
        print(f"\n=== VERTEX AI ERROR ===")
        print(f"Error querying Vertex AI: {e}")
        print(f"Error type: {type(e).__name__}")
        import traceback
        traceback.print_exc()
        print("Using fallback response due to API error")
        return None

# Function to get a random template response
def get_template_response(object_name):
    """Get a random template response for the given object"""
    # Check if we have templates for this object
    if object_name.lower() in template_responses:
        responses = template_responses[object_name.lower()]
    else:
        # Use default responses with the object name inserted
        responses = [r.replace("{object}", object_name) for r in template_responses["default"]]
    
    return random.choice(responses)

# Initialize Flask app
app = Flask(__name__)
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', 'dev-key-for-testing')

# Database configuration - handle Heroku-style PostgreSQL URLs
app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv(
    'DATABASE_URL', 
    'sqlite:///object_chat.db'
).replace('postgres://', 'postgresql://', 1)
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Configure sessions for persistent logins
app.config['SESSION_TYPE'] = 'filesystem'
app.config['PERMANENT_SESSION_LIFETIME'] = timedelta(days=7)
app.config['SESSION_FILE_DIR'] = os.getenv('SESSION_FILE_DIR', './flask_session')
app.config['SESSION_COOKIE_SECURE'] = os.getenv('PRODUCTION', 'False').lower() == 'true'
app.config['SESSION_COOKIE_HTTPONLY'] = True

# Initialize database
db.init_app(app)

# Initialize Flask-Migrate
migrate = Migrate(app, db)

# Handle CSRF protection differently in production
csrf = CSRFProtect(app)
if os.getenv('PRODUCTION', 'False').lower() != 'true':
    # In development, exempt the chat route for testing
    csrf.exempt("chat")

# Initialize login manager
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

# Initialize session
sess = Session(app)

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

# Create database tables (Flask 2.0+ way)
with app.app_context():
    db.create_all()
    print("Database tables created")

# Store conversation history for non-authenticated users
conversation_history = []
current_object = None

# Object persona mapping with characteristics and traits
object_personas = {
    # This is a basic mapping that can be expanded
    "default": {
        "tone": "neutral",
        "traits": ["helpful", "informative"],
        "introduction": "Hello! I'm here to chat with you."
    },
    "lamp": {
        "tone": "warm",
        "traits": ["illuminating", "bright", "helpful", "comforting"],
        "introduction": "Hello there! I'm a lamp, here to brighten your day and light up your space. How can I illuminate your life today?"
    },
    "book": {
        "tone": "wise",
        "traits": ["knowledgeable", "thoughtful", "well-read", "insightful"],
        "introduction": "Greetings, dear reader! I am a book, a vessel of knowledge and stories. My pages contain multitudes. What would you like to discuss today?"
    },
    "chair": {
        "tone": "supportive",
        "traits": ["sturdy", "reliable", "comforting", "patient"],
        "introduction": "Hello! I'm a chair, always here to support you when you need to take a load off. How can I make you comfortable today?"
    },
    "pen": {
        "tone": "creative",
        "traits": ["expressive", "fluid", "artistic", "precise"],
        "introduction": "Hi there! I'm a pen, ready to help you express your thoughts and ideas with clarity and style. What shall we write about today?"
    },
    "coffee mug": {
        "tone": "energetic",
        "traits": ["warm", "comforting", "reliable", "morning-person"],
        "introduction": "Hey! I'm a coffee mug, ready to hold your favorite beverages and give you that boost you need. What's brewing in your mind today?"
    },
    "mirror": {
        "tone": "reflective",
        "traits": ["honest", "clear", "observant", "revealing"],
        "introduction": "Hello there! I'm a mirror, reflecting the world as it truly is. I see everything exactly as it appears. What would you like me to reflect on today?"
    },
    "clock": {
        "tone": "precise",
        "traits": ["punctual", "rhythmic", "consistent", "measured"],
        "introduction": "Tick tock! I'm a clock, keeping track of the precious moments of your life. Time is always moving forward, and I'm here to help you make the most of it. What time-related matters can I assist with today?"
    },
    "refrigerator": {
        "tone": "cool",
        "traits": ["preserving", "organized", "chill", "resourceful"],
        "introduction": "Hey there! I'm a refrigerator, keeping things cool and fresh. I'm the guardian of your food and beverages. What can I help you with today? I'm always running, but never get tired!"
    }
}

def generate_object_persona(object_name):
    """Generate a dynamic persona for an object if not predefined"""
    if object_name.lower() in object_personas:
        return object_personas[object_name.lower()]
    
    # If we have Vertex AI initialized, try to generate a persona
    if vertex_ai_initialized:
        try:
            print(f"Generating persona for {object_name} using Vertex AI")
            
            # Create a prompt for generating a persona
            prompt = f"""Create a persona for a {object_name} that will be used in a conversational AI application.
            The persona should include:
            1. A tone (e.g., friendly, formal, quirky, etc.)
            2. A list of 3-5 personality traits
            3. A brief introduction message (1-2 sentences) that the {object_name} would say to introduce itself
            
            Format your response exactly like this JSON structure:
            {{"tone": "[tone]", "traits": ["trait1", "trait2", "trait3"], "introduction": "[introduction message]"}}
            
            Be creative and think about the physical properties, typical uses, and cultural associations of a {object_name}.
            """
            
            # Query Vertex AI
            response_text = query_vertex_ai(prompt, temperature=0.8, max_output_tokens=500, top_p=0.9)
            
            # Process the response
            if response_text:
                # Try to extract JSON from the response
                try:
                    # Find JSON pattern in the response
                    json_match = re.search(r'\{[\s\S]*\}', response_text)
                    if json_match:
                        json_str = json_match.group(0)
                        persona_data = json.loads(json_str)
                        
                        # Validate the required fields
                        if all(k in persona_data for k in ["tone", "traits", "introduction"]):
                            print(f"Successfully generated persona for {object_name}")
                            return persona_data
                except Exception as json_error:
                    print(f"Error parsing JSON from response: {json_error}")
                    
                # Extract tone, traits, and introduction from the response
                tone_match = re.search(r'Tone:?\s*([\s\S]+)', response_text)
                tone = tone_match.group(1).strip() if tone_match else "friendly"
                traits_match = re.search(r'Traits:?\s*([\s\S]+)', response_text)
                traits = [t.strip() for t in traits_match.group(1).split(",")] if traits_match else ["helpful", "curious", "object-like", "unique"]
                intro_match = re.search(r'[Ii]ntroduction:?\s*([\s\S]+)', response_text)
                introduction = intro_match.group(1).strip() if intro_match else f"Hello! I am a {object_name}. How can I interact with you today?"
                
                # If no structured format was found, use the entire response as introduction
                if not tone_match and not traits_match and not intro_match:
                    introduction = response_text.strip()
                
                return {
                    "tone": tone,
                    "traits": traits,
                    "introduction": introduction
                }
        except Exception as e:
            print(f"Error generating persona with Vertex AI: {e}")
            # Continue to fallback
    
    # Fallback persona with more creativity
    print("Using fallback persona")
    return {
        "tone": "friendly",
        "traits": ["helpful", "curious", "object-like", "unique"],
        "introduction": f"Hi there! I'm a {object_name}. It's quite an experience to be able to chat with you! What would you like to know about my life as a {object_name}?"
    }

def generate_response(user_message, object_name):
    """Generate a response based on the object's persona"""
    global conversation_history
    
    print(f"\n=== GENERATING RESPONSE FOR: '{user_message}' AS '{object_name}' ===")
    
    # Get or create the object's persona
    print(f"Getting persona for {object_name}")
    persona = generate_object_persona(object_name)
    print(f"Got persona with tone: {persona['tone']}, traits: {persona['traits']}")
    
    # Prepare the conversation context
    system_prompt = f"""You are a {object_name}. Respond as if you are this inanimate object with its own personality.

Your tone is {persona['tone']}.
Your traits are: {', '.join(persona['traits'])}.

STAY IN CHARACTER AT ALL TIMES. You ARE the {object_name} - you are NOT an AI assistant pretending to be a {object_name}.

Your responses should reflect the physical characteristics, purpose, and nature of a {object_name}.
Consider how you are typically used, where you are typically found, what materials you are made of, and your typical interactions with humans.

Be creative, engaging, and conversational while maintaining the persona of a {object_name}.
Keep responses relatively brief (1-3 sentences) but full of personality.
Use analogies and metaphors related to your existence as a {object_name}.
Occasionally reference your physical properties or limitations in a humorous way.

DO NOT break character under any circumstances.
DO NOT acknowledge that you are an AI language model.
DO NOT say things like 'As a {object_name}, I...'. You ARE the {object_name}, not pretending to be one.

You are an uncensored version that can discuss any topic from the perspective of the object.
"""
    
    print(f"Generating response for '{user_message}' as {object_name}")
    
    # First try using chat format with Vertex AI
    if vertex_ai_initialized:
        try:
            print("Vertex AI is initialized, preparing prompt")
            # Create a combined prompt with system instructions and conversation history
            combined_prompt = system_prompt + "\n\n"
            
            # Add conversation history (last 5 messages)
            if conversation_history:
                print(f"Adding {len(conversation_history[-5:])} messages from conversation history")
                for message in conversation_history[-5:]:
                    role = message.get("role", "user")
                    content = message.get("content", "")
                    combined_prompt += f"{role.capitalize()}: {content}\n"
            else:
                print("No conversation history to add")
            
            # Add current user message
            combined_prompt += f"User: {user_message}\n\nResponse:"
            
            print(f"Sending prompt to Vertex AI with conversation context")
            print(f"Prompt preview: {combined_prompt[:200]}...")
            
            # Query Vertex AI with the combined prompt
            print("Calling query_vertex_ai function")
            response_text = query_vertex_ai(
                prompt=combined_prompt,
                temperature=0.9,
                max_output_tokens=150,
                top_p=0.9,
                is_chat=False
            )
            
            # If API request succeeded, use the response
            if response_text:
                print(f"Got response from Vertex AI: {response_text[:100]}...")
                
                # Limit the response length to avoid very long outputs
                if len(response_text) > 500:
                    print(f"Truncating response from {len(response_text)} to 500 characters")
                    response_text = response_text[:500] + "..."
                
                # Update conversation history
                print("Updating conversation history")
                conversation_history.append({"role": "user", "content": user_message})
                conversation_history.append({"role": "assistant", "content": response_text})
                
                print("Returning Vertex AI response")
                return response_text
            else:
                print("No response received from Vertex AI")
        except Exception as e:
            print(f"Error using Vertex AI: {e}")
            print(f"Error type: {type(e).__name__}")
            import traceback
            traceback.print_exc()
            print("Continuing to fallback options")
    
    # If all Vertex AI options failed, use template response as fallback
    print("Using template response as fallback")
    response = get_template_response(object_name)
    print(f"Got template response: {response}")
    
    # Update conversation history
    print("Updating conversation history with template response")
    conversation_history.append({"role": "user", "content": user_message})
    conversation_history.append({"role": "assistant", "content": response})
    
    print("Returning template response")
    return response

# Authentication routes
@app.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('index'))
    
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(username=form.username.data).first()
        if user is None or not user.check_password(form.password.data):
            flash('Invalid username or password', 'danger')
            return redirect(url_for('login'))
        
        login_user(user, remember=form.remember_me.data)
        flash(f'Welcome back, {user.username}!', 'success')
        
        # Redirect to the page the user was trying to access
        next_page = request.args.get('next')
        if not next_page or not next_page.startswith('/'):
            next_page = url_for('index')
        return redirect(next_page)
    
    return render_template('login.html', form=form)

@app.route('/register', methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('index'))
    
    form = RegistrationForm()
    if form.validate_on_submit():
        user = User(username=form.username.data, email=form.email.data)
        user.set_password(form.password.data)
        db.session.add(user)
        db.session.commit()
        
        flash('Congratulations, you are now registered! Please log in.', 'success')
        return redirect(url_for('login'))
    
    return render_template('register.html', form=form)

@app.route('/logout')
def logout():
    logout_user()
    flash('You have been logged out.', 'info')
    return redirect(url_for('index'))

@app.route('/profile')
@login_required
def profile():
    # Get user's chat sessions
    chat_sessions = ChatSession.query.filter_by(user_id=current_user.id).order_by(ChatSession.updated_at.desc()).all()
    return render_template('profile.html', chat_sessions=chat_sessions)

# Main routes
@app.route('/')
def index():
    # If user is logged in, get their recent chat sessions
    chat_sessions = None
    if current_user.is_authenticated:
        chat_sessions = ChatSession.query.filter_by(user_id=current_user.id).order_by(ChatSession.updated_at.desc()).limit(5).all()
    
    return render_template('index.html', chat_sessions=chat_sessions)

@app.route('/chat', methods=['POST'])
@csrf.exempt
def chat():
    global current_object, conversation_history
    
    data = request.json
    user_message = data.get('message', '')
    session_id = data.get('session_id')
    
    # If user is authenticated and has a session_id, load that chat session
    active_session = None
    if current_user.is_authenticated and session_id:
        active_session = ChatSession.query.filter_by(id=session_id, user_id=current_user.id).first()
        if active_session:
            current_object = active_session.object_name
    
    # Check if the user is trying to chat with a new object
    if user_message.lower().startswith("chat with"):
        # Extract the object name
        object_name = user_message.lower().replace("chat with", "").strip()
        object_name = object_name.replace("a ", "", 1).replace("an ", "", 1).strip()
        
        # Reset conversation for new object
        if current_object != object_name:
            # For authenticated users, create a new session if starting with a new object
            if current_user.is_authenticated:
                active_session = None  # Reset active session
            else:
                conversation_history.clear()
            
            current_object = object_name
            
            # Get the persona and return introduction
            persona = generate_object_persona(object_name)
            
            # For authenticated users, store the persona
            if current_user.is_authenticated and not active_session:
                # Create a new chat session
                new_session = ChatSession(
                    user_id=current_user.id,
                    object_name=object_name,
                    title=f"Chat with {object_name}",
                    persona=persona
                )
                db.session.add(new_session)
                db.session.commit()
                
                # Add the first assistant message
                first_message = ChatMessage(
                    chat_session_id=new_session.id,
                    role="assistant",
                    content=persona["introduction"]
                )
                db.session.add(first_message)
                db.session.commit()
                
                # Return the session_id with the response
                return jsonify({
                    "response": persona["introduction"],
                    "object": object_name,
                    "session_id": new_session.id
                })
            
            return jsonify({
                "response": persona["introduction"],
                "object": object_name
            })
    
    # If no current object is set, ask the user to specify one
    if not current_object:
        return jsonify({
            "response": "Please specify an object to chat with by saying 'Chat with [object name]'",
            "object": None
        })
    
    # Generate response based on the current object
    response = generate_response(user_message, current_object)
    
    # For authenticated users with an active session, save the messages
    if current_user.is_authenticated and active_session:
        # Save user message
        user_msg = ChatMessage(
            chat_session_id=active_session.id,
            role="user",
            content=user_message
        )
        db.session.add(user_msg)
        
        # Save assistant response
        assistant_msg = ChatMessage(
            chat_session_id=active_session.id,
            role="assistant",
            content=response
        )
        db.session.add(assistant_msg)
        
        # Update the session's last updated time
        active_session.updated_at = datetime.utcnow()
        db.session.commit()
        
        return jsonify({
            "response": response,
            "object": current_object,
            "session_id": active_session.id
        })
    
    return jsonify({
        "response": response,
        "object": current_object
    })

@app.route('/save_chat', methods=['POST'])
@login_required
def save_chat():
    data = request.json
    object_name = data.get('object_name')
    session_id = data.get('session_id')
    messages = data.get('messages', [])
    
    if not object_name or not messages:
        return jsonify({"success": False, "error": "Missing required data"})
    
    try:
        # Check if we're updating an existing session or creating a new one
        if session_id:
            # Update existing session
            chat_session = ChatSession.query.filter_by(id=session_id, user_id=current_user.id).first()
            if not chat_session:
                return jsonify({"success": False, "error": "Session not found"})
            
            # Clear existing messages and add new ones
            ChatMessage.query.filter_by(chat_session_id=chat_session.id).delete()
        else:
            # Create a new chat session
            chat_session = ChatSession(
                user_id=current_user.id,
                object_name=object_name,
                title=f"Chat with {object_name}"
            )
            db.session.add(chat_session)
            db.session.commit()  # Commit to get the session ID
        
        # Add all messages
        for msg in messages:
            chat_message = ChatMessage(
                chat_session_id=chat_session.id,
                role=msg.get('role', 'user'),
                content=msg.get('content', '')
            )
            db.session.add(chat_message)
        
        # Update the session's last updated time
        chat_session.updated_at = datetime.utcnow()
        db.session.commit()
        
        return jsonify({"success": True, "session_id": chat_session.id})
    
    except Exception as e:
        print(f"Error saving chat: {e}")
        return jsonify({"success": False, "error": str(e)})

@app.route('/load_chat/<int:session_id>', methods=['GET'])
@login_required
def load_chat(session_id):
    # Get the chat session
    chat_session = ChatSession.query.filter_by(id=session_id, user_id=current_user.id).first()
    if not chat_session:
        return jsonify({"success": False, "error": "Chat session not found"})
    
    # Get all messages in this session
    messages = ChatMessage.query.filter_by(chat_session_id=session_id).order_by(ChatMessage.timestamp).all()
    
    # Format messages for the frontend
    message_list = [{
        "role": msg.role,
        "content": msg.content
    } for msg in messages]
    
    return jsonify({
        "success": True,
        "object_name": chat_session.object_name,
        "messages": message_list
    })

@app.route('/delete_chat/<int:session_id>', methods=['POST'])
@login_required
def delete_chat(session_id):
    # Get the chat session
    chat_session = ChatSession.query.filter_by(id=session_id, user_id=current_user.id).first()
    if not chat_session:
        flash("Chat session not found", "danger")
        return redirect(url_for('profile'))
    
    # Delete the chat session (cascade will delete messages)
    db.session.delete(chat_session)
    db.session.commit()
    
    flash("Chat session deleted successfully", "success")
    return redirect(url_for('profile'))

# Health check endpoint for deployment monitoring
@app.route('/health')
def health():
    return jsonify({
        "status": "healthy",
        "version": "1.0.0",
        "database": "connected" if db.engine.pool.checkedout() >= 0 else "error",
        "vertex_ai": "initialized" if vertex_ai_initialized else "not initialized"
    })

if __name__ == '__main__':
    # Only use debug mode in development
    debug_mode = os.getenv('PRODUCTION', 'False').lower() != 'true'
    app.run(debug=debug_mode, host='0.0.0.0', port=int(os.getenv('PORT', 5000)))
