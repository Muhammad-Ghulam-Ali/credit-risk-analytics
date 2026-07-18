# Libraries
import os
from dotenv import load_dotenv
from sqlalchemy import create_engine
from sqlalchemy import text
  

def get_engine(db_name):
    db = db_name
    load_dotenv(override=True)
    password = os.getenv('PASSWORD')
    engine = create_engine(f'mysql+pymysql://root:{password}@localhost:3306/{db}')
    return engine


if __name__ == "__main__":
    engine = get_engine('home_credit')
    with engine.connect() as conn:
        print(conn.execute(text('SELECT 1')).fetchone())