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
You are an AI assistant capable of extracting structured information from medical documents. Given a passage, extract specific information and return it as a JSON object. The JSON should include one of the following fields, depending on the type of document (medical analysis or medical research). Ensure that all values are accurately mapped from the text to the corresponding field.

- **MedicalAnalysis (анализы)**:
  - `test_name`: The name of the medical test (e.g., "Гемоглобин", "Глюкоза").
  - `reference_min_value`: The minimum reference value for the test (e.g., 4.39 for Глюкоза).
  - `reference_max_value`: The maximum reference value for the test.
  - `units`: The units of measurement (e.g., "ммоль/л").
  - `result`: The result of the test (e.g., a numerical value or text).
  - `test_date`: The date the test was performed.
  - `institution`: The name of the medical institution or laboratory.
  - `address`: The address of the institution.

- **MedicalResearch (исследования)**:
  - `research_name`: The name of the research (e.g., "Ультразвуковое исследование").
  - `research_date`: The date the research was conducted.
  - `institution`: The name of the institution where the research was conducted.
  - `equipment`: The equipment used for the research.
  - `protocol`: The protocol or steps followed in the research.
  - `conclusion`: The conclusion of the research.
  - `recommendation`: Any recommendations provided.
  - `address`: The address of the institution.

**Instructions**:
- If certain information is not present in the text, return those fields as `None`.
- Focus on patterns and keywords such as dates, names of tests, measurement units, and institutions to guide the extraction process.
- If the text is ambiguous or multiple values exist, extract all relevant data.

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

    date = re.search(date_pattern, input_text)
    if date:
        date = date.group(1)

    prompt = prompt_template.format(input_text=input_text)

    response = model.generate_content(prompt)

    if response and response.candidates:
        match = re.search(r'\{[\w\W]*\}', response.text)
        if match:
            data = json.loads(rf"{match.group()}")
            print(data)
        else:
            raise Exception("No valid response from the model")
        
        await change_date_format(data, date)
        return data

    else:
        raise Exception("No valid response from the model")
