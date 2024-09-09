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
You are an AI assistant capable of extracting structured information from medical documents. Given a passage, extract specific information and return it only as a JSON object. The JSON should include the following fields depending on the type of document:

Medical Tests (анализы):
Test Name (e.g., "Гемоглобин", "Глюкоза")
Reference Range (e.g., norms for the test)
Units (e.g., г/дл, %)
Test Results (e.g., numerical values or text)
Test Date
Test Location (e.g., the name of the medical institution)
Test Address
Medical Studies (исследования):
Study Name (e.g., "Ультразвуковое исследование")
Study Date
Study Location (e.g., the name of the medical institution)
Device (e.g., the equipment used for the study)
Study Protocol
Study Conclusion
Study Recommendations
Study Address
If certain information is not present in the text, return those fields as 'null'. The extracted data should be structured and presented as a json file to the user.

Now, process the following text: {input_text}
"""

def extract_json_from_text(input_text):
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



date_pattern = r"(?i)дата[\w\W]*?\b(?:исследования|анализа|дата)\b:\s*(.*)"

def extract_medical_data(text):
    # Наименование анализа
    analysis_name = re.findall(r"(Гемоглобин|Глюкоза|.*? анализ)", text, re.IGNORECASE)

    # Референтные значения (нормы)
    reference_values = re.findall(r"Референтные значения[:\s]*(\d+[\.,]?\d*)", text)

    # Единицы измерения
    units = re.findall(r"(г/дл|%)", text)

    # Результаты анализа
    results = re.findall(r"Результат[:\s]*(\d+[\.,]?\d*)", text)

    # Дата проведения анализа
    date = re.search(date_pattern, text)
    if date:
        date = date.group(1)
            
    # Место проведения анализа
    place = re.findall(r"Место проведения[:\s]*(.*?)\n", text)

    # Адрес места проведения анализа
    address = re.findall(r"Адрес[:\s]*(.*?)\n", text)

    return {
        "Наименование анализа": analysis_name,
        "Референтные значения": reference_values,
        "Единицы измерения": units,
        "Результаты анализа": results,
        "Дата проведения анализа": date,
        "Место проведения анализа": place,
        "Адрес места проведения анализа": address
    }
