# Medical Chat-Bot

## Overview
Telegram bot designed to process medical documents such as lab tests and research reports. The bot extracts structured data from documents, saves it in a PostgreSQL database, and answers user queries based on the stored information.

## Features
- Accepts documents in **PDF**, **PNG**, and **JPEG** formats.
- Extracts key information such as:
  - Test/Research name
  - Reference values (norms)
  - Measurement units
  - Test results
  - Test/Research date
  - Institution where the test/research was conducted
  - Address of the institution
  - Equipment used (for research)
  - Research protocols, conclusions, and recommendations
- Saves extracted data into a PostgreSQL database.
- Allows users to query the bot for specific data, such as test results or research findings over a given period.

## Technology Stack
- **Python**
- **Telegram Bot API** for managing communication with users.
- **PyMuPDF (fitz)** and **TesseractOCR** for extracting text from PDFs and images.
- **Gemini-pro free model** for structured information extraction from text.
- **Regex** for extracting dates.
- **PostgreSQL** for data storage.
- **LangChain** with **Azure OpenAI's gpt 3.5-turbo model as LLM** for generating SQL queries and answering user questions.

## Database Structure
The bot uses a PostgreSQL database (`medical_db`) with two main tables:
- **medical_analyse**: Stores data related to medical lab tests.
- **medical_research**: Stores data related to medical research reports.

## How it Works
1. **Document Processing**: 
   - Users upload a medical document to the bot (PDF/PNG/JPEG).
   - The bot extracts the text using `PyMuPDF` for PDFs and `TesseractOCR` for images.
   
2. **Information Extraction**:
   - Extracted text is processed using the **Gemini-pro** model to identify structured information like test names, results, and reference values.
   - **Regex** is used for date extraction.

3. **Data Storage**:
   - The extracted information is saved in the corresponding tables (`medical_analyse` or `medical_research`) in the PostgreSQL database.

4. **User Interaction**:
   - Users can ask questions like:
     - "What were my results for [test name]?"
     - "Show my test results from [date range]."
   - The bot uses **LangChain** with **Azure OpenAI** to generate SQL queries and provide human-readable answers based on the data in the database.

## Setup Instructions

### Prerequisites
- Docker (optional but recommended)
- Python 3.8+
- PostgreSQL
- Tesseract OCR (`sudo apt install tesseract-ocr`)
- Azure OpenAI credentials

### Installation
1. Clone the repository:
   ```bash
   git clone https://github.com/yourusername/medical-chatbot.git
   cd medical-chatbot
