# CampusDesk AI

**AI-Powered Student Support Chatbot using Generative AI**
IBM Generative AI Course — Project

A generative AI chatbot that answers student questions (admissions, exams, fees, library, and more) using Google's Gemini API, grounded in a curated FAQ knowledge base. It also supports uploading any college PDF (syllabus, handbook, notice) and answering questions from it using a lightweight Retrieval-Augmented Generation (RAG) pipeline.

---

## Features

**Core**
- Conversational chat interface with a custom, minimal design
- AI-generated answers powered by the Gemini API (`gemini-3.5-flash`)
- Curated FAQ knowledge base
- Suggested question chips
- Copy-to-clipboard on responses
- Voice input (Web Speech API)
- Dark / light theme toggle
- Conversation memory within a session (handles natural follow-up questions)

**Extended: Document Upload (RAG)**
- Upload any college PDF directly in the chat interface
- Text is extracted, chunked, and indexed with TF-IDF
- Cosine similarity retrieves the most relevant chunks for each question
- Only relevant chunks are passed to Gemini, grounding the answer in the actual document

**PWA**
- Installable as an app on desktop/mobile via the browser's install prompt
- Offline shell caching via a service worker

---

## Project Structure

```
student-chatbot/
├── app.py                     # Flask backend, RAG logic, Gemini integration
├── data/
│   └── faq.json                # FAQ knowledge base
├── static/
│   ├── style.css                # All styling (light/dark themes)
│   ├── script.js                # Chat logic, voice input, theme toggle
│   ├── manifest.json            # PWA manifest
│   ├── service-worker.js        # PWA offline shell caching
│   └── icons/                   # App icons for PWA install
├── templates/
│   └── index.html               # Page structure
├── notebooks/
│   └── rag_logic_walkthrough.ipynb   # Standalone demo of the RAG pipeline
├── tests/
│   └── test_core_logic.py       # Basic tests for chunking + FAQ loading
├── docs/
│   └── architecture_diagram.png # System architecture diagram
├── .env.example                 # Template for required environment variables
├── .gitignore
├── requirements.txt
└── README.md
```

---

## Setup

### 1. Install dependencies

```bash
pip install -r requirements.txt
```

### 2. Configure your API key

Copy `.env.example` to `.env` and add your Gemini API key:

```bash
cp .env.example .env
```

Then edit `.env` and replace the placeholder with your real key from
[Google AI Studio](https://aistudio.google.com/app/apikey):

```
GEMINI_API_KEY=your-real-key-here
```

`.env` is excluded from version control via `.gitignore` — never commit your real key.

### 3. Run the app

```bash
python app.py
```

Open **http://127.0.0.1:5000** in your browser.

### 4. Run tests (optional)

```bash
python tests/test_core_logic.py
```

### 5. Explore the RAG logic notebook (optional)

```bash
jupyter notebook notebooks/rag_logic_walkthrough.ipynb
```

This walks through chunking, TF-IDF vectorization, and retrieval in isolation — useful for understanding or grading the core algorithm separately from the web app.

---

## How It Works

1. The student types a question or uploads a PDF document.
2. If a PDF is uploaded, the backend extracts its text and splits it into overlapping chunks (~500 words each).
3. When a question is asked, TF-IDF vectorization converts both the question and all document chunks into numerical vectors.
4. Cosine similarity identifies the chunks most relevant to the question.
5. The relevant chunks (or FAQ data, if no document is uploaded), along with recent conversation history, are combined into a context block.
6. This context, with a system prompt, is sent to the Gemini API, which generates a natural-language answer.
7. The answer is displayed in the chat interface.

See `docs/architecture_diagram.png` for a visual overview.

---

## Known Limitations

- **Dense tabular PDF data** (e.g., semester-wise credit tables) does not extract cleanly as plain text, since PDF text extraction flattens rows and columns into a single line. This affects only structured tables — prose/paragraph content extracts and retrieves reliably. A future improvement would use table-aware parsing (e.g., `pdfplumber`).
- The uploaded PDF's index resets when the server restarts (in-memory storage) — acceptable for a demo/project scope.

---

## Tech Stack

| Category | Technology |
|---|---|
| Programming Language | Python |
| Backend Framework | Flask |
| AI / LLM API | Google Gemini API (`gemini-3.5-flash`) |
| Retrieval Technique | TF-IDF + Cosine Similarity (scikit-learn) |
| PDF Text Extraction | pypdf |
| Frontend | HTML, CSS, JavaScript |
| Data Storage | JSON (FAQ knowledge base) |

---

## Resume Title

*AI-Powered Student Support Chatbot using Generative AI*
