import os
import io
import sys

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from extraction.document_parser import extract_text_from_pdf
from extraction.image_parser import extract_text_from_image
from extraction.get_structured_data import extract_json_from_text
from db.migrate import insert_data
from chat.chat_with_AI import answer_question
from version import *
from telegram import Update
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    MessageHandler,
    filters,
    CallbackContext,
)
import mimetypes
from dotenv import load_dotenv

load_dotenv()
import logging

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO,
    handlers=[logging.StreamHandler(sys.stdout)],  # Logs will be sent to STDOUT
)

logger = logging.getLogger(__name__)

TG_TOKEN = os.environ.get("TG_TOKEN")
ALLOWED_MIME_TYPES = ["application/pdf", "image/png", "image/jpeg"]


def format_info(data):
    if isinstance(data, dict):
        return "\n".join([f"{key} - {value}" for key, value in data.items()])
    elif isinstance(data, list):
        return "\n\n".join(
            [
                f"{index + 1}.\n"
                + "\n".join([f"{key} - {value}" for key, value in item.items()])
                for index, item in enumerate(data)
            ]
        )


async def error(update: Update, context: CallbackContext):
    logger.error(f"Update {update} caused error {context.error}")


async def start(update: Update, context: CallbackContext):
    await update.message.reply_text(
        "Привет! Загрузите медицинский файл (PDF, PNG или JPEG), чтобы я мог обработать его."
    )


async def about(update: Update, context: CallbackContext):
    about_text = (
        f"*{__title__}*\n"
        f"Version: {__version__}\n"
        f"Description: {__description__}\n"
        f"Author: {__author__}\n"
        f"Author's email: {__author_email__}\n"
        f"Source code: {__url__}"
    )
    await update.message.reply_text(about_text, parse_mode="Markdown")


async def handle_document(update: Update, context: CallbackContext):
    document = update.message.document
    if document and document.mime_type in ALLOWED_MIME_TYPES:
        try:
            file_id = document.file_id
            new_file = await context.bot.get_file(file_id)
            file_content = await new_file.download_as_bytearray()
            await update.message.reply_text(
                f"Файл успешно загружен. Пожалуйта подождите до завершении поиска информации..."
            )

            all_text = await extract_text_from_pdf(io.BytesIO(file_content))
            extarcted_info = await extract_json_from_text(
                document.file_name, all_text
            )

            for section in ["MedicalResearch", "MedicalAnalysis"]:
                    if section in extarcted_info:
                        represent_info = format_info(extarcted_info[section])
                        break

            else:
                update.message.reply_text(
                    f"К настоящему моменту не удалось получить информацию из документа. Пожалуйста, попробуйте еще раз."
                )

            await update.message.reply_text(
                f"Информация извлечена из документа:\n{represent_info}"
            )
            
            try:
                await insert_data(extarcted_info)
            except Exception as e:
                await update.message.reply_text(
                    f"Не удалось сохранить информацию в базу данных. Возможно, она уже была сохранена. Пожалуйста, попробуйте еще раз."
                )
                
        except Exception as e:
            await update.message.reply_text(
                f"К настоящему моменту не удалось получить информацию из документа. Пожалуйста, попробуйте еще раз. {e}"
            )
    else:
        await update.message.reply_text(
            "Пожалуйста, отправьте файл в формате PDF, PNG или JPEG."
        )


async def handle_photo(update: Update, context: CallbackContext):
    photo_file = await update.message.photo[-1].get_file()
    file_path = photo_file.file_path
    mime_type, _ = mimetypes.guess_type(file_path)

    if photo_file and mime_type in ALLOWED_MIME_TYPES:
        try:
            photo_file = update.message.photo[-1]
            file_id = photo_file.file_id
            new_file = await context.bot.get_file(file_id)
            file_content = await new_file.download_as_bytearray()
            all_text = await extract_text_from_image(io.BytesIO(file_content))

            await update.message.reply_text(
                f"Файл успешно загружен. Пожалуйта подождите до завершении поиска информации..."
            )

            all_text = await extract_text_from_image(io.BytesIO(file_content))
            extarcted_info = await extract_json_from_text(
                photo_file.file_name, all_text
            )

            for section in ["MedicalResearch", "MedicalAnalysis"]:
                if section in extarcted_info:
                    represent_info = format_info(extarcted_info[section])
                    break

            else:
                update.message.reply_text(
                    "К настоящему моменту не удалось получить информацию из документа. Пожалуйста, попробуйте еще раз."
                )

            await update.message.reply_text(
                f"Информация извлечена из фотографии:\n{represent_info}"
            )
            
            try:
                await insert_data(extarcted_info)
            except Exception as e:
                await update.message.reply_text(
                    "Не удалось сохранить информацию в базу данных. Возможно, она уже была сохранена. Пожалуйста, попробуйте еще раз"
                )
                
        except Exception as e:
            await update.message.reply_text(
                "К настоящему моменту не удалось получить информацию из документа. Пожалуйста, попробуйте еще раз."
            )
    else:
        await update.message.reply_text(
            "Пожалуйста, отправьте файл в формате PDF, PNG или JPEG."
        )


async def handle_message(update: Update, context: CallbackContext):
    user_question = update.message.text

    try:
        answer = answer_question(question=user_question)
        await update.message.reply_text(answer)
    except Exception as e:
        await update.message.reply_text(f"An error occurred: {str(e)}")
        logger.error(f"Error: {str(e)}")


if __name__ == "__main__":
    application = ApplicationBuilder().token(TG_TOKEN).build()

    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("about", about))
    application.add_handler(MessageHandler(filters.Document.ALL, handle_document))
    application.add_handler(MessageHandler(filters.PHOTO, handle_photo))
    application.add_handler(
        MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message)
    )

    application.run_polling(close_loop=False)
    logger.info("Bot started.")
