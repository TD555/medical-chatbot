from PIL import Image
import pytesseract
from io import BytesIO

async def extract_text_from_image(image_stream: BytesIO) -> str:
    image = Image.open(image_stream)
    return pytesseract.image_to_string(image=image, lang="rus")