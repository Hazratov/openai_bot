# AI bilan telegram bot integratsiya qilingan. dasturchi @Behruzov
import asyncio
import os
import google.generativeai as genai
from aiogram import Bot, Dispatcher, executor, types
import httpx
from mimetypes import guess_type
from config import TELEGRAM_BOT_TOKEN, GENAI_API_KEY, generation_config


genai.configure(api_key=GENAI_API_KEY)
model = genai.GenerativeModel("gemini-1.5-pro", generation_config=generation_config)

bot = Bot(token=TELEGRAM_BOT_TOKEN)
dp = Dispatcher(bot)

# /start komandasi
@dp.message_handler(commands=["start"])
async def send_welcome(message: types.Message):
    await message.reply("""Assalomu alaykum! Men sun'iy intellekt asosidagi Telegram botman.
    
Men quyidagilarni qayta ishlashim mumkin:
- Matnli xabarlar
- Rasmlar uchun tasvirlar
- Ovozli xabarlar uchun transkripsiya.

Yordamga tayyorman, shunchaki xabar yoki fayl yuboring!""")


@dp.message_handler(content_types=["text", "photo", "voice", "audio"])
async def handle_all_messages(message: types.Message):
    try:
        user_id = message.from_user.id
        user_caption = message.caption or "Conversation with him/her"
        user_message = message.text or user_caption
        file_path = None  

        processing_message = await bot.send_message(
            chat_id=user_id, text="Kutib turing..."
        )

        # Tekshiramiz: Xabar turi rasm yoki ovozmi
        if message.photo:
            photo = message.photo[-1]  
            file = await bot.get_file(photo.file_id)
            file_path = file.file_path

            
            async with httpx.AsyncClient() as client:
                response = await client.get(f"https://api.telegram.org/file/bot{TELEGRAM_BOT_TOKEN}/{file_path}")
                file_name = "temp_image.jpg"
                with open(file_name, "wb") as f:
                    f.write(response.content)

            
            mime_type = guess_type(file_name)[0] or "image/jpeg"
            with open(file_name, "rb") as f:
                uploaded_file = genai.upload_file(f, mime_type=mime_type)

            # AI API orqali natija
            result = model.generate_content([uploaded_file, f"{user_message}"])

        elif message.voice or message.audio:
            file_id = message.voice.file_id if message.voice else message.audio.file_id
            file = await bot.get_file(file_id)
            file_path = file.file_path

            async with httpx.AsyncClient() as client:
                response = await client.get(f"https://api.telegram.org/file/bot{TELEGRAM_BOT_TOKEN}/{file_path}")
                file_name = "temp_audio.ogg"
                with open(file_name, "wb") as f:
                    f.write(response.content)

            mime_type = guess_type(file_name)[0] or "audio/ogg"
            with open(file_name, "rb") as f:
                uploaded_file = genai.upload_file(f, mime_type=mime_type)

            result = model.generate_content([uploaded_file, f"{user_message}"])

        else:
            result = await asyncio.to_thread(model.generate_content, user_message)


        await bot.delete_message(chat_id=user_id, message_id=processing_message.message_id)

        await message.reply(result.text, parse_mode="Markdown")

    except Exception as e:
        # await bot.delete_message(chat_id=user_id, message_id=processing_message.message_id)
        await message.reply(f"An error occurred: {e}")

async def main():
    await dp.start_polling()

if __name__ == "__main__":
    asyncio.run(main())
