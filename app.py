"""
AI Chatbot for Student Support Services -- CampusDesk AI
-----------------------------------------------------------
Generative AI chatbot with:
- FAQ-grounded answers
- PDF upload + TF-IDF based RAG
- Smart PDF actions
- Image upload + image understanding
- Conversation memory within a session
- PWA support
"""

import os
import json
from io import BytesIO

from flask import Flask, render_template, request, jsonify, send_from_directory
from pypdf import PdfReader
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity


# -----------------------------------------------------------------------
# 0. LOAD .env FILE
# -----------------------------------------------------------------------

def load_dotenv_simple(path=".env"):
    """Minimal .env loader -- avoids adding python-dotenv."""

    if not os.path.exists(path):
        return

    with open(path, "r") as f:

        for line in f:

            line = line.strip()

            if not line:
                continue

            if line.startswith("#"):
                continue

            if "=" not in line:
                continue

            key, value = line.split("=", 1)

            os.environ.setdefault(
                key.strip(),
                value.strip()
            )


load_dotenv_simple()


# -----------------------------------------------------------------------
# FLASK APP
# -----------------------------------------------------------------------

app = Flask(__name__)


# -----------------------------------------------------------------------
# 1. LOAD FAQ KNOWLEDGE BASE
# -----------------------------------------------------------------------

with open("data/faq.json", "r") as f:
    FAQ_DATA = json.load(f)


def faq_context():

    lines = []

    for item in FAQ_DATA:

        lines.append(
            f"Q: {item['question']}\n"
            f"A: {item['answer']}"
        )

    return "\n\n".join(lines)


# -----------------------------------------------------------------------
# 2. PDF + IMAGE MEMORY
# -----------------------------------------------------------------------

pdf_chunks = []
pdf_filename = None

# Complete extracted PDF text.
# Used for smart document actions.
pdf_full_text = ""

image_bytes = None
image_mime_type = None
image_filename = None


# -----------------------------------------------------------------------
# 3. PDF TEXT CHUNKING
# -----------------------------------------------------------------------

def chunk_text(text, chunk_size=500, overlap=50):

    words = text.split()

    chunks = []

    start = 0

    while start < len(words):

        end = start + chunk_size

        chunk = " ".join(
            words[start:end]
        )

        chunks.append(chunk)

        start += chunk_size - overlap

    return chunks


# -----------------------------------------------------------------------
# 4. PDF RETRIEVAL
# -----------------------------------------------------------------------

def retrieve_relevant_chunks(question, top_k=3):

    if not pdf_chunks:
        return []

    vectorizer = TfidfVectorizer(
        stop_words="english"
    )

    all_texts = pdf_chunks + [question]

    tfidf_matrix = vectorizer.fit_transform(
        all_texts
    )

    question_vector = tfidf_matrix[-1]

    chunk_vectors = tfidf_matrix[:-1]

    similarities = cosine_similarity(
        question_vector,
        chunk_vectors
    )[0]

    top_indices = similarities.argsort()[::-1][:top_k]

    relevant = [
        pdf_chunks[i]
        for i in top_indices
        if similarities[i] > 0.02
    ]

    return relevant


# -----------------------------------------------------------------------
# 5. GET GEMINI MODEL
# -----------------------------------------------------------------------

def get_gemini_model(system_prompt):

    import google.generativeai as genai

    api_key = os.environ.get(
        "GEMINI_API_KEY"
    )

    if not api_key:

        raise ValueError(
            "GEMINI_API_KEY is missing. "
            "Please check your .env file."
        )

    genai.configure(
        api_key=api_key
    )

    model = genai.GenerativeModel(
        "gemini-3.5-flash",
        system_instruction=system_prompt
    )

    return model


# -----------------------------------------------------------------------
# 6. NORMAL CHAT
# -----------------------------------------------------------------------

def ask_llm(user_question: str, history=None):

    relevant_chunks = retrieve_relevant_chunks(
        user_question
    )

    if relevant_chunks:

        pdf_context = "\n\n---\n\n".join(
            relevant_chunks
        )

        context_block = (
            "UPLOADED DOCUMENT CONTEXT:\n"
            f"{pdf_context}\n\n"
            "COLLEGE FAQ CONTEXT:\n"
            f"{faq_context()}"
        )

    else:

        context_block = (
            "COLLEGE FAQ CONTEXT:\n"
            f"{faq_context()}"
        )


    history_text = ""

    if history:

        history_lines = [

            f"{h['role'].upper()}: {h['text']}"

            for h in history[-6:]

        ]

        history_text = (
            "\n\nRECENT CONVERSATION:\n"
            + "\n".join(history_lines)
        )


    system_prompt = (

        "You are CampusDesk AI, a helpful student "
        "support assistant. "

        "Answer general questions naturally and clearly. "

        "When a question relates to the uploaded PDF "
        "or college FAQ, prefer that information. "

        "Do not invent college-specific information. "

        "If the uploaded document does not contain "
        "the required college-specific information, "
        "clearly say that. "

        "If an image is attached, carefully analyze "
        "the image and answer the user's question "
        "about it. "

        "The image may contain screenshots, questions, "
        "diagrams, notices, assignments, documents, "
        "or educational content. "

        "If the image is unclear or unreadable, "
        "say so instead of guessing. "

        "Use recent conversation to understand "
        "follow-up questions. "

        "Keep answers clear, useful, and "
        "student-friendly.\n\n"

        f"{context_block}"

        f"{history_text}"
    )


    model = get_gemini_model(
        system_prompt
    )


    content = [
        user_question
    ]


    # ---------------------------------------------------------------
    # Add image if available
    # ---------------------------------------------------------------

    if image_bytes and image_mime_type:

        from PIL import Image

        image = Image.open(
            BytesIO(image_bytes)
        )

        image.load()

        image.thumbnail(
            (1600, 1600)
        )

        content.insert(
            0,
            image
        )


    response = model.generate_content(
        content
    )

    return response.text


# -----------------------------------------------------------------------
# 7. SMART PDF ACTIONS
# -----------------------------------------------------------------------

def get_document_for_action():

    if not pdf_full_text.strip():

        raise ValueError(
            "Please upload a PDF first."
        )

    # Keep the prompt reasonably sized.
    # For very large PDFs, use the most useful
    # extracted content available.
    max_chars = 30000

    if len(pdf_full_text) <= max_chars:

        return pdf_full_text

    return (
        pdf_full_text[:max_chars]
        + "\n\n[Document continues beyond this section.]"
    )


def perform_pdf_action(action):

    document = get_document_for_action()


    # ---------------------------------------------------------------
    # ACTION: SUMMARY
    # ---------------------------------------------------------------

    if action == "summarize":

        instruction = """
Summarize the uploaded PDF for a college student.

Give:
1. A short overview
2. The main topics
3. Important facts or instructions
4. Important dates, numbers, rules, or requirements if present
5. A short "What you should remember" section

Do not invent information that is not present in the document.
Keep the answer structured and easy to study.
"""


    # ---------------------------------------------------------------
    # ACTION: MCQS
    # ---------------------------------------------------------------

    elif action == "mcqs":

        instruction = """
Create 10 multiple-choice questions from the uploaded PDF.

Requirements:
- Each question must be based only on the document.
- Give 4 options: A, B, C, D.
- Clearly identify the correct answer.
- Add a one-sentence explanation for the answer.
- Mix easy, medium, and difficult questions.
- Do not create questions from information that is not present.
"""


    # ---------------------------------------------------------------
    # ACTION: EXAM PREP
    # ---------------------------------------------------------------

    elif action == "exam_prep":

        instruction = """
Turn the uploaded PDF into an exam-preparation guide.

Include:
1. Most important topics
2. Key definitions or concepts
3. Important facts, rules, dates, or numbers
4. Topics that appear especially important
5. Possible exam questions
6. A quick revision checklist

Base everything on the uploaded document.
Do not invent college-specific information.
Keep it concise but useful for revision.
"""


    # ---------------------------------------------------------------
    # ACTION: KEY POINTS
    # ---------------------------------------------------------------

    elif action == "key_points":

        instruction = """
Extract the most important points from the uploaded PDF.

Organize them into clear headings and bullet points.

Focus on:
- Important concepts
- Rules
- Requirements
- Dates
- Numbers
- Procedures
- Important warnings or notes

Do not add information that is not supported by the document.
"""


    # ---------------------------------------------------------------
    # UNKNOWN ACTION
    # ---------------------------------------------------------------

    else:

        raise ValueError(
            "Unknown PDF action."
        )


    system_prompt = (

        "You are CampusDesk AI's document "
        "analysis assistant. "

        "You are given content extracted from "
        "a student's uploaded PDF. "

        "Your job is to perform the requested "
        "document action accurately. "

        "Use ONLY information supported by "
        "the uploaded document. "

        "Never invent facts. "

        "If the document does not contain enough "
        "information for something, say so clearly. "

        "Format the response with clear headings, "
        "bullets, and numbering where useful.\n\n"

        f"REQUEST:\n{instruction}\n\n"

        "UPLOADED PDF CONTENT:\n"

        f"{document}"
    )


    model = get_gemini_model(
        system_prompt
    )


    response = model.generate_content(
        "Perform the requested action."
    )


    return response.text


# -----------------------------------------------------------------------
# 8. HOME PAGE
# -----------------------------------------------------------------------

@app.route("/")
def home():

    return render_template(
        "index.html"
    )


# -----------------------------------------------------------------------
# 9. CHAT
# -----------------------------------------------------------------------

@app.route(
    "/chat",
    methods=["POST"]
)
def chat():

    data = request.json or {}

    user_message = data.get(
        "message",
        ""
    ).strip()

    history = data.get(
        "history",
        []
    )


    if not user_message:

        return jsonify({
            "reply": "Please type a question."
        })


    try:

        reply = ask_llm(
            user_message,
            history
        )

    except Exception as e:

        print(
            "Chat error:",
            e
        )

        reply = (
            "Sorry, something went wrong while "
            "processing your question."
        )


    return jsonify({
        "reply": reply
    })


# -----------------------------------------------------------------------
# 10. SMART PDF ACTION ROUTE
# -----------------------------------------------------------------------

@app.route(
    "/pdf-action",
    methods=["POST"]
)
def pdf_action():

    data = request.json or {}

    action = data.get(
        "action",
        ""
    ).strip().lower()


    allowed_actions = {
        "summarize",
        "mcqs",
        "exam_prep",
        "key_points"
    }


    if action not in allowed_actions:

        return jsonify({

            "success": False,

            "message": (
                "Invalid PDF action."
            )

        })


    if not pdf_full_text.strip():

        return jsonify({

            "success": False,

            "message": (
                "Please upload a PDF first."
            )

        })


    try:

        result = perform_pdf_action(
            action
        )


        return jsonify({

            "success": True,

            "action": action,

            "reply": result

        })


    except Exception as e:

        print(
            "PDF action error:",
            e
        )


        return jsonify({

            "success": False,

            "message": (
                f"Could not process the PDF: {e}"
            )

        })


# -----------------------------------------------------------------------
# 11. PDF UPLOAD
# -----------------------------------------------------------------------

@app.route(
    "/upload",
    methods=["POST"]
)
def upload():

    global pdf_chunks
    global pdf_filename
    global pdf_full_text


    if "file" not in request.files:

        return jsonify({

            "success": False,

            "message": (
                "No file uploaded."
            )

        })


    file = request.files["file"]


    if file.filename == "":

        return jsonify({

            "success": False,

            "message": (
                "No file selected."
            )

        })


    if not file.filename.lower().endswith(".pdf"):

        return jsonify({

            "success": False,

            "message": (
                "Please upload a PDF file."
            )

        })


    try:

        reader = PdfReader(
            file
        )

        full_text = ""


        for page in reader.pages:

            page_text = (

                page.extract_text(
                    extraction_mode="layout"
                )

                or ""

            )

            full_text += (
                page_text
                + "\n"
            )


        if not full_text.strip():

            return jsonify({

                "success": False,

                "message": (
                    "Couldn't extract text "
                    "from this PDF."
                )

            })


        pdf_full_text = full_text


        pdf_chunks = chunk_text(
            full_text
        )


        pdf_filename = file.filename


        return jsonify({

            "success": True,

            "message": (

                f"'{file.filename}' "
                "uploaded successfully "
                f"({len(pdf_chunks)} sections indexed)."

            ),

            "filename": file.filename

        })


    except Exception as e:

        print(
            "PDF upload error:",
            e
        )


        return jsonify({

            "success": False,

            "message": (
                f"Error processing PDF: {e}"
            )

        })


# -----------------------------------------------------------------------
# 12. IMAGE UPLOAD
# -----------------------------------------------------------------------

@app.route(
    "/upload-image",
    methods=["POST"]
)
def upload_image():

    global image_bytes
    global image_mime_type
    global image_filename


    if "file" not in request.files:

        return jsonify({

            "success": False,

            "message": (
                "No image uploaded."
            )

        })


    file = request.files["file"]


    if file.filename == "":

        return jsonify({

            "success": False,

            "message": (
                "No image selected."
            )

        })


    allowed_types = {

        "image/png",

        "image/jpeg",

        "image/webp"

    }


    if file.mimetype not in allowed_types:

        return jsonify({

            "success": False,

            "message": (
                "Please upload PNG, JPG, "
                "JPEG or WEBP."
            )

        })


    data = file.read()


    if not data:

        return jsonify({

            "success": False,

            "message": (
                "The image is empty."
            )

        })


    if len(data) > 8 * 1024 * 1024:

        return jsonify({

            "success": False,

            "message": (
                "Please upload an image "
                "smaller than 8 MB."
            )

        })


    image_bytes = data

    image_mime_type = (
        file.mimetype
    )

    image_filename = (
        file.filename
    )


    return jsonify({

        "success": True,

        "filename": file.filename,

        "message": (
            "Image uploaded successfully."
        )

    })


# -----------------------------------------------------------------------
# 13. CLEAR ATTACHMENTS
# -----------------------------------------------------------------------

@app.route(
    "/clear-attachments",
    methods=["POST"]
)
def clear_attachments():

    global pdf_chunks
    global pdf_filename
    global pdf_full_text

    global image_bytes
    global image_mime_type
    global image_filename


    pdf_chunks = []

    pdf_filename = None

    pdf_full_text = ""


    image_bytes = None

    image_mime_type = None

    image_filename = None


    return jsonify({

        "success": True,

        "message": (
            "Attachments cleared."
        )

    })


# -----------------------------------------------------------------------
# 14. PWA SUPPORT
# -----------------------------------------------------------------------

@app.route("/manifest.json")
def manifest():

    return send_from_directory(
        "static",
        "manifest.json"
    )


@app.route("/service-worker.js")
def service_worker():

    return send_from_directory(
        "static",
        "service-worker.js"
    )


# -----------------------------------------------------------------------
# 15. RUN APPLICATION
# -----------------------------------------------------------------------

if __name__ == "__main__":

    app.run(
        debug=True,
        port=5000
    )