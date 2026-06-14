from langchain_groq import ChatGroq
from dotenv import load_dotenv



import os
load_dotenv()
groq_api_key = os.getenv("GROQ_API_KEY")
model = ChatGroq(
    model="llama-3.1-8b-instant",
    temperature=0.0,
    max_retries=2,
    api_key=groq_api_key,

    # other params...
)
messages = [
    ("system", "You are a helpful translator. Translate the user sentence to French."),
    ("human", "I love programming."),
]
response=model.invoke(messages)
print(response.content)
from langchain_docling.loader import DoclingLoader

FILE_PATH = 'data/Dental_Clinic_RAG_Documents.docx'

loader = DoclingLoader(file_path=FILE_PATH)
docs = loader.load()
for doc in docs:
    print(doc.page_content)
    print("-" * 100)
from langchain_community.vectorstores.utils import filter_complex_metadata

docs = filter_complex_metadata(docs)
from langchain_huggingface import HuggingFaceEmbeddings

embeddings = HuggingFaceEmbeddings(model_name="sentence-transformers/all-mpnet-base-v2")

query_embedding = embeddings.embed_query("what is dental hygiene")
doc_embeddings = embeddings.embed_documents(
    [
      doc.page_content for doc in docs
    ]
)
from langchain_chroma import Chroma

vectorstore = Chroma.from_documents(
    documents=docs,
    embedding=embeddings,
    persist_directory="./chroma_db"
)
retriever = vectorstore.as_retriever(
    search_kwargs={"k": 3}
)
results = retriever.invoke(
    "What should I do during a dental emergency?"
)
for doc in results:
    print(doc.page_content)
question = ""
while(question!='exit'):
    question = input("What is the question?")
    retrieved_docs = retriever.invoke(question)
    context = "\n\n".join(
        doc.page_content for doc in retrieved_docs
    )

    prompt = f"""
    You are a helpful dental clinic assistant.

    Answer the user's question using ONLY the context below.

    Context:
    {context}

    Question:
    {question}
    """

    response = model.invoke(prompt)

    print(response.content)


