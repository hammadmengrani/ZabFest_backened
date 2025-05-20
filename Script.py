import pickle
from pymongo import MongoClient
from langchain.schema import Document
from langchain.embeddings import HuggingFaceEmbeddings
from langchain.vectorstores import FAISS
from langchain.prompts import PromptTemplate
from langchain.chains import RetrievalQA
from langchain.llms.base import LLM
import google.generativeai as genai
from typing import Optional, List

# Step 1: Configure Gemini API
genai.configure(api_key="AIzaSyD5xpx54iRKW2ljyK95gFepJ7irbzhK3W8")  # Replace with your key

# Step 2: Custom LLM Wrapper
class GeminiLLM(LLM):
    model_name: str = "gemini-2.0-flash"

    def _call(self, prompt: str, stop: Optional[List[str]] = None, **kwargs) -> str:
        model = genai.GenerativeModel(self.model_name)
        response = model.generate_content(prompt)
        return response.text.strip() if response.text else "No response generated."

    @property
    def _llm_type(self) -> str:
        return "google_gemini"

# Step 3: Fetch products from MongoDB
client = MongoClient("mongodb+srv://hammadmengrani05:zgHTJ7ug0qfsJsQH@zabfest.brf4gwu.mongodb.net/")
db = client["marketplace"]
products_collection = db["products"]

documents = []
for product in products_collection.find():
    text = f"""
Title: {product.get('title', '')}
Short Description: {product.get('short_description', '')}
Full Description: {product.get('description', '')}
Brand: {product.get('brand', '')}
Price: {product.get('price', '')}
Sale Price: {product.get('sale_price', '')}
Category: {', '.join(product.get('category', []))}
SKU: {product.get('sku', '')}
"""
    metadata = {
        "id": str(product["_id"]),
        "title": product.get("title", ""),
        "brand": product.get("brand", ""),
        "price": product.get("price", ""),
        "sale_price": product.get("sale_price", ""),
        "category": product.get("category", []),
        "sku": product.get("sku", ""),
        "image_url": product.get("image_url", "")
    }
    documents.append(Document(page_content=text, metadata=metadata))

# Optional: Save documents (if needed)
with open("products.pkl", "wb") as f:
    pickle.dump(documents, f)
print("✅ Saved products.pkl")

# Step 5: Load embeddings
embedding_model = HuggingFaceEmbeddings(
    model_name="sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2",
    model_kwargs={'device': 'cpu'},
    encode_kwargs={'normalize_embeddings': True}
)

# Step 6: Create FAISS vectorstore
vectorstore = FAISS.from_documents(documents, embedding_model)
print("✅ FAISS index created")

# --- SAVE FAISS index to pkl ---
with open("faiss_index.pkl", "wb") as f:
    pickle.dump(vectorstore, f)
print("✅ FAISS index saved as faiss_index.pkl")

# Step 7: Create prompt template
prompt_template = PromptTemplate(
    input_variables=["context", "question"],
    template = """
You are a professional assistant specializing in helping users find products that best match their specific needs and preferences. 
Your task is to provide highly accurate and helpful answers based on the detailed product context provided. When responding to user queries, ensure that your answers are clear, comprehensive, and tailored to the user's unique request. Be sure to reference key product features, specifications, and any other relevant information from the provided context. Your responses should not only answer the immediate question but also guide users by offering insights into product performance, variations, or comparisons when applicable.

Whenever you provide an answer, include relevant product metadata at the end to help the user make an informed decision. This metadata should encompass crucial attributes such as the product's category, pricing (in PKR), availability, reviews, ratings, brand, and any special offers or discounts. If the user requests detailed comparisons or more specific information, take care to emphasize differences between products where relevant and offer precise recommendations. Always keep the user's intent in mind, whether they prioritize cost, features, style, or availability.

Context:  
{context}

User Question:  
{question}

Answer:  
"""
)

# Step 8: Setup RetrievalQA
qa_chain = RetrievalQA.from_chain_type(
    llm=GeminiLLM(),
    retriever=vectorstore.as_retriever(),
    chain_type="stuff",
    chain_type_kwargs={"prompt": prompt_template}
)

# Step 9: Ask question
question = "I want original Nike running shoes under "
answer = qa_chain.run(question)

print("\n📌 Answer:\n", answer)
