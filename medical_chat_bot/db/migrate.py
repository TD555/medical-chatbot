from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.exc import SQLAlchemyError
from db import MedicalAnalysis, MedicalResearch
import os
from dotenv import load_dotenv
load_dotenv()

# Database connection parameters
dbname = os.environ.get('POSTGRES_DB')
user = os.environ.get('POSTGRES_USER')
password = os.environ.get('POSTGRES_PASSWORD')
host = os.environ.get('POSTGRES_HOST')
port = os.environ.get('POSTGRES_PORT')

# Define the SQLAlchemy session and engine
DATABASE_URL = f'postgresql://{user}:{password}@{host}:{port}/{dbname}?client_encoding=utf8'
engine = create_engine(DATABASE_URL)
Session = sessionmaker(bind=engine)


async def insert_data(data):
    session = Session()
    try:
        for section, model in [("MedicalAnalysis", MedicalAnalysis), ("MedicalResearch", MedicalResearch)]:
            if section in data:
                items = data[section]
                
                if not isinstance(items, list):
                    items = [items]
                    
                for item in items:
                    session.add(model(**item))
        
        session.commit()
            
    except SQLAlchemyError as e:
        raise Exception(f"Error saving data: {e}")

    finally:
        session.close()