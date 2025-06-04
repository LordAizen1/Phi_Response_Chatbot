from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import spacy
import requests
import json

# Load the spaCy model outside the endpoint for efficiency
try:
    nlp = spacy.load("en_core_web_sm")
except OSError:
    print("Downloading en_core_web_sm model. This will only happen once.")
    from spacy.cli import download
    download("en_core_web_sm")
    nlp = spacy.load("en_core_web_sm")

app = FastAPI()

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], # Allows all origins
    allow_credentials=True,
    allow_methods=["*"], # Allows all methods
    allow_headers=["*"], # Allows all headers
)

class PromptRequest(BaseModel):
    prompt: str

@app.post("/process_prompt")
async def process_prompt(request: PromptRequest):
    """
    Receives a prompt, performs NER with spaCy, sends to Ollama, and prints results.
    """
    user_prompt = request.prompt

    # 1. Perform NER with spaCy
    doc = nlp(user_prompt)
    detected_entities = []
    for ent in doc.ents:
        detected_entities.append({"text": ent.text, "label": ent.label_, "start": ent.start_char, "end": ent.end_char})

    print("\n--- Detected Entities ---")
    if detected_entities:
        for entity in detected_entities:
            print(f"Text: {entity['text']}, Label: {entity['label']}")
    else:
        print("No entities detected.")
    print("-------------------------")

    # 2. Send prompt to Ollama REST API
    ollama_url = "http://localhost:11434/api/generate"
    model_name = "phi" # Replace with the model you have downloaded in Ollama

    payload = {
        "model": model_name,
        "prompt": user_prompt,
        "stream": False # We're not streaming for this task
    }

    llm_response_text = "Could not get response from LLM."
    try:
        print("\n--- Sending to Ollama ---")
        response = requests.post(ollama_url, json=payload)
        response.raise_for_status() # Raise an exception for bad status codes
        result = response.json()
        llm_response_text = result.get("response", "No response field in Ollama output.")
        print("Received response from Ollama.")
    except requests.exceptions.RequestException as e:
        print(f"Error calling Ollama API: {e}")
    except json.JSONDecodeError:
        print("Error decoding JSON response from Ollama.")

    # 3. Print LLM response to console
    print("\n--- LLM Response ---")
    print(llm_response_text)
    print("--------------------")

    return {"status": "processing complete", "entities": detected_entities, "llm_response": llm_response_text}