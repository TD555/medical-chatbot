import re
import os
import google.generativeai as genai
import json
from dateutil import parser
from dotenv import load_dotenv
load_dotenv()

GEMINI_MODEL = 'gemini-pro'
GOOGLE_API_KEY = os.environ.get('GOOGLE_API_KEY')

genai.configure(api_key=GOOGLE_API_KEY)
model = genai.GenerativeModel(GEMINI_MODEL)


date_pattern = r"(?i)дата[\w\W]*?\b(?:исследования|анализа|дата)\b:\s*(.*)"

# Define the prompt template for extracting structured data as JSON
prompt_template = """
You are an AI assistant capable of extracting structured information from medical documents . Given a passage, extract specific information and return it only as a JSON object. The JSON should include one of the following fields depending on the type of document:

MedicalAnalysis (анализы):
test_name (e.g., Гемоглобин, Глюкоза)
reference_min_value (e.g., min norm for the test, for example: 30.8)
reference_max_value (e.g., max norm for the test, for example: 14.5)
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
recommendation
address (e.g., Москва, Ломоносовский просп., 2, стр. 1)

If certain information is not present in the text, return those fields only as None values. The extracted data should be structured and presented as a json file to the user.

Now, process the following text: {input_text}
"""


async def change_date_format(data, date):
    if "MedicalAnalysis" in data:
        for key, item in enumerate(data["MedicalAnalysis"]):
            try:
                data["MedicalAnalysis"][key]['test_date'] = parser.parse(
                    item['test_date'] if item['test_date'] else date.split(' ')[0])
            except:
                data["MedicalAnalysis"][key]['test_date'] = None

    if "MedicalResearch" in data:
        try:
            data["MedicalResearch"]['research_date'] = parser.parse(
                data["MedicalResearch"]['research_date'] if data["MedicalResearch"]['research_date'] else date.split(' ')[0])
        except Exception as e:
            print(str(e))
            data["MedicalResearch"]['research_date'] = None


async def extract_json_from_text(input_text):
    print(input_text)
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
        
        await change_date_format(data, date)
        return data

    else:
        raise Exception("No valid response from the model")
