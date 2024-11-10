from flask import Flask, request, jsonify, render_template
import os
from datetime import datetime
import json
import ssl
import requests
from dotenv import load_dotenv
from pathlib import Path
import nltk

app = Flask(__name__)

# Load environment variables from .env file
env_path = Path('.') / '.env'
load_dotenv(dotenv_path=env_path)

# Informatica decoder configuration
INFORMATICA_DECODER_URL = os.environ.get('INFORMATICA_DECODER_URL', 'https://your-decoder-app.cfapps.url')

# NLTK setup
if not os.path.exists('nltk_data'):
    os.makedirs('nltk_data')

nltk.data.path.append(os.path.join(os.getcwd(), 'nltk_data'))

# Function to safely download NLTK data
def download_nltk_data():
    try:
        try:
            _create_unverified_https_context = ssl._create_unverified_context
        except AttributeError:
            pass
        else:
            ssl._create_default_https_context = _create_unverified_https_context

        for package in ['punkt', 'stopwords', 'wordnet']:
            try:
                nltk.download(package, download_dir='nltk_data', quiet=True)
            except Exception as e:
                print(f"Error downloading {package}: {str(e)}")
                pass
    except Exception as e:
        print(f"Error in NLTK setup: {str(e)}")

download_nltk_data()

# Load responses
try:
    with open('responses.json', 'r') as f:
        RESPONSES = json.load(f)
except Exception as e:
    print(f"Error loading responses: {str(e)}")
    RESPONSES = {
        "greeting": "Hello! I'm your SAP AI assistant. I can help you with general queries, generate content using AI, and decode Informatica mappings!",
        "farewell": "Goodbye! Have a great day!",
        "help": "I can help you with:\n- General SAP information\n- Generate content using AI\n- Decode Informatica mappings\n- Current date and time",
        "sap_info": "SAP is a leading enterprise software company.",
        "unknown": "I'm not sure I understand. Could you please rephrase that or ask for help to see what I can do?"
    }

def get_genai_response(prompt, intent=None):
    """Get response from OpenAI using direct API call"""
    try:
        openai_api_key = os.environ.get('OPENAI_API_KEY')
        if not openai_api_key:
            return "I apologize, but AI generation is currently unavailable. Please try basic queries or Informatica decoding."

        # Define system prompts based on intent
        system_prompts = {
            'genai_code_generation': """You are an SAP BTP deployment expert. Provide code and configuration examples specifically 
                                        for deploying applications to SAP Cloud Foundry and Kyma environments. Focus on SAP BTP best 
                                        practices, CLI commands, and deployment strategies relevant to these environments."""
        }

        # Select the appropriate system prompt or use a default
        system_prompt = system_prompts.get(
            intent,
            "You are a helpful SAP technical assistant with expertise in integration and data management."
        )

        # Prepare the API request
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {openai_api_key}"
        }
        
        data = {
            "model": "gpt-4",
            "messages": [
                {
                    "role": "system",
                    "content": system_prompt
                },
                {
                    "role": "user",
                    "content": prompt
                }
            ]
        }

        # Make the API call
        response = requests.post(
            "https://api.openai.com/v1/chat/completions",
            headers=headers,
            json=data
        )

        # Check if the request was successful
        if response.status_code == 200:
            return response.json()['choices'][0]['message']['content']
        else:
            print(f"OpenAI API Error: {response.status_code}")
            print(f"Response: {response.text}")
            return "I apologize, but I'm having trouble generating a response. Please try again later."

    except Exception as e:
        print(f"Error in GenAI response: {str(e)}")
        return "I apologize, but I'm having trouble generating an AI response right now. Please try again later."

def format_cloud_foundry_response():
    return (
        "Sure, here are the steps to deploy your application to Cloud Foundry:<br><br>"
        "1. <strong>Install the Cloud Foundry CLI</strong>: Ensure you have the Cloud Foundry CLI installed on your local machine.<br><br>"
        "2. <strong>Navigate to your application directory</strong>:<br>"
        "<pre>cd your_application_directory</pre><br>"
        "3. <strong>Set the API Endpoint</strong>:<br>"
        "<pre>cf api YOUR_API_ENDPOINT</pre><br>"
        "4. <strong>Log in to Cloud Foundry</strong>:<br>"
        "<pre>cf login</pre><br>"
        "5. <strong>Push your app</strong>:<br>"
        "<pre>cf push YOUR_APP_NAME</pre><br><br>"
        "These steps will help you get started with deploying your app to Cloud Foundry. Let me know if you need more details!"
    )

def check_informatica_intent(text):
    """Check if the message is about decoding Informatica mapping"""
    decode_keywords = ['decode', 'decipher', 'interpret', 'explain']
    informatica_keywords = ['informatica', 'mapping', 'etl']
    
    text_lower = text.lower()
    has_decode = any(keyword in text_lower for keyword in decode_keywords)
    has_informatica = any(keyword in text_lower for keyword in informatica_keywords)
    
    return has_decode and has_informatica

def get_intent(text):
    """Enhanced intent classification with priority order"""
    try:
        if check_informatica_intent(text):
            return 'informatica_decode'
        
        preprocessed_text = text.lower()
        
        intent_patterns = {
            'genai': ['generate', 'create', 'write', 'explain', 'how to', 'python', 'code', 'deploy', 'cloud foundry', 'kyma'],
            'greeting': ['hello', 'hi', 'hey', 'greetings'],
            'farewell': ['bye', 'goodbye', 'see you'],
            'help': ['help', 'support', 'assist'],
            'sap_info': ['sap', 'system', 'software'],
            'datetime': ['time', 'date', 'when']
        }
        
        for intent, patterns in intent_patterns.items():
            if any(pattern in preprocessed_text for pattern in patterns):
                print(f"Detected intent: {intent}")
                return intent

        return 'genai'
    except Exception as e:
        print(f"Error in intent classification: {str(e)}")
        return 'unknown'

@app.route('/')
def home():
    return render_template('index.html')

@app.route('/api/chat', methods=['POST'])
def chat():
    try:
        data = request.json
        user_message = data.get('message', '')

        if not user_message:
            return jsonify({'error': 'No message provided'}), 400

        intent = get_intent(user_message)
        print(f"User intent: {intent}")

        if intent == 'informatica_decode':
            return jsonify({
                'response': f"I can help you decode your Informatica mapping. Please visit: {INFORMATICA_DECODER_URL}",
                'intent': intent,
                'action': 'link',
                'link': INFORMATICA_DECODER_URL
            })
        
        elif intent == 'genai' and "cloud foundry" in user_message.lower():
            response = format_cloud_foundry_response()
            return jsonify({
                'response': response,
                'intent': intent
            })
        
        elif intent == 'genai':
            ai_response = get_genai_response(user_message)
            print(f"AI response: {ai_response}")
            return jsonify({
                'response': ai_response if ai_response else RESPONSES['unknown'],
                'intent': intent
            })

        elif intent == 'datetime':
            response = f"Current time is {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
        else:
            response = RESPONSES.get(intent, RESPONSES['unknown'])
        
        return jsonify({
            'response': response,
            'intent': intent
        })

    except Exception as e:
        print(f"Error in chat endpoint: {str(e)}")
        return jsonify({
            'response': "I apologize, but I'm having trouble processing your request right now. Please try again.",
            'intent': 'error'
        }), 500

@app.route('/api/health', methods=['GET'])
def health_check():
    openai_available = bool(os.environ.get('OPENAI_API_KEY'))
    
    if openai_available:
        try:
            headers = {
                "Content-Type": "application/json",
                "Authorization": f"Bearer {os.environ['OPENAI_API_KEY']}"
            }
            
            data = {
                "model": "gpt-4",
                "messages": [
                    {
                        "role": "system",
                        "content": "You are a helpful assistant."
                    },
                    {
                        "role": "user",
                        "content": "test"
                    }
                ]
            }
            
            response = requests.post(
                "https://api.openai.com/v1/chat/completions",
                headers=headers,
                json=data
            )
            openai_available = response.status_code == 200
        except Exception:
            openai_available = False
    
    status = {
        'status': 'healthy',
        'openai_available': openai_available,
        'informatica_decoder_url': INFORMATICA_DECODER_URL != 'https://your-decoder-app.cfapps.url'
    }
    return jsonify(status)

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 8080))
    debug_mode = os.environ.get('FLASK_DEBUG', 'False').lower() == 'true'
    app.run(host='0.0.0.0', port=port, debug=debug_mode)
