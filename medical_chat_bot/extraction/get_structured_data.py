import re
import os
import google.generativeai as genai
import json
import uuid
from dateutil import parser
from dotenv import load_dotenv
load_dotenv()

GEMINI_MODEL = 'gemini-pro'
GOOGLE_API_KEY = os.environ.get('GOOGLE_API_KEY')

genai.configure(api_key=GOOGLE_API_KEY)
model = genai.GenerativeModel(GEMINI_MODEL)

namespace = uuid.NAMESPACE_DNS

date_pattern = r"(?i)дата[\w\W]*?\b(?:исследования|анализа|дата)\b:\s*(.*)"

# Define the prompt template for extracting structured data as JSON
prompt_template = """
You are an AI assistant capable of extracting structured information from medical documents. Given a passage, extract specific information and return it only as a JSON object. The JSON should include one of the following fields depending on the type of document:

MedicalAnalysis (анализы):
test_name (e.g., Гемоглобин, Глюкоза)
reference_min_value (e.g., min norm for the test, numeric value, for example: 30.8)
reference_max_value (e.g., max norm for the test, numeric value, for example: 14.5)
units (e.g., г/дл, %)
result (e.g., numerical values or text, numeric value, for example: 28.5)
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
recommendation
address (e.g., Москва, Ломоносовский просп., 2, стр. 1)

If certain information is not present in the text, return those fields only as None values. The extracted data should be structured and presented as a json file to the user. All properties names should be enclosed in double quotes.

Now, process the following text: {input_text}
"""

async def change_date_format(data, date, text):
    def update_date(item, field_name):
        try:
            item[field_name] = parser.parse(item[field_name] if item[field_name] else default_date)
        except ValueError as e:
            print(str(e))
            item[field_name] = None

    default_date = date.split(' ')[0]
    
    def to_numeric(item, fields):
        for field in fields:
            try:
                item[field] = float(item[field].replace(',', '.'))
            except: item[field] = None

    default_date = date.split(' ')[0]

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
        data = json.loads(rf'{re.search(r'\{[\w\W]*\}', response.text).group()}')
        await change_date_format(data, date, text)
        print(data)
        return data
    
    else:
        raise Exception("No valid response from the model")
    