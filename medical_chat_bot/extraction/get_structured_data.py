import re
import os
import google.generativeai as genai
import json
from dotenv import load_dotenv
load_dotenv()

GEMINI_MODEL = 'gemini-pro'
GOOGLE_API_KEY = os.environ.get('GOOGLE_API_KEY')

genai.configure(api_key=GOOGLE_API_KEY)
model = genai.GenerativeModel(GEMINI_MODEL)


# Define the prompt template for extracting structured data as JSON
prompt_template = """
You are an AI assistant capable of extracting structured information from medical documents. Given a passage, extract specific information and return it only as a JSON object. The JSON should include one of the following fields depending on the type of document:

MedicalAnalysis (анализы):
test_name (e.g., Гемоглобин, Глюкоза)
reference_values (e.g., norms for the test, for example: 14.5-30)
units (e.g., г/дл, %)
result (e.g., numerical values or text, for example: 50)
test_date (e.g., 24/06/2020)
institution (e.g., the name of the medical institution (ФГАУ Национальный медицинский иссле­довательский центр здоровья детей Минздрава России))
address (e.g., Москва, Ломоносовский просп., 2, стр. 1)

MedicalResearch (исследования):
research_name (e.g., "Ультразвуковое исследование")
research_date (e.g., 24/06/2020)
institution (e.g., the name of the medical institution (ФГАУ Национальный медицинский иссле­довательский центр здоровья детей Минздрава России))
equipment (e.g., the equipment used for the study)
protocol 
conclusion (e.g., Достоверных МР-данных за наличие изменений очагового и диффузного характера в веществе мозга не
получено.)
recommendations
address (e.g., Москва, Ломоносовский просп., 2, стр. 1)

If certain information is not present in the text, return those fields as 'null'. The extracted data should be structured and presented as a json file to the user.

Now, process the following text: {input_text}
"""

async def extract_json_from_text(input_text):
    # Format the prompt with the input text
    prompt = prompt_template.format(input_text=input_text)
    
    # Generate a completion
    response = model.generate_content(prompt)
    
    # Extract and return the result
    if response and response.candidates:
        print(response.text)
        return json.loads(re.search('\{[\w\W]*\}', response.text).group())
    else:
        return {"error": "No valid response from the model"}



# date_pattern = r"(?i)дата[\w\W]*?\b(?:исследования|анализа|дата)\b:\s*(.*)"

# def extract_medical_data(text):
#     # Наименование анализа
#     analysis_name = re.findall(r"(Гемоглобин|Глюкоза|.*? анализ)", text, re.IGNORECASE)

#     # Референтные значения (нормы)
#     reference_values = re.findall(r"Референтные значения[:\s]*(\d+[\.,]?\d*)", text)

#     # Единицы измерения
#     units = re.findall(r"(г/дл|%)", text)

#     # Результаты анализа
#     results = re.findall(r"Результат[:\s]*(\d+[\.,]?\d*)", text)

#     # Дата проведения анализа
#     date = re.search(date_pattern, text)
#     if date:
#         date = date.group(1)
            
#     # Место проведения анализа
#     place = re.findall(r"Место проведения[:\s]*(.*?)\n", text)

#     # Адрес места проведения анализа
#     address = re.findall(r"Адрес[:\s]*(.*?)\n", text)

#     return {
#         "Наименование анализа": analysis_name,
#         "Референтные значения": reference_values,
#         "Единицы измерения": units,
#         "Результаты анализа": results,
#         "Дата проведения анализа": date,
#         "Место проведения анализа": place,
#         "Адрес места проведения анализа": address
#     }
