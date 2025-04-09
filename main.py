from flask import Flask, request, jsonify, render_template, send_file
import speech_recognition as sr
import webbrowser
import pyttsx3
import os
import tempfile
import pygame
from gtts import gTTS
import threading
import time
import json
import urllib.parse
import re

# Enhanced imports
import musicLibrary
import requests
import google.generativeai as genai
from bs4 import BeautifulSoup

# Load API Key Securely
GEMINI_API_KEY = "xxxxx"  # Your API key

# Configure Gemini API
if GEMINI_API_KEY:
    genai.configure(api_key=GEMINI_API_KEY)
else:
    print("Error: GEMINI API Key is missing!")

# Initialize recognizer and speech engine
recognizer = sr.Recognizer()
engine = pyttsx3.init()
newsapi = "46d63d6e8b4c463194ecaa2d3dc158cc"  # Your News API key

# Initialize the Gemini model with better configuration
try:
    model = genai.GenerativeModel(
        model_name="gemini-1.5-flash",
        generation_config={
            "temperature": 0.7,
            "top_p": 0.95,
            "top_k": 40,
            "max_output_tokens": 2048,  # Increased token limit for more complete answers
        }
    )
    
    # Start a chat session with enhanced context and instructions
    chat = model.start_chat(
        history=[
            {
                "role": "user",
                "parts": ["""You are Jarvis, an advanced AI voice assistant. Your goal is to provide comprehensive, 
                accurate answers to any question while keeping responses clear and concise. When you don't know 
                something, you should indicate that you'll search for the information. Always prioritize factual 
                information and be helpful in all contexts."""]
            },
            {
                "role": "model",
                "parts": ["I am Jarvis, your advanced voice assistant. I'm ready to help with information, tasks, and any questions you have. Just ask, and I'll provide the most helpful answer possible."]
            }
        ]
    )
    print("Gemini model and chat session initialized successfully")
except Exception as e:
    print(f"Error initializing Gemini model: {e}")
    chat = None

# Create Flask app
app = Flask(__name__)

# Audio output queue for handling speech output
speech_queue = []
is_speaking = False

def speak_worker():
    """Background worker to process speech queue"""
    global is_speaking
    while True:
        if speech_queue and not is_speaking:
            text = speech_queue.pop(0)
            is_speaking = True
            try:
                tts = gTTS(text)
                temp_file = tempfile.NamedTemporaryFile(delete=False, suffix=".mp3")
                temp_filename = temp_file.name
                temp_file.close()
                
                tts.save(temp_filename)
                
                pygame.mixer.init()
                pygame.mixer.music.load(temp_filename)
                pygame.mixer.music.play()
                
                while pygame.mixer.music.get_busy():
                    pygame.time.Clock().tick(10)
                
                pygame.mixer.music.stop()
                pygame.mixer.quit()
                
                try:
                    os.remove(temp_filename)
                except:
                    print(f"Warning: Unable to delete {temp_filename}")
            except Exception as e:
                print(f"Error in speech worker: {e}")
            finally:
                is_speaking = False
        time.sleep(0.1)

# Start speech worker thread
speech_thread = threading.Thread(target=speak_worker, daemon=True)
speech_thread.start()

def generate_speech(text):
    """Generate speech file and return the path"""
    try:
        tts = gTTS(text)
        temp_file = tempfile.NamedTemporaryFile(delete=False, suffix=".mp3")
        temp_filename = temp_file.name
        temp_file.close()
        
        tts.save(temp_filename)
        return temp_filename
    except Exception as e:
        print(f"Error generating speech: {e}")
        return None

def queue_speech(text):
    """Add text to speech queue"""
    speech_queue.append(text)

def search_web(query):
    """Search the web for information when AI doesn't have an answer"""
    try:
        # Format the query for a search URL
        search_query = urllib.parse.quote_plus(query)
        search_url = f"https://www.google.com/search?q={search_query}"
        
        # Set a user agent to avoid being blocked
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
        
        # Send the request
        response = requests.get(search_url, headers=headers)
        
        if response.status_code == 200:
            # Parse the HTML content
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # Extract information from search results
            # Look for featured snippets or knowledge panels first
            featured_snippet = soup.select('.hgKElc')
            if featured_snippet:
                return featured_snippet[0].get_text().strip()
            
            # Look for regular search results
            search_results = soup.select('.BNeawe')
            if search_results:
                # Combine the first few results
                result_text = ""
                for result in search_results[:3]:
                    result_text += result.get_text().strip() + " "
                return result_text.strip()
            
        return f"I searched for information about '{query}' but couldn't find a clear answer. Would you like me to open a web browser so you can see the search results?"
    
    except Exception as e:
        print(f"Web search error: {e}")
        return f"I tried to search for '{query}' but encountered a technical issue. Would you like me to open a web browser instead?"

def get_wikipedia_summary(topic):
    """Get a summary from Wikipedia API"""
    try:
        # Format the topic for Wikipedia API
        formatted_topic = urllib.parse.quote_plus(topic)
        wiki_url = f"https://en.wikipedia.org/api/rest_v1/page/summary/{formatted_topic}"
        
        response = requests.get(wiki_url)
        
        if response.status_code == 200:
            data = response.json()
            return data.get('extract', '')
        else:
            return ""
    except Exception as e:
        print(f"Wikipedia API error: {e}")
        return ""

def get_weather(location):
    """Get current weather information"""
    try:
        # You would need to sign up for a weather API service like OpenWeatherMap
        # This is a placeholder implementation
        weather_api_key = "your_weather_api_key"
        weather_url = f"https://api.openweathermap.org/data/2.5/weather?q={location}&appid={weather_api_key}&units=metric"
        
        response = requests.get(weather_url)
        
        if response.status_code == 200:
            data = response.json()
            temp = data['main']['temp']
            condition = data['weather'][0]['description']
            humidity = data['main']['humidity']
            
            return f"Weather in {location}: {condition}, {temp}°C with {humidity}% humidity."
        else:
            return f"I couldn't retrieve the weather for {location}. Would you like me to search the web instead?"
    except Exception as e:
        print(f"Weather API error: {e}")
        return f"I'm having trouble getting the weather information. I can open a weather website for you instead."

def aiProcess(command):
    try:
        if not GEMINI_API_KEY or chat is None:
            return "AI services are unavailable. Please check your API key and connection."

        # Detect if this is a factual/knowledge question vs. a chat
        is_knowledge_question = re.search(r'(what|who|where|when|why|how|explain|tell me about|search for|find|look up)', command.lower())
        
        # Use the chat session to maintain context
        try:
            # For knowledge questions, enhance the prompt
            if is_knowledge_question:
                # Try to get information from Wikipedia first for common knowledge questions
                potential_topic = re.sub(r'^(what|who|where|when|why|how|is|are|tell me about|search for) ', '', command.lower())
                wiki_info = get_wikipedia_summary(potential_topic)
                
                if wiki_info:
                    # If we found wiki info, include it in the prompt
                    enhanced_prompt = f"""Question: {command}
                    
                    Here is some relevant information to help you answer:
                    {wiki_info}
                    
                    Please provide a clear, concise, and accurate answer based on this information."""
                    
                    response = chat.send_message(enhanced_prompt)
                else:
                    # If no wiki info, just send the regular command
                    response = chat.send_message(command)
            else:
                # For regular chat, just send the command
                response = chat.send_message(command)
            
            # Get the text response
            response_text = response.text
            
            # If the model indicates uncertainty or lack of knowledge
            if any(phrase in response_text.lower() for phrase in 
                   ["i don't know", "i'm not sure", "i don't have information", 
                    "i can't provide", "i don't have access", "i'm unable to"]):
                # Try web search as fallback
                web_result = search_web(command)
                
                if web_result:
                    # Combine the AI response with web search results
                    return f"Based on my search: {web_result}"
                
            # Keep responses concise for better voice output but ensure completeness
            if len(response_text) > 800:
                response_text = response_text[:797] + "..."
                
            return response_text
                
        except Exception as e:
            print(f"Gemini Chat Error: {e}")
            
            # Fallback to direct generation if chat fails
            try:
                direct_response = model.generate_content(
                    "Act as Jarvis, an advanced AI assistant. Answer this question with accurate and helpful information: " + command
                )
                return direct_response.text
            except Exception as fallback_error:
                print(f"Fallback generation error: {fallback_error}")
                
                # If AI fails completely, try web search
                web_result = search_web(command)
                if web_result:
                    return web_result
                
                return "I'm having trouble processing that request. Would you like me to open a web browser so you can search for this information?"
    
    except Exception as e:
        print(f"AI Processing Error: {e}")
        return "I'm having trouble connecting to AI services. Would you like me to search the web instead?"

def processCommand(c):
    # Process the command and return the response
    # Basic command handling
    if "open google" in c.lower():
        webbrowser.open("https://google.com")
        return "Opening Google"
    elif "open facebook" in c.lower():
        webbrowser.open("https://facebook.com")
        return "Opening Facebook"
    elif "open youtube" in c.lower():
        webbrowser.open("https://youtube.com")
        return "Opening YouTube"
    elif "open linkedin" in c.lower():
        webbrowser.open("https://linkedin.com")
        return "Opening LinkedIn"
    
    # Enhanced command handling
    elif "search for" in c.lower() or "look up" in c.lower() or "find information" in c.lower():
        search_term = c.lower().replace("search for", "").replace("look up", "").replace("find information", "").strip()
        if search_term:
            search_url = f"https://www.google.com/search?q={urllib.parse.quote_plus(search_term)}"
            webbrowser.open(search_url)
            return f"Searching for {search_term} on Google"
        else:
            return "What would you like me to search for?"
    
    elif c.lower().startswith("play"):
        song = c.lower().replace("play ", "")
        link = musicLibrary.music.get(song) if hasattr(musicLibrary, "music") else None
        if link:
            webbrowser.open(link)
            return f"Playing {song}"
        else:
            # Enhanced music search
            search_url = f"https://www.youtube.com/results?search_query={urllib.parse.quote_plus('play ' + song)}"
            webbrowser.open(search_url)
            return f"I couldn't find {song} in the music library, so I'm searching for it on YouTube."
    
    elif "weather" in c.lower():
        # Extract location from the command
        location_match = re.search(r'weather (?:in|for|at) (.+)', c.lower())
        if location_match:
            location = location_match.group(1).strip()
            return get_weather(location)
        else:
            return "For which location would you like the weather information?"
    
    elif "news" in c.lower():
        # Enhanced news handling
        category_match = re.search(r'news (?:about|on|for) (.+)', c.lower())
        category = category_match.group(1).strip() if category_match else None
        
        try:
            # If category is specified, search for news in that category
            if category:
                r = requests.get(f"https://newsapi.org/v2/everything?q={category}&apiKey={newsapi}&pageSize=5")
            else:
                r = requests.get(f"https://newsapi.org/v2/top-headlines?country=us&apiKey={newsapi}&pageSize=5")
                
            if r.status_code == 200:
                data = r.json()
                articles = data.get('articles', [])
                if articles:
                    news_response = "Here are the top headlines:\n\n"
                    for i, article in enumerate(articles[:5]):
                        news_response += f"{i+1}. {article['title']}\n"
                    return news_response
                else:
                    return "Sorry, I couldn't find any news articles at the moment."
            else:
                return "Sorry, I'm having trouble connecting to the news service."
        except Exception as e:
            print(f"News error: {e}")
            return "Sorry, I couldn't retrieve the news at this moment."
    
    elif "timer" in c.lower() or "set timer" in c.lower():
        # Extract time information
        time_match = re.search(r'(\d+)\s+(second|minute|hour)', c.lower())
        if time_match:
            quantity = int(time_match.group(1))
            unit = time_match.group(2)
            
            # Convert to seconds
            seconds = quantity
            if unit == "minute":
                seconds = quantity * 60
            elif unit == "hour":
                seconds = quantity * 3600
                
            # Start a timer in a separate thread
            timer_thread = threading.Thread(target=lambda: timer_function(seconds, f"Timer for {quantity} {unit}{'s' if quantity > 1 else ''} is complete!"))
            timer_thread.daemon = True
            timer_thread.start()
            
            return f"I've set a timer for {quantity} {unit}{'s' if quantity > 1 else ''}."
        else:
            return "For how long would you like me to set the timer? Please specify seconds, minutes, or hours."
    
    elif "exit" in c.lower() or "quit" in c.lower() or "stop" in c.lower():
        return "I'll remain active in the background. Feel free to call me when you need assistance!"
    
    # For all other commands, use Gemini with enhanced AI processing
    else:
        return aiProcess(c)

def timer_function(seconds, message):
    """Function to handle timers"""
    time.sleep(seconds)
    queue_speech(message)

# Routes
@app.route('/')
def index():
    return render_template('index.html')

@app.route('/command', methods=['POST'])
def command():
    try:
        data = request.json
        command_text = data.get('command', '')
        
        if not command_text:
            return jsonify({"response": "I didn't hear anything. Could you try again?"}), 400
        
        # Process the command
        response_text = processCommand(command_text)
        
        # Generate speech
        speech_file = generate_speech(response_text)
        
        if speech_file:
            # Return both text and audio path
            return jsonify({
                "response": response_text,
                "audio": f"/audio/{os.path.basename(speech_file)}"
            })
        else:
            # Queue speech for background processing
            queue_speech(response_text)
            return jsonify({"response": response_text})
    
    except Exception as e:
        print(f"Command error: {e}")
        return jsonify({"response": "I encountered an error processing your request."}), 500

@app.route('/audio/<filename>')
def get_audio(filename):
    try:
        # Ensure the filename is safe
        if '..' in filename or filename.startswith('/'):
            return "Invalid filename", 400
        
        # Construct the full path to the temp file
        temp_dir = tempfile.gettempdir()
        file_path = os.path.join(temp_dir, filename)
        
        # Send the file and delete it after
        return send_file(file_path, conditional=True, as_attachment=False)
    except Exception as e:
        print(f"Audio error: {e}")
        return "Audio not found", 404

@app.route('/wake-detection', methods=['POST'])
def wake_detection():
    # This endpoint can be used to handle wake word detection from the browser
    try:
        data = request.json
        audio_data = data.get('audio')
        
        # In a real implementation, you would process the audio data here
        # For now, we'll just simulate a wake word detection
        
        return jsonify({"detected": True})
    except Exception as e:
        return jsonify({"detected": False, "error": str(e)})

if __name__ == '__main__':
    print("Starting Jarvis web interface with enhanced search capabilities...")
    app.run(debug=True, port=5000)