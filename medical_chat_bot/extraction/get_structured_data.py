import re
import os
import google.generativeai as genai
import json
import uuid
from dateutil import parser
from dotenv import load_dotenv
load_dotenv(override=True)

GEMINI_MODEL = 'gemini-pro'
GOOGLE_API_KEY = os.environ.get('GOOGLE_API_KEY')

genai.configure(api_key=GOOGLE_API_KEY)
model = genai.GenerativeModel(GEMINI_MODEL)

namespace = uuid.NAMESPACE_DNS

date_pattern = r"(?i)дата[\w\W]*?\b(?:исследования|анализа|дата)\b:\s*(.*)"

# Define the prompt template for extracting structured data as JSON
prompt_template = """
You are an advanced AI model designed to extract structured information from medical documents. Given a passage, your task is to extract relevant information based on the following two types of documents: MedicalAnalysis (анализы) and MedicalResearch (исследования). Your output should always be a valid JSON object with specific fields.

Instructions for Extraction:
MedicalAnalysis (анализы):

"test_name": The name of the medical test (e.g., "Гемоглобин", "Глюкоза").
"reference_min_value": The minimum reference value for the test (numeric value, e.g., 30.8).
"reference_max_value": The maximum reference value for the test (numeric value, e.g., 14.5).
"units": Units of measurement for the test result (e.g., г/дл, %).
"result": The outcome of the test (numeric or textual, e.g., 28.5).
"test_date": The date when the test was conducted (e.g., "24/06/2020").
"institution": The name of the medical institution (e.g., "ФГАУ Национальный медицинский исследовательский центр здоровья детей Минздрава России").
"address": The address of the medical institution (e.g., "Москва, Ломоносовский просп., 2, стр. 1").
MedicalResearch (исследования):

"research_name": The name of the medical research or study (e.g., "Ультразвуковое исследование").
"research_date": The date the research was conducted (e.g., "24/06/2020").
"institution": The name of the medical institution (e.g., "ФГАУ Национальный медицинский исследовательский центр здоровья детей Минздрава России").
"equipment": The equipment used in the research (e.g., "MRI scanner").
"protocol": The detailed protocol of the research (e.g., a description of the research procedure).
"conclusion": The conclusion from the research (e.g., "Достоверных МР-данных за наличие изменений очагового и диффузного характера в веществе мозга не получено.").
"recommendation": Any recommendations provided following the research.
"address": The address of the medical institution (e.g., "Москва, Ломоносовский просп., 2, стр. 1").

If any of these details are not present in the input text, return the respective fields with None values. The output should always include all relevant fields.
All properties names should be enclosed in double quotes.

Now, process the following text: {input_text}
"""

async def change_date_format(data, date, text):

    if date:
        default_date = date.split(' ')[0]
    else:
        default_date=None

    def update_date(item, field_name):
        try:
            item[field_name] = parser.parse(item[field_name] if item[field_name] else default_date)
        except ValueError as e:
            print(str(e))
            item[field_name] = None

    
    def to_numeric(item, fields):
        for field in fields:
            try:
                item[field] = float(item[field].replace(',', '.'))
            except: item[field] = None


    # Handle MedicalAnalysis
    if "MedicalAnalysis" in data:
        if isinstance(data["MedicalAnalysis"], list):
            for index, item in enumerate(data["MedicalAnalysis"]):
                update_date(item, 'test_date')
                to_numeric(item=item, fields=['reference_min_value', 'reference_max_value', 'result'])
                item.update({"id": uuid.uuid5(namespace, text + str(index))})
        elif isinstance(data["MedicalAnalysis"], dict):
            update_date(data["MedicalAnalysis"], 'test_date')
            to_numeric(item=item, fields=['reference_min_value', 'reference_max_value', 'result'])
            data["MedicalAnalysis"].update({"id": uuid.uuid5(namespace, text)})

    # Handle MedicalResearch
    if "MedicalResearch" in data:
        if isinstance(data["MedicalResearch"], list):
            for index, item in enumerate(data["MedicalResearch"]):
                update_date(item, 'research_date')
                item.update({"id": uuid.uuid5(namespace, text + str(index))})
        elif isinstance(data["MedicalResearch"], dict):
            update_date(data["MedicalResearch"], 'research_date') 
            data["MedicalResearch"].update({"id": uuid.uuid5(namespace, text)})
                
                
async def extract_json_from_text(filename, text):
    
    input_text = filename + '\n' + text
    
    date = re.search(date_pattern, input_text)
    if date:
        date = date.group(1)
        
    prompt = prompt_template.format(input_text=input_text)
    
    response = model.generate_content(prompt)
    
    if response and response.candidates:
        match = re.search(r'\{[\w\W]*\}', response.text)
        if match:
            data = json.loads(rf"{match.group()}")
        else:
            raise Exception("No valid response from the model")

        await change_date_format(data, date, text)
        return data
    else:
        raise Exception("No valid response from the model")
    