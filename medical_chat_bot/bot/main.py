import os
import io
import sys
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from extraction.document_parser import extract_text_from_pdf
from extraction.image_parser import extract_text_from_image 
from extraction.get_structured_data import extract_json_from_text
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters
from dotenv import load_dotenv
load_dotenv()
from db.migrate import save_data_to_db

TG_TOKEN = os.environ.get('TG_TOKEN')
# Разрешённые MIME-типы для PDF, PNG и JPEG
ALLOWED_MIME_TYPES = ['application/pdf', 'image/png', 'image/jpeg']

import logging
# logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
#                     level=logging.DEBUG)


# Функция для обработки команды /start
async def start(update: Update, context):
    await update.message.reply_text("Привет! Загрузите медицинский файл (PDF, PNG или JPEG), чтобы я мог обработать его.")

# Функция для обработки загрузки файлов
async def handle_document(update: Update, context):
    document = update.message.document
    if document and document.mime_type in ALLOWED_MIME_TYPES:

        file_id = document.file_id
        new_file = await context.bot.get_file(file_id)
        file_content = await new_file.download_as_bytearray()
        await update.message.reply_text(f"Файл {document.file_name} успешно загружен. Пожалуйта подождите до завершении поиска информации...")
        all_text = await extract_text_from_pdf(io.BytesIO(file_content))
        extarcted_info = await extract_json_from_text(document.file_name + ' ' + all_text)
        if 'MedicalResearch' in extarcted_info:
            represent_info = '\n'.join([f'{key} - {value}' for key, value in extarcted_info['MedicalResearch'].items()])
            
        elif 'MedicalAnalysis' in extarcted_info:
            represent_info = ''
            for index, item in enumerate(extarcted_info['MedicalAnalysis']):        
                represent_info += f'{index + 1}.' + '\n'.join([f'{key} - {value}' for key, value in item.items()]) + '\n\n'
        
        await update.message.reply_text(f"Информация извлечена из документа: \n{represent_info}")
        await save_data_to_db(extarcted_info)
        
    else:
        await update.message.reply_text("Пожалуйста, отправьте файл в формате PDF, PNG или JPEG.")

async def handle_photo(update: Update, context):
    import mimetypes
    photo_file = await update.message.photo[-1].get_file()
    file_path = photo_file.file_path
    
    # Guess the MIME type based on the file extension
    mime_type, _ = mimetypes.guess_type(file_path)
    print(file_path)
    if photo_file and mime_type in ALLOWED_MIME_TYPES:
        photo_file = update.message.photo[-1]  # Получаем наибольшее качество фото
        file_id = photo_file.file_id
        new_file = await context.bot.get_file(file_id)
        file_content = await new_file.download_as_bytearray()
        all_text = await extract_text_from_image(io.BytesIO(file_content))
        # file_path = f"downloads/photo_{file_id}.jpg"
        # await new_file.download_to_drive(file_path)
        await update.message.reply_text(f"Фото успешно загружено и сохранено. Контент изображения: {extract_json_from_text(all_text)}")
    else:
        await update.message.reply_text("Пожалуйста, отправьте файл в формате PDF, PNG или JPEG.")

if __name__ == '__main__':
    application = ApplicationBuilder().token(TG_TOKEN).build()

    # Обработчики команд
    application.add_handler(CommandHandler('start', start))

    # Обработчик документов
    application.add_handler(MessageHandler(filters.Document.ALL, handle_document))

    # Обработчик изображений
    application.add_handler(MessageHandler(filters.PHOTO, handle_photo))

    # Запуск бота
    application.run_polling(close_loop=False)
