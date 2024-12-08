
import streamlit as st
import requests

# Backend API endpoints
BASE_URL = "http://127.0.0.1:8000"  
FETCH_SUMMARIZE_ENDPOINT = "/fetch-and-summarize/"
TTS_ENDPOINT = "/text-to-speech/"

def fetch_and_summarize(query, tone, platform, language="en"):
    payload = {
        "query": query,
        "language": language,
        "tone": tone,
        "platform": platform
    }
    response = requests.post(BASE_URL + FETCH_SUMMARIZE_ENDPOINT, json=payload)
    if response.status_code == 200:
        return response.json()
    else:
        st.error("Error fetching and summarizing news.")
        return None

def convert_text_to_speech(text):
    payload = {"text": text}
    response = requests.post(BASE_URL + TTS_ENDPOINT, json=payload)
    if response.status_code == 200:
        return response.json()["audio_file_path"]
    else:
        st.error("Error converting text to speech.")
        return None


st.markdown("<h1 style='text-align: center; font-size: 45px;'>Accessible Times</h1>", unsafe_allow_html=True)
st.markdown("<p style='text-align: center; font-size: 20px;'>An AI-powered news summarizer and text-to-speech app for daily updates</p>", unsafe_allow_html=True)


query = st.text_input("Enter your news search query:", placeholder="e.g., AI breakthroughs in 2024")
tone = st.selectbox("Select Tone", ["Professional", "Casual"])
platform = st.selectbox("Select Platform", ["LinkedIn", "Instagram"])

# Fetch and summarize news
if st.button("Generate"):
    if query:
        result = fetch_and_summarize(query, tone, platform)
        if result:
            st.subheader("News Summary:")
            st.write(result["summary"])
            
            st.subheader("Articles:")
            for article in result["articles"]:
                st.markdown(f"**{article['title']}**")
                st.markdown(f"{article['description']}")
                st.markdown(f"[Read more]({article['url']})")

            # Convert the summary to speech
            if st.button("Convert Summary to Speech"):
                audio_file_path = convert_text_to_speech(result["summary"])
                if audio_file_path:
                    st.audio(audio_file_path)
    else:
        st.error("Please enter a news query.")
