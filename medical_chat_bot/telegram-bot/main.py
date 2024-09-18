import logging
from dotenv import load_dotenv
import mimetypes
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    MessageHandler,
    filters,
    CallbackContext,
)
from telegram import Update
from version import (__title__,
                    __description__,
                    __url__ ,
                    __version__,
                    __author__,
                    __author_email__)
import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from extraction.get_structured_data import extract_json_from_text
from extraction.image_parser import extract_text_from_image
from extraction.document_parser import extract_text_from_pdf
from db.migrate import insert_data
from chat.chat_with_AI import answer_question
import io


load_dotenv()

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.ERROR,
    # Logs will be sent to STDOUT
    handlers=[logging.StreamHandler(sys.stdout)],
)

logger = logging.getLogger(__name__)

TG_TOKEN = os.environ.get("TG_TOKEN")
ALLOWED_MIME_TYPES = ["application/pdf", "image/png", "image/jpeg"]


KEY_MAPPING = {
            'test_name': 'Наименование анализа',
            'reference_min_value': 'Референтные значения (мин)',
            'reference_max_value': 'Референтные значения (макс)',
            'units': 'Единицы измерения',
            'result': 'Результаты анализа',
            'test_date': 'Дата проведения анализа',
            'institution': 'Место проведения анализа',
            'address': 'Адрес места проведения анализа',
            'research_name': 'Наименование исследования',
            'research_date': 'Дата проведения исследования',
            'equipment': 'Аппарат, на котором проводилось исследование',
            'protocol': 'Протокол исследования',
            'conclusion': 'Заключение исследования',
            'recommendation': 'Рекомендация исследования'
}

        
def format_info(data):
    if isinstance(data, dict):
        return "\n".join([f"{KEY_MAPPING.get(key, key)} - {value if value else 'Нет данных'}" for key, value in data.items()])
    elif isinstance(data, list):
        return "\n\n".join(
            [
                f"{index + 1}.\n"
                + "\n".join([f"{KEY_MAPPING.get(key, key)} - {value if value else 'Нет данных'}" for key,
                            value in item.items()])
                for index, item in enumerate(data)
            ]
        )


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
                await update.message.reply_text(
                    f"К настоящему моменту не удалось получить информацию из документа. Пожалуйста, попробуйте еще раз."
                )
            await update.message.reply_text("Информация извлечена из документа:\n")
            msgs = [represent_info[i:i + 4096] for i in range(0, len(represent_info), 4096)]
            for text in msgs:
                await update.message.reply_text(text=text)
                
            try:
                await insert_data(extarcted_info)
                await update.message.reply_text(
                    f"Информация извлечена из документа {document.file_name} успешно сохранена в базу данных!"
                )
            except Exception as e:
                await update.message.reply_text(
                    "Не удалось сохранить информацию в базу данных. Возможно, она уже была сохранена. Пожалуйста проверьте и попробуйте еще раз."
                )
                logger.error(f"Error: {str(e)}")

        except Exception as e:
            await update.message.reply_text(
                f"К настоящему моменту не удалось получить информацию из документа. Пожалуйста, попробуйте еще раз."
            )
            logger.error(f"Error: {str(e)}")
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
            await update.message.reply_text(
                f"Файл успешно загружен. Пожалуйта подождите до завершении поиска информации..."
            )

            all_text = await extract_text_from_image(io.BytesIO(file_content))
            extarcted_info = await extract_json_from_text(
                filename='', text=all_text
            )

            for section in ["MedicalResearch", "MedicalAnalysis"]:
                if section in extarcted_info:
                    represent_info = format_info(extarcted_info[section])
                    break

            else:
                await update.message.reply_text(
                    "К настоящему моменту не удалось получить информацию из документа. Пожалуйста, попробуйте еще раз."
                )
                
            await update.message.reply_text("Информация извлечена из фотографии:\n")
            msgs = [represent_info[i:i + 4096] for i in range(0, len(represent_info), 4096)]
            for text in msgs:
                await update.message.reply_text(text=text)

            try:
                await insert_data(extarcted_info)
                await update.message.reply_text(
                    f"Информация извлечена из фотографии успешно сохранена в базу данных!"
                )
            except Exception as e:
                await update.message.reply_text(
                    "Не удалось сохранить информацию в базу данных. Возможно, она уже была сохранена. Пожалуйста проверьте и попробуйте еще раз."
                )
                logger.error(f"Error: {str(e)}")

        except Exception as e:
            await update.message.reply_text(
                "К настоящему моменту не удалось получить информацию из фотографии. Пожалуйста, попробуйте еще раз."
            )
            logger.error(f"Error: {str(e)}")
    else:
        await update.message.reply_text(
            "Пожалуйста, отправьте файл в формате PDF, PNG или JPEG."
        )


async def handle_message(update: Update, context: CallbackContext):
    user_question = update.message.text
    print(user_question)
    try:
        answer = answer_question(question=user_question)
        await update.message.reply_text(answer)
    except Exception as e:
        await update.message.reply_text(f"An error occurred: {str(e)}")
        logger.error(f"Error: {str(e)}")


if __name__ == "__main__":
    application = ApplicationBuilder().token(TG_TOKEN).read_timeout(30).write_timeout(30).build()

    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("about", about))
    application.add_handler(MessageHandler(
        filters.Document.ALL, handle_document))
    application.add_handler(MessageHandler(filters.PHOTO, handle_photo))
    application.add_handler(
        MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message)
    )

    application.run_polling(close_loop=False)
    logger.info("Bot started.")
