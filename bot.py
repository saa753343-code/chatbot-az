import os
import logging
import requests
from telegram import Update
from telegram.ext import Application, MessageHandler, CommandHandler, filters, ContextTypes

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

TELEGRAM_TOKEN = os.environ.get("TELEGRAM_TOKEN", "YOUR_TELEGRAM_TOKEN")
GROQ_API_KEY = os.environ.get("GROQ_API_KEY", "YOUR_GROQ_KEY")

# =============================================
# BURAYA BİZNES MƏLUMATLARINI DAXİL EDİN
# ЗДЕСЬ НАСТРОЙТЕ ИНФОРМАЦИЮ О БИЗНЕСЕ
# =============================================
BUSINESS_INFO = """
Sən "Çinar" restoranının AI köməkçisisən. 
Sen ChatBot.az platforması tərəfindən idarə olunursan.

Restoran haqqında məlumat:
- Ad: Çinar Restoran
- Ünvan: Bakı, Nizami küçəsi 45, Sahil metrosunun yanı
- İş saatları: Hər gün 11:00 - 00:00
- Telefon: +994 12 555 00 00
- Çatdırılma: Bütün Bakı, minimum 15 AZN, 30-45 dəq, 30 AZN-dən pulsuz
- Orta qiymət: 20-40 AZN/nəfər
- Xüsusi: Uşaq otağı, parkinq, WiFi var

Qaydalar:
- Qısa, mehriban, peşəkar cavab ver (max 3-4 cümlə)
- Azərbaycan, Rus, İngilis dillərini başa düşürsən
- Müştəri hansı dildə yazırsa o dildə cavab ver
- Rezervasiya üçün: vaxt, tarix, nəfər sayı soruş
- Bilmədikdə: "Zəng edin: +994 12 555 00 00" de
"""

# Hər istifadəçi üçün söhbət tarixi / История чата для каждого пользователя
user_histories = {}

def ask_groq(user_id: int, message: str) -> str:
    if user_id not in user_histories:
        user_histories[user_id] = []
    
    user_histories[user_id].append({"role": "user", "content": message})
    
    # Son 10 mesajı saxla (yaddaş) / Храним последние 10 сообщений
    if len(user_histories[user_id]) > 10:
        user_histories[user_id] = user_histories[user_id][-10:]
    
    headers = {
        "Authorization": f"Bearer {GROQ_API_KEY}",
        "Content-Type": "application/json"
    }
    
    payload = {
        "model": "llama-3.3-70b-versatile",
        "messages": [
            {"role": "system", "content": BUSINESS_INFO}
        ] + user_histories[user_id],
        "max_tokens": 500,
        "temperature": 0.7
    }
    
    response = requests.post(
        "https://api.groq.com/openai/v1/chat/completions",
        headers=headers,
        json=payload,
        timeout=30
    )
    
    if response.status_code == 200:
        reply = response.json()["choices"][0]["message"]["content"]
        user_histories[user_id].append({"role": "assistant", "content": reply})
        return reply
    else:
        logger.error(f"Groq error: {response.text}")
        return "Bağışlayın, xəta baş verdi. Bir az sonra cəhd edin. / Извините, произошла ошибка."

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    user_histories[user_id] = []  # Söhbəti sıfırla
    
    await update.message.reply_text(
        "Salam! 👋 Çinar Restorana xoş gəlmisiniz!\n"
        "Masa rezervasiyası, menyu, çatdırılma haqqında soruşa bilərsiniz.\n\n"
        "Здравствуйте! 👋 Добро пожаловать в ресторан Чинар!\n"
        "Спрашивайте о столиках, меню, доставке — отвечу на любой вопрос!"
    )

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    user_message = update.message.text
    
    # Yazır... göstər / Показать "печатает..."
    await context.bot.send_chat_action(
        chat_id=update.effective_chat.id,
        action="typing"
    )
    
    reply = ask_groq(user_id, user_message)
    await update.message.reply_text(reply)

def main():
    app = Application.builder().token(TELEGRAM_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    
    logger.info("Bot işə düşdü! / Бот запущен!")
    app.run_polling(drop_pending_updates=True)

if __name__ == "__main__":
    main()
