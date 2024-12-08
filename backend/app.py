import json
from datetime import datetime, timedelta

import requests
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

app = FastAPI()

# Keys and Constants
VECTARA_API_KEY = "zut_PkP5QQ7kCkke_1lVsz5l1uGuK7OOM0mTNuFgrA"
VECTARA_CUSTOMER_ID = "1044642113"
VECTARA_CORPUS_ID = "black-holes-sample-data"
NEWSAPI_KEY = "e17cc78c8aad4a89a4059f2387df220f"
XI_API_KEY = "sk_c6c4356ddace668cd51bf698c4db0cab0daac35ca3c432a7"
VOICE_ID = "9BWtsMINqrJLrRacOk9x"
OUTPUT_PATH = "output.mp3"
CHUNK_SIZE = 1024


# Pydantic Models
class QueryRequest(BaseModel):
    query: str
    language: str = "en"
    tone: str = "neutral"
    platform: str = "general"


class TTSRequest(BaseModel):
    text: str


@app.post("/fetch-and-summarize/")
def fetch_and_summarize(request: QueryRequest):
    """
    Fetch news articles from NewsAPI, summarize them using Vectara,
    and return the titles, URLs, and a combined summary tailored to tone and platform.
    """
    articles = fetch_news_articles(request.query, request.language)
    if not articles:
        raise HTTPException(status_code=404, detail="No news articles found.")

    combined_content = " ".join(
        article.get("description") or article.get("content") or ""
        for article in articles
        if article.get("description") or article.get("content")
    )

    if combined_content.strip():
        summary = summarize_with_vectara(
            combined_content, request.tone, request.platform
        )
    else:
        summary = "No content available to summarize."

    summarized_articles = [
        {
            "title": article.get("title", "No title"),
            "url": article.get("url", "#"),
            "description": article.get("description", "No description available"),
        }
        for article in articles
    ]

    return {"summary": summary, "articles": summarized_articles}


@app.post("/text-to-speech/")
def text_to_speech(request: TTSRequest):
    """
    Convert the provided summary text to speech and return the audio file path.
    """
    try:
        audio_file_path = convert_text_to_speech(request.text)
        return {"audio_file_path": audio_file_path}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


def fetch_news_articles(query, language="en"):
    """
    Fetch news articles from NewsAPI, sorted by popularity, for the last 7 days.
    """
    url = "https://newsapi.org/v2/everything"

    today = datetime.now()
    one_week_ago = today - timedelta(days=7)
    from_date = one_week_ago.strftime("%Y-%m-%d")
    to_date = today.strftime("%Y-%m-%d")

    params = {
        "q": query,
        "language": language,
        "from": from_date,
        "to": to_date,
        "sortBy": "popularity",
        "apiKey": NEWSAPI_KEY,
    }
    response = requests.get(url, params=params)
    if response.status_code == 200:
        return response.json().get("articles", [])
    else:
        print(f"Error fetching news: {response.status_code} - {response.text}")
        return []


def sanitize_input(text, max_length=20000):
    """
    Sanitize input by removing unwanted characters and truncating text.
    """
    sanitized_text = text.replace("\n", " ").replace("\r", " ").strip()
    if len(sanitized_text) > max_length:
        sanitized_text = sanitized_text[:max_length] + "..."
    return sanitized_text


def summarize_with_vectara(combined_content, tone, platform):
    """
    Summarize combined articles' content using Vectara's API with tone and platform.
    """
    headers = {
        "x-api-key": VECTARA_API_KEY,
        "customer-id": VECTARA_CUSTOMER_ID,
        "Content-Type": "application/json",
    }
    sanitized_content = sanitize_input(combined_content)

    prompt_template = [
        {"role": "system", "content": "You are a helpful assistant."},
        {
            "role": "user",
            "content": f"Summarize the following content in a {tone} tone for the {platform} platform: {sanitized_content}",
        },
    ]

    prompt_template_string = json.dumps(prompt_template)

    payload = {
        "query": sanitized_content,
        "search": {"corpora": [{"corpus_key": VECTARA_CORPUS_ID}]},
        "generation": {
            "generation_preset_name": "vectara-summary-ext-v1.2.0",
            "prompt_template": prompt_template_string,
            "response_language": "eng",
            "max_response_characters": 2000,
            "enable_factual_consistency_score": True,
        },
        "save_history": True,
    }

    response = requests.post(
        "https://api.vectara.io/v2/query", json=payload, headers=headers
    )
    if response.status_code == 200:
        data = response.json()
        summary = data.get("summary", "No summary available.")
        return summary
    else:
        print(
            f"Error summarizing with Vectara: {response.status_code} - {response.text}"
        )
        return "No summary available."


def convert_text_to_speech(text_to_speak):
    """
    Converts the provided text to speech using ElevenLabs API and saves the audio as an MP3 file.

    Args:
        text_to_speak (str): The text to convert into speech.

    Returns:
        str: Path to the generated audio file.

    Raises:
        ValueError: If the text_to_speak is empty or invalid.
        Exception: If the API request fails.
    """
    if not text_to_speak.strip():
        raise ValueError("The text_to_speak parameter must not be empty.")

    tts_url = f"https://api.elevenlabs.io/v1/text-to-speech/{VOICE_ID}/stream"

    headers = {"Accept": "application/json", "xi-api-key": XI_API_KEY}

    data = {
        "text": text_to_speak,
        "model_id": "eleven_multilingual_v2",
        "voice_settings": {
            "stability": 0.5,
            "similarity_boost": 0.8,
            "style": 0.0,
            "use_speaker_boost": True,
        },
    }

    response = requests.post(tts_url, headers=headers, json=data, stream=True)

    if response.ok:
        with open(OUTPUT_PATH, "wb") as f:
            for chunk in response.iter_content(chunk_size=CHUNK_SIZE):
                f.write(chunk)
        return OUTPUT_PATH
    else:
        raise Exception(f"Error generating speech: {response.text}")
