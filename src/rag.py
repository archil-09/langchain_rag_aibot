"""
rag.py — Handles document loading, embeddings, and answering questions
"""

import os
from langchain_groq import ChatGroq
from langchain_docling.loader import DoclingLoader
from langchain_community.vectorstores.utils import filter_complex_metadata
from langchain_huggingface import HuggingFaceEndpointEmbeddings
from langchain_chroma import Chroma
from dotenv import load_dotenv
load_dotenv()

# ── Initialize LLM ─────────────────────────────────────────────────
model = ChatGroq(
    model="llama-3.1-8b-instant",
    temperature=0.0,
    max_retries=2,
    api_key=os.getenv("GROQ_API_KEY"),
)

# ── Load and embed documents (runs once at startup) ─────────────────
def load_documents(file_path: str):
    """Load clinic documents and return retriever"""
    print(f"Loading documents from {file_path}...")
    loader = DoclingLoader(file_path=file_path)
    docs = loader.load()
    docs = filter_complex_metadata(docs)

    embeddings = HuggingFaceEndpointEmbeddings(
        model="sentence-transformers/all-mpnet-base-v2",
        huggingfacehub_api_token=os.getenv("HUGGING_FACE"),
    )

    vectorstore = Chroma.from_documents(
        documents=docs,
        embedding=embeddings,
        persist_directory="./chroma_db"
    )

    print("Documents loaded and indexed successfully!")
    return vectorstore.as_retriever(search_kwargs={"k": 3})


# ── Answer a question using RAG ─────────────────────────────────────
def ask_rag(retriever, question: str) -> str:
    """Take a question, retrieve context, return AI answer"""
    retrieved_docs = retriever.invoke(question)
    context = "\n\n".join(doc.page_content for doc in retrieved_docs)

    prompt = f"""
    You are a helpful dental clinic assistant.
    Answer the user's question using ONLY the context below.
    If the answer is not in the context, say:
    "I don't have that information. Please call the clinic directly."

    Context:
    {context}

    Question:
    {question}
    """

    response = model.invoke(prompt)
    return response.content


# ── Detect intent of user message ──────────────────────────────────
def detect_intent(message: str) -> str:
    """
    Returns one of:
    - 'book'        → user wants to book appointment
    - 'reschedule'  → user wants to reschedule
    - 'cancel'      → user wants to cancel
    - 'status'      → user wants to check their appointment
    - 'faq'         → general question
    """
    prompt = f"""
    Classify this WhatsApp message from a dental clinic patient into ONE of these categories:
    - book (wants to book a new appointment)
    - reschedule (wants to change existing appointment)
    - cancel (wants to cancel appointment)
    - status (wants to check their appointment details)
    - faq (any other general question)

    Message: "{message}"

    Reply with ONLY one word from the list above. Nothing else.
    """
    response = model.invoke(prompt)
    intent = response.content.strip().lower()

    # Fallback to faq if unexpected response
    if intent not in ["book", "reschedule", "cancel", "status", "faq"]:
        return "faq"
    return intent