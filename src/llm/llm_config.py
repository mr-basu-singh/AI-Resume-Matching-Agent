import os
from dotenv import load_dotenv
from langchain_groq import ChatGroq

load_dotenv()

# --------------------------------------------------
# SINGLETON: reuse one client instead of creating a
#