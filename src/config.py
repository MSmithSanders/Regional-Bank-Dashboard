from dotenv import load_dotenv
import os

load_dotenv()

SEC_USER_AGENT = os.getenv("SEC_USER_AGENT")
FDIC_API_KEY = os.getenv("FDIC_API_KEY")