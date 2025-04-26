import os
import telebot
from telebot import types
from dotenv import load_dotenv
import google.generativeai as genai
import time
import logging
import PyPDF2
import json  # <-- NEW for tuition info

# Load environment variables
load_dotenv()

# Telegram and Gemini keys
TELEGRAM_TOKEN = os.getenv("TELEGRAM_API_KEY")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

# Initialize services
bot = telebot.TeleBot(TELEGRAM_TOKEN)
genai.configure(api_key=GEMINI_API_KEY)
model = genai.GenerativeModel('gemini-1.5-pro-latest')

# Context files
PDF_FILE = "diu_admission.pdf"
TUITION_FILE = "tuition_info_diu.json"


def load_pdf_content(pdf_path):
    try:
        reader = PyPDF2.PdfReader(pdf_path)
        content = ""
        for page in reader.pages:
            content += page.extract_text() + "\n"
        return content
    except Exception as e:
        print(f"Error loading PDF: {e}")
        return ""


def load_tuition_info(json_path):
    try:
        with open(json_path, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception as e:
        print(f"Error loading JSON: {e}")
        return {}


# Load content
DIU_INFO = load_pdf_content(PDF_FILE)
TUITION_INFO = load_tuition_info(TUITION_FILE)

# For saving conversation history
user_histories = {}


# Start command
@bot.message_handler(commands=['start', 'help'])
def send_welcome(message):
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    markup.add("🎓 Ask Admission Info", "💸 View Tuition Fees")

    bot.send_message(message.chat.id,
                     "🎓 *Welcome to DIU Admission Assistant!*\n\n"
                     "Ask me anything about Admission, Programs, Fees, Scholarships, Campus Life and more! ✨",
                     parse_mode="Markdown",
                     reply_markup=markup)


# Handle main user messages
@bot.message_handler(func=lambda message: True)
def handle_query(message):
    chat_id = message.chat.id
    user_text = message.text

    # Save conversation
    if chat_id not in user_histories:
        user_histories[chat_id] = []
    user_histories[chat_id].append(("Q", user_text))

    try:
        bot.send_chat_action(chat_id, 'typing')

        # Special case for Tuition Menu button
        if user_text == "💸 View Tuition Fees":
            tuition_text = json.dumps(TUITION_INFO, indent=2)
            bot.send_message(chat_id, f"📚 *Here’s the Tuition Information:*\n\n`{tuition_text}`", parse_mode="Markdown")
            return

        # Check if question is tuition-related
        tuition_keywords = ["tuition", "fee", "cost", "payment", "semester fee", "credit fee"]
        is_tuition_query = any(word in user_text.lower() for word in tuition_keywords)

        if is_tuition_query:
            context_info = f"Tuition Information:\n{json.dumps(TUITION_INFO, indent=2)}"
        else:
            context_info = f"General Admission Information:\n{DIU_INFO}"

        full_prompt = f"""
        You are an expert admission assistant for Daffodil International University (DIU).
        Use ONLY the following information to answer:
        {context_info}

        Question: {user_text}

        If the answer is not in the context, politely say "Please contact admission@daffodilvarsity.edu.bd or call +880 1814-555666."
        """

        # Generate answer from Gemini
        response = model.generate_content(full_prompt)
        answer = response.text.strip()

        user_histories[chat_id].append(("A", answer))

        # Send answer
        bot.send_message(chat_id, answer)

        # Ask if want to continue
        markup = types.ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)
        markup.add("✅ Yes", "❌ No")
        bot.send_message(chat_id, "Do you want to ask more questions?", reply_markup=markup)

    except Exception as e:
        print(f"Error: {e}")
        bot.reply_to(message, "⚠️ Sorry, there was a problem. Please try again later!")


# Handle Yes/No
@bot.message_handler(func=lambda message: message.text in ["✅ Yes", "❌ No"])
def handle_continue(message):
    chat_id = message.chat.id
    choice = message.text

    if choice == "✅ Yes":
        bot.send_message(chat_id, "Awesome! 🎯 Ask your next question:", reply_markup=types.ReplyKeyboardRemove())
    else:
        # Show summary
        summary = "📝 *Here’s your conversation summary:*\n\n"
        for qa in user_histories.get(chat_id, []):
            if qa[0] == "Q":
                summary += f"🔵 *Question:* {qa[1]}\n"
            else:
                summary += f"🟢 *Answer:* {qa[1]}\n\n"

        bot.send_message(chat_id, summary, parse_mode="Markdown")

        # Clear history
        user_histories.pop(chat_id, None)

        # Thank the user
        bot.send_message(chat_id, "Thank you for chatting with DIU Admission Assistant! 🌟\n"
                                  "Wishing you a bright future! 🚀",
                         reply_markup=types.ReplyKeyboardRemove())


# Main Loop
if __name__ == '__main__':
    print("🚀 Bot is running...")
    while True:
        try:
            bot.infinity_polling()
        except Exception as e:
            print(f"Bot crashed: {e}")
            time.sleep(5)
