import psycopg2
from psycopg2 import sql
from sqlalchemy import create_engine, Column, Uuid, String, DateTime, Text, Float
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from datetime import datetime
import os
from dotenv import load_dotenv
load_dotenv()

# Define the SQLAlchemy base class
Base = declarative_base()

# Define models for the tables
class MedicalAnalysis(Base):
    __tablename__ = 'medical_analyse'
    id = Column(Uuid, primary_key=True)
    test_name = Column(String, nullable=True)
    reference_min_value = Column(Float, nullable=True)
    reference_max_value = Column(Float, nullable=True)
    units = Column(String, nullable=True)
    result = Column(Float, nullable=True)
    test_date = Column(DateTime, nullable=True)
    institution = Column(String, nullable=True)
    address = Column(String, nullable=True)

class MedicalResearch(Base):
    __tablename__ = 'medical_research'
    id = Column(Uuid, primary_key=True)
    research_name = Column(String, nullable=True)
    research_date = Column(DateTime, nullable=True)
    institution = Column(String, nullable=True)
    equipment = Column(String, nullable=True)
    protocol = Column(Text, nullable=True)
    conclusion = Column(Text, nullable=True)
    recommendation = Column(Text, nullable=True)
    address = Column(String, nullable=True)

# Database connection parameters
dbname = os.environ.get('DB_NAME')
user = os.environ.get('DB_USER')
password = os.environ.get('DB_PASSWORD')
host = os.environ.get('DB_HOST')
port = os.environ.get('DB_PORT')

# Create the database if it does not exist
def create_database_if_not_exists():
    connection = psycopg2.connect(dbname='postgres', user=user, password=password, host=host)
    connection.autocommit = True
    with connection.cursor() as cursor:
        cursor.execute(sql.SQL("SELECT 1 FROM pg_database WHERE datname = %s"), [dbname])
        if not cursor.fetchone():
            cursor.execute(sql.SQL("CREATE DATABASE {}").format(sql.Identifier(dbname)))
            print(f"Database '{dbname}' created.")
            already_exists = False
        else:
            print(f"Database '{dbname}' already exists.")
            already_exists = True
    connection.close()
    
    return already_exists

# Create tables in the database
def create_tables():
    DATABASE_URL = f'postgresql://{user}:{password}@{host}:{port}/{dbname}?client_encoding=utf8'
    engine = create_engine(DATABASE_URL)
    Base.metadata.create_all(engine)
    print("Tables created.")

# Run database creation functions
if not create_database_if_not_exists():
    create_tables()
