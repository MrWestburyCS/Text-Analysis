import os
import enum
import logging
import json
from flask import Flask, request, jsonify, render_template
from pydantic import BaseModel, Field, ValidationError
import google.generativeai as genai
from google.generativeai.types import HarmCategory, HarmBlockThreshold
from dotenv import load_dotenv
import spacy # Ensure spaCy is imported

# --- Configuration ---
load_dotenv()
API_KEY = os.getenv("GEMINI_API_KEY")

if not API_KEY:
    raise ValueError("GEMINI_API_KEY not found in environment variables.")

genai.configure(api_key=API_KEY)
logging.basicConfig(level=logging.INFO)

# --- Load spaCy Model ---
try:
    nlp = spacy.load("en_core_web_sm")
    logging.info("spaCy model 'en_core_web_sm' loaded successfully.")
except OSError:
    logging.error(
        "Could not find spaCy model 'en_core_web_sm'. "
        "Please run: python -m spacy download en_core_web_sm"
    )
    nlp = None

# --- Pydantic Model (for Gemini validation) ---
class FigureOfSpeechType(str, enum.Enum):
    METAPHOR = "metaphor"
    SIMILE = "simile"

class FoundFigure(BaseModel):
    type: FigureOfSpeechType
    text: str

# --- Flask App Setup ---
app = Flask(__name__)

# --- Gemini Model Configuration ---
# (Keep Gemini config as before)
base_generation_config = {
    "temperature": 0.2, "top_p": 1, "top_k": 1, "max_output_tokens": 4096,
}
safety_settings = {
    HarmCategory.HARM_CATEGORY_HARASSMENT: HarmBlockThreshold.BLOCK_MEDIUM_AND_ABOVE,
    HarmCategory.HARM_CATEGORY_HATE_SPEECH: HarmBlockThreshold.BLOCK_MEDIUM_AND_ABOVE,
    HarmCategory.HARM_CATEGORY_SEXUALLY_EXPLICIT: HarmBlockThreshold.BLOCK_MEDIUM_AND_ABOVE,
    HarmCategory.HARM_CATEGORY_DANGEROUS_CONTENT: HarmBlockThreshold.BLOCK_MEDIUM_AND_ABOVE,
}
model = genai.GenerativeModel(
    model_name="gemini-2.0-flash",
    safety_settings=safety_settings,
    generation_config=base_generation_config
)
openapi_schema = {
    "type": "ARRAY",
    "items": {
        "type": "OBJECT",
        "properties": {
            "type": {"type": "STRING", "enum": ["metaphor", "simile"]},
            "text": {"type": "STRING"}
        },
        "required": ["type", "text"],
    }
}

POS_TAG_MAP = {
    "ADJ": "adjective", "ADP": "adposition", "ADV": "adverb", "AUX": "auxiliary",
    "CONJ": "conjunction", "CCONJ": "coord_conjunction", "DET": "determiner",
    "INTJ": "interjection", "NOUN": "noun", "NUM": "numeral", "PART": "particle",
    "PRON": "pronoun", "PROPN": "proper_noun", "PUNCT": "punctuation",
    "SCONJ": "subord_conjunction", "SYM": "symbol", "VERB": "verb", "X": "other",
    "SPACE": "space" # spaCy sometimes tags whitespace
}

def find_parts_of_speech(text):
    """
    Processes text using spaCy to find ALL parts of speech.

    Args:
        text (str): The input text string.

    Returns:
        list: A list of dictionaries, e.g.,
              [{'type': 'determiner', 'text': 'The'}, ...]
              Returns an empty list if spaCy model is not loaded.
    """
    if not nlp:
        logging.warning("spaCy model not loaded, skipping POS tagging.")
        return []

    doc = nlp(text)
    pos_results = []

    for token in doc:

        pos_tag = token.pos_
        if pos_tag != "SPACE": # Usually don't need to highlight spaces
             pos_type = POS_TAG_MAP.get(pos_tag, pos_tag.lower()) 
             pos_results.append({"type": pos_type, "text": token.text})

    logging.info(f"spaCy found {len(pos_results)} tagged tokens.")
    return pos_results


# --- Routes ---
@app.route('/')
def index():
    """Serves the main HTML page."""
    # Pass the list of tag types to the template for checkbox generation
    # Combine figure types and POS types
    tag_types = ["metaphor", "simile"] + sorted(list(POS_TAG_MAP.values()))
    # Remove 'space' if it was accidentally included
    if 'space' in tag_types: tag_types.remove('space')

    return render_template('FrontEndAccess.html', tag_types=tag_types)

@app.route('/analyze', methods=['POST'])
def analyze_text():
    """
    Receives text, analyzes using Gemini (figures of speech) and
    spaCy (parts of speech), and returns combined results.
    """
    if not request.json or 'text' not in request.json:
        return jsonify({"error": "Missing 'text' in request body"}), 400

    input_text = request.json['text']
    if not input_text.strip():
         return jsonify({"error": "Input text cannot be empty"}), 400

    logging.info(f"Received text for analysis: {input_text[:100]}...")

    analysis_results = { "figures_of_speech": [], "parts_of_speech": [], "errors": [] }
    gemini_error = None
    spacy_error = None

    # --- 1. Perform spaCy Analysis ---
    try:
        # This now returns ALL tags
        analysis_results["parts_of_speech"] = find_parts_of_speech(input_text)
    except Exception as e:
        logging.error(f"Error during spaCy analysis: {e}")
        spacy_error = "Failed to analyze parts of speech."
        analysis_results["errors"].append(spacy_error)

    # --- 2. Perform Gemini Analysis (Keep existing logic) ---
    prompt = f"""Please analyze the following text to identify metaphors and similes.
Return your findings strictly as a JSON list. Each item in the list must be an object containing exactly two keys:
1.  `type`: Must be either "metaphor" or "simile".
2.  `text`: Must be the exact text segment identified.
Ensure every object in the list has both the 'type' and 'text' keys.
Text to analyze:\n---\n{input_text}\n---\nJSON List:"""
    json_generation_config = {
        "response_mime_type": "application/json",
        "response_schema": openapi_schema,
    }
    try:
        response = model.generate_content(prompt, generation_config=json_generation_config)

        if response.prompt_feedback and response.prompt_feedback.block_reason:
             gemini_error = f"Figure of speech analysis blocked ({response.prompt_feedback.block_reason})."
        elif not hasattr(response, 'text') or not response.text:
             gemini_error = "Figure of speech analysis returned empty response." 
        else:
            try:
                raw_parsed_data = json.loads(response.text)
                if isinstance(raw_parsed_data, list):
                    validated_figures_list = []
                    for item in raw_parsed_data:
                        try:
                            if isinstance(item, dict):
                                validated_figure = FoundFigure(**item)
                                validated_figures_list.append(validated_figure.model_dump())
                        except ValidationError:
                            pass # Skip invalid items silently or log warning
                    analysis_results["figures_of_speech"] = validated_figures_list
                else:
                     gemini_error = "Gemini returned unexpected data format."
            except json.JSONDecodeError:
                gemini_error = "Gemini returned invalid JSON."
            except Exception as parse_error:
                 gemini_error = f"Failed to process Gemini response: {parse_error}"

        if gemini_error:
            analysis_results["errors"].append(gemini_error)

    except Exception as e:
        logging.error(f"Error calling Gemini API: {e}")
        gemini_error = "Error communicating with figure of speech analysis API."
        analysis_results["errors"].append(gemini_error)

    return jsonify(analysis_results)


if __name__ == '__main__':
    if nlp is None:
        print("spaCy model 'en_core_web_sm' not found. Please install it.")
        print("Run: python -m spacy download en_core_web_sm")
    app.run()

