# Text Analysis Web Application

This project is a web application that analyzes input text to identify figures of speech (metaphors and similes) and performs Part-of-Speech (POS) tagging. It uses Google's Gemini API for identifying figures of speech and the spaCy library for POS tagging.

## Features

*   **Figure of Speech Detection**: Identifies metaphors and similes in the provided text using the Gemini API.
*   **Part-of-Speech Tagging**: Tags each word in the text with its corresponding part of speech (e.g., noun, verb, adjective) using spaCy.
*   **Web Interface**: Provides a user-friendly web page to input text and view the analysis results.
*   **API Endpoint**: Exposes an `/analyze` endpoint that accepts text and returns analysis results in JSON format.

## Technology Stack

*   **Backend**: Python, Flask
*   **Natural Language Processing**:
    *   Google Gemini API (for figures of speech)
    *   spaCy (for Part-of-Speech tagging)
*   **Frontend**: HTML, CSS, JavaScript
*   **Deployment**: Configured for Google App Engine (via `app.yaml`)

## Prerequisites

*   Python 3.9+
*   pip (Python package installer)
*   Git (for cloning, if applicable)

## Setup and Installation

1.  **Clone the Repository (Optional, if you haven't already):**
    ```bash
    git clone https://github.com/MrWestburyCS/Text-Analysis
    cd <repository-directory>
    ```

2.  **Create and Activate a Virtual Environment (Recommended):**
    ```bash
    python -m venv venv
    # On Windows
    venv\Scripts\activate
    # On macOS/Linux
    source venv/bin/activate
    ```

3.  **Install Dependencies:**
    Make sure you are in the project's root directory (where `requirements.txt` is located).
    ```bash
    pip install -r requirements.txt
    ```

4.  **Download spaCy Model:**
    The application uses the `en_core_web_sm` model from spaCy.
    ```bash
    python -m spacy download en_core_web_sm
    ```

5.  **Set Up Environment Variables:**
    The application requires a Google Gemini API key.
    *   Create a file named `.env` in the root of the project directory.
    *   Add your API key to this file:
        ```
        GEMINI_API_KEY='YOUR_ACTUAL_GEMINI_API_KEY'
        ```
    *   **Important:** The `.env` file is included in the `.gitignore` file, so it will not be committed to your Git repository.
    *   Alternatively, you can set the `GEMINI_API_KEY` as an environment variable directly in your system if you prefer not to use a `.env` file for local development.

## Running the Application

1.  **Start the Flask Development Server:**
    Make sure your virtual environment is activated and you are in the project's root directory.
    ```bash
    python app.py
    ```

2.  **Access the Application:**
    Open your web browser and go to:
    [http://127.0.0.1:5000/](http://127.0.0.1:5000/)

    You should see the web interface where you can enter text for analysis.

## Project Structure

```
├── app.py                # Main Flask application logic
├── app.yaml              # Configuration for Google App Engine deployment
├── requirements.txt      # Python package dependencies
├── .gitignore            # Specifies intentionally untracked files that Git should ignore
├── static/               # Static assets for the frontend
│   ├── script.js         # JavaScript for frontend interactivity
│   └── style.css         # CSS for styling
├── templates/            # HTML templates
│   └── index.html        # Main HTML page for the application
└── README.md             # This file
```

## Deployment

This application is configured for deployment to Google App Engine using the `app.yaml` file. Ensure your `GEMINI_API_KEY` is set as an environment variable in your App Engine configuration. 