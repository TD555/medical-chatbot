from langchain_community.tools.sql_database.tool import QuerySQLDataBaseTool
from langchain_core.prompts import PromptTemplate
from langchain_community.utilities import SQLDatabase
from langchain_core.output_parsers import StrOutputParser
from langchain_core.runnables import RunnablePassthrough
from operator import itemgetter
from langchain_openai import AzureOpenAI
from langchain.chains import create_sql_query_chain
import os
from dotenv import load_dotenv
load_dotenv()


# Database connection parameters
dbname = os.environ.get('POSTGRES_DB')
user = os.environ.get('POSTGRES_USER')
password = os.environ.get('POSTGRES_PASSWORD')
host = os.environ.get('POSTGRES_HOST')
port = os.environ.get('POSTGRES_PORT')

connection_string= f"postgresql+psycopg2://{user}:{password}@{host}:{port}/{dbname}"
db = SQLDatabase.from_uri(connection_string)

model = os.environ.get('AZURE_OPENAI_MODEL')

llm = AzureOpenAI(
    deployment_name=model,
    api_version="2023-03-15-preview",
    model=model,
    temperature=0
)

sql_query_prompt = PromptTemplate.from_template(
    """Given the following user question in Russian, from the 'medical_analyse' and 'medical_research' tables
    generate the corresponding SQL query that retrieves the answer.
    
Input: {input}
Database: "{table_info}"
Top K: {top_k}
SQL Query: """
)

answer_prompt = PromptTemplate.from_template(
    """Given the user's question in Russian, the corresponding SQL query, and the SQL result, 
       provide a human-like response to the user in Russian, using formal address ('Вы'). 
       
       Important prerequisites:
        The answer should not mention database, table or any technical words.
        The answer should be as specific and detailed as possible.
        The response should only address the user's question and not include information unrelated to it.
        
User Question: {question}
Generated SQL Query: {query}
SQL Query Result: {result}

Answer: """
)



def answer_question(question="Напиши сколько анализов я давал?"):
    
    execute_query = QuerySQLDataBaseTool(db=db)
    write_query = create_sql_query_chain(llm, db, prompt=sql_query_prompt)
    sql_chain = (
        RunnablePassthrough.assign(query=write_query).assign(
            result=itemgetter("query") | execute_query)
        | answer_prompt
        | llm.bind(stop=["\n\n"])
        | StrOutputParser()
    )

    result = sql_chain.invoke({"question": question})
    
    return result.strip()