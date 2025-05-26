from langchain.vectorstores import FAISS
import pickle
from langchain.chains import RetrievalQA
from langchain.prompts import PromptTemplate
from langchain.memory import ConversationBufferMemory
from langchain.chains import ConversationChain
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


async def ask(prompt:str,ask: str, history = [], isTopic = False) -> str:
        prompt = PromptTemplate(input_variables=["history", "input"], template=prompt)
        memory = ConversationBufferMemory(memory_key="history")
        memory.clear()
        conversation_chain = ConversationChain(llm=gemini_llm, memory=memory, prompt=prompt, verbose=False)
        if not isTopic:
            for item in history:
                memory.save_context({"input": item["question"]}, {"output": item["answer"]})
        response = await conversation_chain.ainvoke(ask)  # ✅ async support
        return response["response"]

async def genrate_chat_topic(prompt: str)->str:
    """Generate a chat topic based on the first user question."""
    system_prompt = "Give me topic of this chat in 2 to 5 words only. Do not include any special characters or punctuation. If you can't find a topic, return 'untitled chat'. {history} user question: {input}"
    topic = await ask(f"{system_prompt}", prompt, [], True)
    return topic.strip() if topic else "untitled chat"