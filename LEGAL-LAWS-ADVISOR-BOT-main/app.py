import streamlit as st
import pyttsx3
import speech_recognition as sr
import threading
import pandas as pd
import json

# Initialize text-to-speech engine
engine = pyttsx3.init()

# Initialize session state attributes if not already set
if "messages" not in st.session_state:
    st.session_state.messages = []
if "conversation_context" not in st.session_state:
    st.session_state.conversation_context = []
if "interaction_log" not in st.session_state:
    st.session_state.interaction_log = pd.DataFrame(columns=["user_query", "assistant_response"])

# Ensure language_preference and user_logged_in are initialized
if "language_preference" not in st.session_state:
    st.session_state.language_preference = "English"
if "user_logged_in" not in st.session_state:
    st.session_state.user_logged_in = False
if "speech_in_progress" not in st.session_state:
    st.session_state.speech_in_progress = False

# Function to convert text to speech
def speak(text):
    # If speech is in progress, stop the speech before starting new speech
    if st.session_state.speech_in_progress:
        engine.stop()  # Stop any ongoing speech
        st.session_state.speech_in_progress = False  # Reset the flag immediately

    def speak_thread():
        st.session_state.speech_in_progress = True
        engine.say(text)
        engine.runAndWait()
        st.session_state.speech_in_progress = False

    # Run the speech in a separate thread to avoid blocking Streamlit's main event loop
    threading.Thread(target=speak_thread).start()

# Function for voice input (speech to text)
def listen():
    recognizer = sr.Recognizer()
    with sr.Microphone() as source:
        st.write("Listening...")
        recognizer.adjust_for_ambient_noise(source)
        audio = recognizer.listen(source)
        try:
            query = recognizer.recognize_google(audio)
            st.write(f"Voice Input: {query}")
            return query
        except sr.UnknownValueError:
            st.error("Sorry, I couldn't understand that.")
        except sr.RequestError:
            st.error("Sorry, the speech service is down.")

# Load patterns from JSON file
def load_patterns():
    try:
        with open('legal_patterns.json', 'r') as file:
            return json.load(file)
    except FileNotFoundError:
        return {"error": "Patterns file not found."}
    except json.JSONDecodeError:
        return {"error": "Error decoding the patterns file."}

patterns = load_patterns()

# Define response function based on patterns
def get_response(query):
    query = query.lower().strip()
    if len(query) < 3:
        return translations[st.session_state.language_preference]["no_response"]

    # Add the latest user query to the conversation context
    st.session_state.conversation_context.append(f"User: {query}")

    # Check for matching patterns
    for item in patterns:
        pattern = item['pattern'].lower().strip()
        if pattern in query:
            response = item['response']
            st.session_state.conversation_context.append(f"Assistant: {response}")
            return response

    return translations[st.session_state.language_preference]["no_response"]

# Language Translation Dictionary
translations = {
    "English": {
        "ask_query": "Ask me anything about legal laws",
        "thinking": "Thinking ✨...",
        "no_response": "Sorry, I couldn't find a matching response for your query.",
        "positive_feedback": "👍 Positive feedback",
        "negative_feedback": "👎 Negative feedback",
        "login_button": "Login",
        "welcome": "Welcome",
        "faq_button": "Show FAQs",
        "download_button": "Download Chat History as CSV",
        "interaction_history": "Show Interaction History",
        "voice_query": "Voice Query 🎙️",
        "view_history": "View History 📜",
        "download_law": "Download Law 📁",
        "info_section": "**Legal Laws Advisor Bot:📄**\n- **Objective:** Developed a conversational chatbot to provide legal law info and assistance.\n- **Features:**📜\n  - Allows users to ask their query of law.\n  - Provides a response to user query. ✔\n  - Offers a user-friendly interface for asking legal questions."
    },
    # Add other languages as needed
}

# Streamlit Title
st.title("AI-LEGAL LAWS ASSISTANT 🎗️")

# Load and display the info section
st.info(translations[st.session_state.language_preference]["info_section"])

# Language selection from the sidebar
language_preference = st.sidebar.selectbox(
    "Welcome Select your preferred language :",
    ["English"],
    index=["English"].index(st.session_state.language_preference)
)

# Save selected language preference in session state
if language_preference != st.session_state.language_preference:
    st.session_state.language_preference = language_preference

# User login logic
if not st.session_state.user_logged_in:
    st.session_state.username = st.text_input("Enter your name to start chatting with legal laws assistant 🎗️")
    if st.session_state.username:
        st.session_state.user_logged_in = True
        st.rerun()
else:
    st.write(f"👋 Hello {st.session_state.username}! {translations[st.session_state.language_preference]['ask_query']}")
    prompt = st.chat_input(translations[st.session_state.language_preference]["ask_query"])

    if prompt:
        st.write(f"👤 Your Query: {prompt}")
        response = get_response(prompt)
        st.write(f"🤖 Response: {response}")

        new_log = {"user_query": prompt, "assistant_response": response}
        st.session_state.interaction_log = pd.concat(
            [st.session_state.interaction_log, pd.DataFrame([new_log])], ignore_index=True
        )

# Adding custom styling for buttons
st.markdown("""
    <style>
        .stButton>button {
            border: 2px solid #4CAF50;
            border-radius: 8px;
            color: white;
            padding: 5px 7px;
            font-size: 6px;
            margin: 10px;
            cursor: pointer;
        }

        .stButton>button:hover {
            background-color: white;
        }
    </style>
""", unsafe_allow_html=True)        

# Create 3 columns for the buttons
col1, col2, col3 = st.columns(3)

# Speech to Text Button
with col1:
    if st.button(translations[st.session_state.language_preference]["voice_query"]):
        if st.session_state.speech_in_progress:
            st.write("Stopping current speech...")
            engine.stop()  # Stop the ongoing speech
            st.session_state.speech_in_progress = False  # Reset the flag
        else:
            query = listen()
            if query:
                st.write(f"Your Query: {query}")
                response = f"Answering your query: {query}"  # Placeholder response
                st.write(f"Response: {response}")
                speak(response)  # Speak the response

# Interaction History Button
with col2:
    if st.button(translations[st.session_state.language_preference]["view_history"]):
        st.dataframe(st.session_state.interaction_log)

# Download Button
with col3:
    if st.button(translations[st.session_state.language_preference]["download_law"]):
        st.download_button(
            translations[st.session_state.language_preference]["download_button"],
            st.session_state.interaction_log.to_csv(index=False),
            file_name="interaction_history.csv"
        )
