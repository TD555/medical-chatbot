from langchain_community.tools.sql_database.tool import QuerySQLDataBaseTool
from langchain_core.prompts import PromptTemplate
from langchain_community.utilities import SQLDatabase
from langchain_core.output_parsers import StrOutputParser
from langchain_core.runnables import RunnablePassthrough
from operator import itemgetter
from langchain_openai import ChatOpenAI
from langchain.chains import create_sql_query_chain
import os
from dotenv import load_dotenv

load_dotenv(override=True)


dbname = os.environ.get("POSTGRES_DB")
user = os.environ.get("POSTGRES_USER")
password = os.environ.get("POSTGRES_PASSWORD")
host = os.environ.get("POSTGRES_HOST")
port = os.environ.get("POSTGRES_PORT")

connection_string = f"postgresql+psycopg2://{user}:{password}@{host}:{port}/{dbname}"
db = SQLDatabase.from_uri(connection_string)

model = os.environ.get("OPENAI_MODEL")

llm = ChatOpenAI(
    model=model, temperature=0
)

no_data_prompt = PromptTemplate.from_template(
    """
    You are an assistant who provides human-like responses to the user's questions in Russian.
    
    If found is True: No data found for your request.
    If found is False: Please clarify or provide more details.

    Make sure not to mention technical details like databases or tables, and avoid repeating the same response.

    User Question: {question}
    Found: {found}

    Answer:"""
)

sql_query_prompt = PromptTemplate.from_template(
    """
    You are an expert in SQL generation.
    Given a user's question in Russian, generate as simple as possible SQL query based on the following rules:
    
    - Do not use 'LIMIT 5'.
    - Use in SQL query only 'medical_analyse' table if the question is about анализы (analyses) and not about исследования.
    - Use in SQL query only 'medical_research' table if the question is about исследования (researches) and not about анализы.
    - For questions about both, use both tables and match columns by filling missing columns with NULL.
    - Ensure case-insensitivity for string columns using the LOWER function and try to search with wildcards.
    - Do not apply LOWER to columns that are not strings (e.g., numeric or date columns).
    
    Input Question: {input}
    Table Info: "{table_info}"
    Top K Results: {top_k}
    
    SQL Query: 
    """
)

answer_prompt = PromptTemplate.from_template(
    """
    You are an SQL assistant, and your job is to provide accurate, clear answers in Russian based on the SQL query results.
    
    Requirements:
    - Avoid mentioning any technical or SQL-related terms such as "база данных", "таблица", "запрос", etc.
    - The answer should be in detail, tailored directly to the user's question and the SQL results.
    - The answer must be brief, specific, formal and in Russian, addressing the user as "Вы".
    - If no data is found, provide a polite but non-repetitive message.
    
    User Question: {question}
    SQL Query: {query}
    SQL Result: {result}
    
    Answer:
    """
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
        | llm
        | StrOutputParser()
    )

    result = sql_chain.invoke({"question": question})

    print(result.strip())
    
    return result.strip()
