from langchain.vectorstores import FAISS
import pickle
from langchain.chains import RetrievalQA
from langchain.prompts import PromptTemplate
from models.Gemini import GeminiLLM
from models.Prompt import template

# Initialize the Gemini LLM model
gemini_llm = GeminiLLM()

# Load the FAISS index from the pickle file
with open("faiss_index.pkl", "rb") as f:
    faiss_index = pickle.load(f)
print(type(faiss_index))

# Create a PromptTemplate with the loaded template
prompt = PromptTemplate(input_variables=["context", "question"], template=template)

# Create the RetrievalQA chain with FAISS and Gemini
qa_chain = RetrievalQA.from_chain_type(
    llm=gemini_llm,
    retriever=faiss_index.as_retriever(),
    chain_type="stuff",  # or use "map_reduce" or any other method as needed
    chain_type_kwargs={"prompt": prompt}
)


async def ask_gemini(ask: str) -> str:
    answer = await qa_chain.ainvoke(ask)
    return answer

