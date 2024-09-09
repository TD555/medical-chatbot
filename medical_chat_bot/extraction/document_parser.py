import fitz
import re
from typing import Union
from io import BytesIO
from PIL import Image
import pytesseract

async def extract_text_from_pdf(pdf_file: Union[BytesIO, bytes]) -> str:
    all_texts = ''
    pdf_document = fitz.open("pdf", pdf_file.read() if isinstance(pdf_file, BytesIO) else pdf_file)

    # Iterate through each page
    for page_num in range(pdf_document.page_count):
        page = pdf_document.load_page(page_num)

        # Extract text from the page
        text = page.get_text("text", sort=True)
        # clean_text = text.replace("\n", " ")
        # clean_text = re.sub(r'\s+', ' ', clean_text)
        all_texts += text + ' '  # Append text from the page

        # Extract text from images on the page
        images_text = await extract_text_from_pdf_images(page, pdf_document)
        all_texts += images_text + ' '

    # Close the PDF document
    pdf_document.close()

    return all_texts

async def extract_text_from_pdf_images(page, pdf_document) -> str:
    text = ''
    images = page.get_images(full=False)

    for img_index, img in enumerate(images):
        xref = img[0]
        base_image = pdf_document.extract_image(xref)
        image_bytes = base_image["image"]
        image_stream = BytesIO(image_bytes)

        try:
            # Convert the image stream to a PIL.Image object
            pil_image = Image.open(image_stream)
            pil_image = pil_image.convert('RGB')  # Ensure the image is in RGB mode

            # Perform OCR on the image
            text += pytesseract.image_to_string(pil_image) + ' '
        
        except Exception as e:
            print(f"Error processing image {img_index}: {e}")

    return text
