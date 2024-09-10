from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.exc import SQLAlchemyError
from db import MedicalAnalysis, MedicalResearch
import os
from dotenv import load_dotenv
load_dotenv()

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


async def save_data_to_db(data):
    session = Session()
    try:
        if 'MedicalAnalysis' in data:
            for item in data['MedicalAnalysis']:
                analysis = MedicalAnalysis(**item)
                session.add(analysis)
                session.commit()
                
        elif 'MedicalResearch' in data:
            item = data['MedicalResearch']
            analysis = MedicalResearch(**item)
            session.add(analysis)
            session.commit()
            
    except SQLAlchemyError as e:
        print(f"Error saving data: {e}")
        session.rollback()
    finally:
        session.close()