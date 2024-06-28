from langchain.agents import tool
from langchain.agents.openai_functions_agent.base import OpenAIFunctionsAgent
from langchain.schema import SystemMessage
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain.chat_models import ChatOpenAI
from langchain_community.vectorstores import FAISS
from langchain.agents import AgentExecutor

vectors = "./vectors"
system_message = SystemMessage(
        content=(
            "You are a helpful AI that summarizes all the Special Education information"
            "Do your best to answer the questions. "
        )
)
db = FAISS.load_local(vectors)
retriever = db.as_retriever()

@tool
def tool(query):
    "Summarize all information regarding SPED"
    docs = retriever.get_relevant_documents(query)
    return docs

tools = [tool]

prompt = ChatPromptTemplate.from_messages(
    [
        ("system", "You are a helpful assistant that can guide parents with labyrinth of SPED system."),
        MessagesPlaceholder("chat_history", optional=True),
    ]
)
llm = ChatOpenAI(model="gpt-3.5-turbo", temperature=0)
agent = OpenAIFunctionsAgent(llm=llm, tools=tools, prompt=prompt)
agent_executor = AgentExecutor(agent=agent, tools=tools)

def summarize():
    result = agent_executor.invoke({"input:" "Is my child getting enough SPED services from school?"
    "What are all the options available today in the school and in future as a student progresses in the school?"
    "What are the options available outside the school system?"})
    return result