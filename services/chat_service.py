import os
from dotenv import load_dotenv
from utils.conversations import select_chat_agent
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.runnables.history import RunnableWithMessageHistory
from langchain.agents import AgentExecutor
from langchain_community.chat_message_histories import ChatMessageHistory
from langchain.tools import tool
from langchain_mongodb.chat_message_histories import MongoDBChatMessageHistory
from langchain_core.runnables.history import RunnableWithMessageHistory
from langchain_core.runnables import ConfigurableFieldSpec
from langchain_core.messages.utils import get_buffer_string
from langchain_openai import OpenAIEmbeddings
from langchain_community.vectorstores import FAISS
import faiss
import logging


load_dotenv()
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
MONGODB_URI = os.getenv("MONGODB_URI")
DB_NAME = os.getenv("DB_NAME")

embeddings = OpenAIEmbeddings(openai_api_key=OPENAI_API_KEY)

vectors_folder = "faiss_vectors"
if not os.path.exists(vectors_folder):
    print("Creating a new FAISS vector store...")
    dimension = 1536 
    index = faiss.IndexFlatL2(dimension) 
    db = FAISS(embeddings, index=index, docstore=None, index_to_docstore_id={})
    db.save_local(vectors_folder)
else:
    print("Loading existing FAISS vector store...")
    logging.info("Loading existing FAISS vector store...")
    db = FAISS.load_local(vectors_folder, embeddings, allow_dangerous_deserialization=True)

retriever = db.as_retriever()

@tool
def tool(query):
    "Searches and returns documents regarding the llm powered autonomous agents blog"
    docs = retriever.get_relevant_documents(query)
    return docs

tools = [tool]   

prompt = ChatPromptTemplate.from_messages(
    [
        ("system", "You are a helpful assistant that can guide parents with labyrinth of SPED system."),
        ("human", "Hello, how are you doing?"),
        ("ai", "I'm doing well, how can I help you regarding SPED systems today?"),
        MessagesPlaceholder(variable_name="history"),
        ("human", "{input}"),
        MessagesPlaceholder("agent_scratchpad"),
    ]
)

def get_session_history(user_id: str) -> MongoDBChatMessageHistory:
    return MongoDBChatMessageHistory(MONGODB_URI, user_id, database_name=DB_NAME, collection_name="chat_histories")

llm = ChatOpenAI(model="gpt-3.5-turbo", temperature=0)
agent = select_chat_agent(llm, tools, prompt)
agent_executor = AgentExecutor( agent=agent, tools=tools)

chain_with_history = RunnableWithMessageHistory(
    agent_executor,
    get_session_history,
    input_messages_key="input",
    history_messages_key="history",
    history_factory_config=[
        ConfigurableFieldSpec(
            id="user_id",
            annotation=str,
            name="User ID",
            description="Unique identifier for the user.",
            default="",
            is_shared=True,
        ),
    ],
)

async def handle_chat_query(user_id: str, query: str):
    config = {"configurable": {"user_id": user_id}}
    response = chain_with_history.invoke({"input": query}, config=config)
    response['history'] = get_buffer_string(response['history'])
    response_dict = {
        "data": response,
        "user_id": user_id
    }
    return response_dict