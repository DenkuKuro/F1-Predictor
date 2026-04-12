import os
import psycopg2
from dotenv import load_dotenv

load_dotenv()

DATABASE_URL: str = os.environ.get("DATABASE_URL")

def get_db_conn():
    return psycopg2.connect(DATABASE_URL)
