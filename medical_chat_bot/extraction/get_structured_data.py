import re

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
    date = re.findall(r"\d{2}\.\d{2}\.\d{4}", text)

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
