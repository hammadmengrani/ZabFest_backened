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
# prompt = PromptTemplate(input_variables=["context", "question"], template=template)




async def ask_gemini(ask: str, system_prompt = "") -> str:
    prompt = PromptTemplate(input_variables=["context", "question"], template=system_prompt if len(system_prompt) > 0 else template)
    # Create the RetrievalQA chain with FAISS and Gemini
    qa_chain = RetrievalQA.from_chain_type(
        llm=gemini_llm,
        retriever=faiss_index.as_retriever(),
        chain_type="stuff",  # or use "map_reduce" or any other method as needed
        chain_type_kwargs={"prompt": prompt}
    )
    answer = await qa_chain.ainvoke(ask)
    return answer

async def genrate_chat_topic(self,prompt: str)->str:
    """Generate a chat topic based on the first user question."""
    system_prompt = "Generate a chat title in one sentance and should be precise in 2 to 5 words only {history} \n\n user input {input}"
    topic = await self.ask_gemini(prompt, system_prompt)
    # topic = await ask_gemini(f"{system_prompt}\n\nUser prompt: {prompt}", [], True)
    return topic.strip() if topic else "untitled chat"