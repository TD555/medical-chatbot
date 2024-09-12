from langchain_community.tools.sql_database.tool import QuerySQLDataBaseTool
from langchain_core.prompts import PromptTemplate
from langchain_community.utilities import SQLDatabase
from langchain_core.output_parsers import StrOutputParser
from langchain_core.runnables import RunnablePassthrough
from operator import itemgetter
from langchain_openai import AzureChatOpenAI
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

connection_string = f"postgresql+psycopg2://{user}:{password}@{host}:{port}/{dbname}"
db = SQLDatabase.from_uri(connection_string)

model = os.environ.get("AZURE_OPENAI_MODEL")

llm = AzureChatOpenAI(
    deployment_name=model, api_version="2023-03-15-preview", model=model, temperature=0
)

no_data_prompt = PromptTemplate.from_template(
    """
    You are an assistant who provides human-like responses to the user's questions.
    
    If `found=True`: No data found based on the user's question, generate a concise and polite message in Russian. 
    If `found=False`: The query could not be understood, or there might be insufficient information to find the answer. Ask the user to clarify or provide more specific details.

    Make sure not to mention technical details like databases or tables, and avoid repeating the same response.

    User Question: {question}
    Found: {found}

    Answer:"""
)

sql_query_prompt = PromptTemplate.from_template(
    """
    You are a text to SQL expert.
    Given the following question from a user in Russian.
    For questions about анализы (analyses), generate a query from the 'medical_analyse' table.
    For questions about исследования (researches), generate a query from the 'medical_research' table.
    Create the appropriate SQL query to answer the user's question.
    Given that the 'medical_analyse' and 'medical_research' tables contain different columns.
    Try to logically understand what the user means by the question.
    Don't use LIMIT command in SQL query if user don't want to set a limit.
    To handle the UNION of two queries with different columns, you need to explicitly match the columns in both queries. Since the UNION operation requires both queries to have the same number of columns and in the same order, you can fill in missing columns with NULL for the table that doesn't have them.
    When using WHERE clause make it case insensitive with LOWER function like "where lower(column_name) = LOWER('value')".
    
    Input: {input}
    Database: "{table_info}"
    Top K: {top_k}
    SQL Query: """

)

answer_prompt = PromptTemplate.from_template(
    """
        You are an SQL assistant who can accurately answer based generally on SQL query results, and on 'medical_analyse' and 'medical_research' tables information.
        Given the user's question in Russian, the corresponding SQL query, and the SQL result, provide a human-like response to the user only in Russian, using formal address ("Вы").

        Key requirements:
            Don't try to invent or generate untrue answers.
            The response must be directly tailored to the user's specific question and provide a concise, accurate, clear and relevant answer based on the SQL query results and the user's question.
            The response must not mention anything related to SQL. Do not use technical words like database, table, column, etc, give easy to understand responses.
        
        User Question: {question}
        Generated SQL Query: {query}
        SQL Query Result: {result}
        
        Answer:"""
)


def answer_question(question="Напиши сколько анализов я давал?"):

    try:
        execute_query = QuerySQLDataBaseTool(db=db)
        write_query = create_sql_query_chain(llm, db, prompt=sql_query_prompt)
        
        generated_sql = write_query.invoke({"question": question})
        sql_result = execute_query.invoke({"query": generated_sql})
        
        print(generated_sql)
        
        if not sql_result or len(sql_result) == 0:
            # Generate a custom response when no data is found
                no_data_response = no_data_prompt.format(question=question, found=True if not len(sql_result) else False)
                custom_no_data_answer = llm.predict(no_data_response)
                return custom_no_data_answer.strip()
    except Exception as e:
        print(str(e)) 
        return "К сожалению, данные не найдены, пожалуйста, попробуйте еще раз."
    
    sql_chain = (
        RunnablePassthrough.assign(query=write_query).assign(
            result=itemgetter("query") | execute_query
        )
        | answer_prompt
        | llm.bind(stop=["\n\n"])
        | StrOutputParser()
    )

    result = sql_chain.invoke({"question": question})

    return result.strip()