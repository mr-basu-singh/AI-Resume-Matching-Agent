import os
from dotenv import load_dotenv
from langchain_groq import ChatGroq

load_dotenv()

# --------------------------------------------------
# SINGLETON: reuse one client instead of creating a
# new ChatGroq connection on every single call
# --------------------------------------------------
_llm_instance = None


def get_llm():
    global _llm_instance

    if _llm_instance is None:
        _llm_instance = ChatGroq(
            model="llama-3.3-70b-versatile",
            temperature=0
        )

    return _llm_instance
