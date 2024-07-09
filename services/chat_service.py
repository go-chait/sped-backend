import os
from dotenv import load_dotenv
from fastapi import Depends
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
from services.auth import get_current_user_id
from langchain_community.vectorstores import FAISS
import faiss
import logging
from langchain.retrievers import EnsembleRetriever
from langchain.tools.retriever import create_retriever_tool


load_dotenv()
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
MONGODB_URI = os.getenv("MONGODB_URI")
DB_NAME = os.getenv("DB_NAME")


async def handle_chat_query(user_id: str, query: str):
    embeddings = OpenAIEmbeddings(openai_api_key=OPENAI_API_KEY)

    vectors_folder = "sped_vectors"
    if not os.path.exists(vectors_folder):
        print("Creating a new FAISS vector store...")
        dimension = 1536 
        index = faiss.IndexFlatL2(dimension) 
        db = FAISS(embeddings, index=index, docstore=None, index_to_docstore_id={})
        db.save_local(vectors_folder)
    else:
        print("Loading existing FAISS vector store...")
        logging.info("Loading existing FAISS vvvector store...")
        db = FAISS.load_local(vectors_folder, embeddings, allow_dangerous_deserialization=True)

    faiss_embeddings = OpenAIEmbeddings(openai_api_key=OPENAI_API_KEY)

    iep_vectors_folder = "iep_vectors"
    if not os.path.exists(iep_vectors_folder):
        os.makedirs(iep_vectors_folder)

    user_folder = os.path.join(iep_vectors_folder, user_id)
    if not os.path.exists(user_folder):
        os.makedirs(user_folder)
        dimension = 1536
        index = faiss.IndexFlatL2(dimension)
        iep_db = FAISS(faiss_embeddings, index=index, docstore=None, index_to_docstore_id={})
        iep_db.save_local(user_folder)
        print("Loading new IEP FAISS vector store...")            
        logging.info("Loading new IEP FAISS vector store...")
    else:
        print("Loading exisiting IEP FAISS vector store...")  
        print(user_folder)          
        iep_db = FAISS.load_local(user_folder, faiss_embeddings, allow_dangerous_deserialization=True)

    # iep_db = get_or_create_vector_store(user_id, faiss_embeddings)

    retriever = db.as_retriever()
    iep_retriever = iep_db.as_retriever()
    ensemble_retriever = EnsembleRetriever(
        retrievers=[retriever, iep_retriever], weights=[0.5, 0.5]
    )

    retriever_tool = create_retriever_tool (ensemble_retriever, "search", "Search for information about SPED and IEP. For any questions about IEP, you must use this tool")

    @tool
    async def sped_tool(query):
        "Searches and returns info on documents or links"
        docs = ensemble_retriever.invoke(query)
        return docs

    @tool
    async def iep_tool(query):
        "Searches and returns info on documents regarding IEP of a child"
        docs = iep_retriever.invoke(query)
        return docs

    tools = [retriever_tool]

    prompt = ChatPromptTemplate.from_messages(
        [
            ("system", """Analyze the given Individualized Education Program (IEP) document and compare it with the provided Special Education (SPED) strategic plan stored in the vector stores. Extract specific information and provide a detailed comparison including:

            1. Educational Goals and Objectives
            2. Accommodation and Modification Plans
            3. Behavioral Interventions and Supports
            4. Transition Services and Post-Secondary Goals
            5. Assessment Participation and Modifications
            6. Service Delivery and Least Restrictive Environment

            For each section, reference the exact text from the IEP and SPED data, highlight any discrepancies, and provide actionable insights. Use the following structure in your response:

            1. **Summary of the IEP:**
            - Extracted goals, accommodations, interventions, etc.
            
            2. **Comparison with SPED Guidelines:**
            - Refer to specific sections in the SPED document for each aspect.
            
            3. **Identified Gaps:**
            - Highlight areas where the IEP does not meet SPED recommendations.

            4. **Recommendations:**
            - Provide detailed suggestions based on the extracted data.

            Ensure your response includes direct quotes and references from the IEP and SPED documents."""),
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
    agent_executor = AgentExecutor( agent=agent, tools=tools, max_iterations=3)

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

    config = {"configurable": {"user_id": user_id}}
    response = chain_with_history.invoke({"input": query}, config=config)
    response['history'] = get_buffer_string(response['history'])
    response_dict = {
        "data": response,
        "user_id": user_id
    }
    return response_dict