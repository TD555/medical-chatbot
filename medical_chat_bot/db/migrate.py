from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.exc import SQLAlchemyError
from db import MedicalAnalysis, MedicalResearch
import os
from dotenv import load_dotenv
load_dotenv()

# Create a mapping between keys and models
MODEL_MAPPING = {
    "MedicalAnalysis": MedicalAnalysis,
    "MedicalResearch": MedicalResearch
}

# Database connection parameters
dbname = os.environ.get('DB_NAME')
user = os.environ.get('DB_USER')
password = os.environ.get('DB_PASSWORD')
host = os.environ.get('DB_HOST')
port = os.environ.get('DB_PORT')

# Define the SQLAlchemy session and engine
DATABASE_URL = f'postgresql://{user}:{password}@{host}:{port}/{dbname}'
engine = create_engine(DATABASE_URL)
Session = sessionmaker(bind=engine)

from datetime import datetime
from dateutil import parser

async def save_data_to_db(data, medical_type='MedicalAnalysis'):
    session = Session()
    try:
        # Save to medical_analyses or medical_research based on data type
        data['test_date'] = parser.parse(data['test_date'])
        analysis = MedicalAnalysis(**data)
        session.add(analysis)
        session.commit()
    except SQLAlchemyError as e:
        print(f"Error saving data: {e}")
        session.rollback()
    finally:
        session.close()