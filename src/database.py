import os
import dotenv
from sqlalchemy import create_engine
import sqlalchemy

def database_connection_url():
    dotenv.load_dotenv()


    return os.environ.get("POSTGRES_URI")

engine = create_engine("postgresql://postgres:Pablituminguet12.@db.oucjsoobcnpwdnqsvoyx.supabase.co:5432/postgres", pool_pre_ping=True)
