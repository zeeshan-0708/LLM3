from dotenv import load_dotenv
import os
import requests
import streamlit as st
import google.generativeai as genai
import speech_recognition as sr
from PIL import Image
import io

# Load environment variables
load_dotenv()

api_key = os.getenv("GOOGLE_API_KEY")
if api_key is None:
    st.error("API key not found. Please set the GOOGLE_API_KEY environment variable.")
    st.stop()

genai.configure(api_key=api_key)
model = genai.GenerativeModel("gemini-pro")
chat = model.start_chat(history=[])

def get_gemini_response(question):
    response = chat.send_message(question, stream=True)
    return response

def analyze_image(image):
    img_byte_arr = io.BytesIO()
    image.save(img_byte_arr, format='JPEG')
    img_byte_arr = img_byte_arr.getvalue()
    
    url = "https://example.com/api/analyze_image"  
    response = requests.post(url, files={"image": img_byte_arr})

    if response.status_code == 200:
        result = response.json()
        # Debugging: Print the raw response
        print("Response from image analysis API:", result)
        return result.get('description', 'No description available.')
    else:
        # Debugging: Print the error response
        print("Error analyzing image:", response.status_code, response.text)
        return "Failed to analyze image."

def get_speech_to_text():
    recognizer = sr.Recognizer()
    with sr.Microphone() as source:
        st.info("Listening...")
        audio = recognizer.listen(source)
        
        try:
            text = recognizer.recognize_google(audio)
            st.success(f"You said: {text}")
            return text
        except sr.UnknownValueError:
            st.error("Sorry, I did not understand that.")
        except sr.RequestError as e:
            st.error(f"Could not request results from Google Speech Recognition service; {e}")
    return ""

def clear_chat():
    st.session_state['chat_history'] = []

# Streamlit app layout
st.set_page_config(page_title="Personalized Chat Bot", layout="wide")

# Initialize chat history in session state
if 'chat_history' not in st.session_state:
    st.session_state['chat_history'] = []

st.title("🤖 Personalized Chat Bot")
st.markdown("### Ask me anything or speak your question!")

col1, col2 = st.columns([3, 1])

with col1:
    user_input = st.text_area('Your Question:', height=100, key="input", placeholder="Type your question here...")
    submit_text = st.button("🤔 Ask the Question", key="submit_text")
    submit_speech = st.button("🎤 Speak the Question", key="submit_speech")

    # Image upload functionality
    uploaded_image = st.file_uploader("Upload an Image:", type=["jpg", "jpeg", "png"])
    
    if uploaded_image is not None:
        image = Image.open(uploaded_image)
        st.image(image, caption='Uploaded Image', use_column_width=True)

        # Add Analyze Image button
        analyze_image_button = st.button("🔍 Analyze Image", key="analyze_image_button")

        if analyze_image_button:
            with st.spinner("Analyzing image..."):
                description = analyze_image(image)
                st.subheader("Image Description:")
                st.markdown(f'<div class="response-box">{description}</div>', unsafe_allow_html=True)

with col2:
    st.button("🗑️ Clear Chat History", on_click=clear_chat)

# Function to handle submission
def handle_submission(input_text):
    with st.spinner("Getting response..."):
        response = get_gemini_response(input_text)
        st.session_state['chat_history'].append(("You", input_text))
        response_text = ""
        for chunk in response:
            response_text += chunk.text + "\n"
            st.session_state['chat_history'].append(("Bot", chunk.text))
        st.subheader("The Response is:")
        st.markdown(f'<div class="response-box">{response_text}</div>', unsafe_allow_html=True)

# Speech-to-text processing
if submit_speech:
    user_input = get_speech_to_text()
    if user_input:  
        st.session_state['chat_history'].append(("You (via speech)", user_input))
        handle_submission(user_input)

# Process text-based input submission
if submit_text and user_input:
    handle_submission(user_input)

# Display chat history
st.subheader("💬 Chat History")
for role, text in st.session_state['chat_history']:
    st.write(f"**{role}:** {text}")

# Footer with additional information
st.markdown("---")
st.markdown("### About this app")
st.markdown("This app uses Google's Generative AI to answer your questions and provides speech recognition for easier interaction.")
st.markdown("Developed by [Zeeshan Khan](#) |")
