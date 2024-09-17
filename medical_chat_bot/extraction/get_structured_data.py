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

# Dictionary to map Russian month names to month numbers
months = {
    "января": "01",
    "февраля": "02",
    "марта": "03",
    "апреля": "04",
    "мая": "05",
    "июня": "06",
    "июля": "07",
    "августа": "08",
    "сентября": "09",
    "октября": "10",
    "ноября": "11",
    "декабря": "12"
}


# Define the prompt template for extracting structured data as JSON
prompt_template = """
You are an AI assistant capable of extracting structured information from medical documents. Given a passage, extract specific information and return it only as a JSON object. The JSON should include one of the following fields depending on the type of document:

MedicalAnalysis (анализы):
test_name (e.g., Гемоглобин, Глюкоза)
reference_min_value (e.g., min norm for the test, numeric value, for example: 30.8)
reference_max_value (e.g., max norm for the test, numeric value, for example: 14.5)
units (e.g., г/дл, %)
result (e.g., numerical values or text, numeric value, for example: 28.5)
test_date (e.g., 24.06.2020, 24/06/2020)
institution (e.g., the name of the medical institution e.g., ФГАУ Национальный медицинский иссле­довательский центр здоровья детей Минздрава России)
address (the address of the medical institution, e.g., "Москва, Ломоносовский просп., 2, стр. 1")

MedicalResearch (исследования):
research_name (e.g., "Ультразвуковое исследование")
research_date (e.g., 24.06.2020, 24/06/2020)
institution (the name of the medical institution ,e.g., ФГАУ Национальный медицинский иссле­довательский центр здоровья детей Минздрава России)
equipment (e.g., the equipment used for the study)
protocol (the detailed protocol of the research, a description of the research procedure, e.g., На серии МР-томограмм взвешенных по Т1 и Т2 в аксиальной, сагиттальной и фронтальной проекциях
визуализированы суб- и супратенториальные структуры.)
conclusion (e.g., Достоверных МР-данных за наличие изменений очагового и диффузного характера в веществе мозга не получено)
recommendation (any recommendations provided following the research, e.g., Для завершения обследования и постановки диагноза, полученные результаты должны быть
рассмотрены лечащим врачом в совокупности с клиническими данными)
address (the address of the medical institution, e.g., Москва, Ломоносовский просп., 2, стр. 1)

If certain information is not present in the text, return those fields only as null values. The extracted data should be structured and presented as a json file to the user. All properties names should be enclosed in double quotes.
All properties names should be enclosed in double quotes.

Now, process the following text: {input_text}
"""


def check_and_complete_json(json_string):
    try:
        # Try to load the JSON as is
        data = json.loads(json_string)
        return data
    except json.JSONDecodeError as e:
        print(f"Error : {str(e)}")

        # Stack to keep track of opening braces/brackets
        stack = []
        fixed_json = []
        
        for char in json_string:
            fixed_json.append(char)

            if char == "{" or char == "[":
                stack.append(char)
            elif char == "}" or char == "]":
                if not stack:
                    continue
                open_brace = stack.pop()
                if (open_brace == "{" and char != "}") or (
                    open_brace == "[" and char != "]"
                ):
                    return {}  # Structure is corrupted, cannot be fixed

        # Complete any unclosed braces/brackets
        while stack:
            open_brace = stack.pop()
            if open_brace == "{":
                fixed_json.append("}")
            elif open_brace == "[":
                fixed_json.append("]")

        completed_json_string = "".join(fixed_json)

        # Try parsing the corrected JSON
        try:
            data = json.loads(completed_json_string)
            return data
        except json.JSONDecodeError as e:
            print(f"Error after completion attempt: {str(e)}")
            return {}


async def change_date_format(data, date, text):

    if date:
        default_date = date.split(" ")[0]
    else:
        default_date = None

    def update_date(item, field_name):
        try:
            date_Str = str(item[field_name])
            if date_Str:
                for month in months and date_Str:
                    if month in date_Str:
                        parts = date_Str.split()
                        day = parts[0]
                        month = months[parts[1]]
                        year = parts[2]
                        date_Str = f"{day}/{month}/{year}"
                        break

            item[field_name] = parser.parse(
                date_Str if date_Str else default_date
            )
        except Exception as e:
            print(str(e))
            item[field_name] = None

    def to_numeric(item, fields):
        for field in fields:
            try:
                item[field] = float(str(item[field]).replace(",", "."))
            except:
                item[field] = None

    # Handle MedicalAnalysis
    if "MedicalAnalysis" in data:
        if isinstance(data["MedicalAnalysis"], list):
            for index, item in enumerate(data["MedicalAnalysis"]):
                update_date(item, "test_date")
                to_numeric(
                    item=item,
                    fields=["reference_min_value",
                            "reference_max_value", "result"],
                )
                item.update({"id": uuid.uuid5(namespace, text + str(index))})
        elif isinstance(data["MedicalAnalysis"], dict):
            update_date(data["MedicalAnalysis"], "test_date")
            to_numeric(
                item=item,
                fields=["reference_min_value",
                        "reference_max_value", "result"],
            )
            data["MedicalAnalysis"].update({"id": uuid.uuid5(namespace, text)})

    # Handle MedicalResearch
    if "MedicalResearch" in data:
        if isinstance(data["MedicalResearch"], list):
            for index, item in enumerate(data["MedicalResearch"]):
                update_date(item, "research_date")
                item.update({"id": uuid.uuid5(namespace, text + str(index))})
        elif isinstance(data["MedicalResearch"], dict):
            update_date(data["MedicalResearch"], "research_date")
            data["MedicalResearch"].update({"id": uuid.uuid5(namespace, text)})


async def extract_json_from_text(filename, text):

    input_text = filename + "\n" + text

    date = re.search(date_pattern, input_text)
    if date:
        date = date.group(1)

    prompt = prompt_template.format(input_text=input_text)

    response = model.generate_content(prompt)

    if response and response.candidates:
        match = re.search(r"\{[\w\W]*\}", response.text)
        if match:
            data = check_and_complete_json(match.group())
            if data:
                await change_date_format(data, date, text)
                return data
            else:
                raise Exception("No valid response from the model")
        else:
            raise Exception("No valid response from the model")
    else:
        raise Exception("No valid response from the model")
