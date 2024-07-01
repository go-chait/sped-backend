from langchain.agents import create_openai_tools_agent
from models.conversations import ChatEntry
from db.mongodb import Conversation


def select_chat_agent(llm, tools, prompt):
    agent = create_openai_tools_agent(llm=llm, tools=tools, prompt=prompt)

    return agent

def add_chat_to_conversation(user_id: str, chat: ChatEntry):
    Conversation.update_one(
        {"user_id": user_id},
        {"$setOnInsert": {"user_id": user_id, "conversation": []}},
        upsert=True
    )
    result = Conversation.update_one(
        {"user_id": user_id},
        {"$push": {"conversation": chat.dict()}}
    )
    return result.modified_count > 0

