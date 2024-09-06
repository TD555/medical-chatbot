import fitz
import re


async def extract_text_from_pdf(pdf_file):

    all_texts = []
    pdf_document = fitz.open("pdf", pdf_file.read())

    # Iterate through each page
    for page_num in range(pdf_document.page_count):
        page = pdf_document.load_page(page_num)

        # Extract text from the page
        text = page.get_text("text")

        clean_text = text.replace("\n", " ")
        clean_text = re.sub(r'\s+', ' ', clean_text)

        all_texts.append((text, clean_text))

    # Close the PDF document
    pdf_document.close()

    return all_texts