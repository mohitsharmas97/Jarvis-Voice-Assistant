# Jarvis Voice Assistant

Jarvis is an advanced web-based voice assistant that combines the power of Google's Gemini AI model with web search capabilities and practical functionality to create a responsive and intelligent digital assistant.

![image](https://github.com/user-attachments/assets/a29ca190-dc66-4bd3-aaab-d92c1bac81a6)


## 🌟 Features

- **Voice and Text Input**: Interact with Jarvis using voice commands or text input
- **AI-Powered Responses**: Utilizes Google's Gemini AI model for intelligent conversations
- **Comprehensive Search**: Enhanced with web search integration for questions the AI can't answer directly
- **Wikipedia Integration**: Accesses Wikipedia API for factual knowledge
- **Voice Synthesis**: Natural-sounding speech responses using gTTS
- **Web Navigation**: Open websites with simple voice commands
- **Music Playback**: Play songs from your custom library or search YouTube
- **News Updates**: Get the latest headlines or news on specific topics
- **Weather Information**: Check current weather conditions for any location
- **Timer Functionality**: Set timers with voice commands

## 📋 Requirements

- Python 3.8+
- Flask
- SpeechRecognition
- pyttsx3
- pygame
- gTTS (Google Text-to-Speech)
- BeautifulSoup4
- Google Generative AI Python SDK
- Requests

## 📢 Example Commands

- "Open YouTube"
- "Play [song name]"
- "Search for [topic]"
- "Tell me about [topic]"
- "What's the weather in [location]"
- "Set a timer for [number] [seconds/minutes/hours]"
- "Tell me the latest news"
- "News about [topic]"


## 🧠 How It Works

1. **Voice Recognition**: The browser captures audio using the Web Speech API
2. **Command Processing**: The Flask backend processes the command
3. **Smart Routing**:
   - Known commands are handled directly (opening websites, playing music, etc.)
   - Questions and unknown commands are sent to the Gemini AI model
   - If the AI doesn't know, the system performs a web search
4. **Response Synthesis**: The response is converted to speech and played back

## 🛠️ Architecture

```
┌─────────────┐     ┌──────────────────┐     ┌───────────────┐
│  Web Browser │ ──> │ Flask Web Server │ ──> │ Command Router│
└─────────────┘     └──────────────────┘     └───────┬───────┘
       ▲                                             │
       │                                             ▼
┌──────┴──────┐     ┌──────────────────┐     ┌───────────────┐
│  TTS Engine  │ <── │ Response Handler │ <── │  AI Processor │
└─────────────┘     └──────────────────┘     └───────┬───────┘
                                                    │
                          ┌─────────────────────────┼─────────────────────────┐
                          ▼                         ▼                         ▼
                    ┌──────────┐            ┌───────────────┐          ┌───────────┐
                    │ Gemini AI│            │ Wikipedia API │          │ Web Search│
                    └──────────┘            └───────────────┘          └───────────┘
```


## 👤 Author

Mohit

## Acknowledgements

- Google Generative AI for providing the Gemini API
- NewsAPI for news information
- Wikipedia for knowledge base access
- The open-source community for various libraries used in this project
