import telebot
from dotenv import load_dotenv
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton
import os

# Load environment variables from .env file
load_dotenv()

# Access the API key
API_TOKEN = os.getenv('API_KEY')
# Check if API key is loaded
if not API_TOKEN:
    raise ValueError("API key not found in .env file")

# Initialize bot with the API token
bot = telebot.TeleBot(API_TOKEN)

# Define the main menu text
menu_text = "Hello, Welcome to HAMOZA AI! Please choose an option:"

# Define a dictionary to store message IDs for each chat
chat_messages = {}

# Define a function to create the main menu keyboard
def create_main_menu():
    markup = InlineKeyboardMarkup(row_width=1)
    markup.add(
        InlineKeyboardButton("Start the bot", callback_data="start"),
        InlineKeyboardButton("About Resources", callback_data="content"),
        InlineKeyboardButton("Contact us", callback_data="contact")
    )
    return markup

# Define a function to create the confirmation keyboard
def create_confirmation_menu():
    markup = InlineKeyboardMarkup(row_width=2)
    markup.add(
        InlineKeyboardButton("Yes", callback_data="continue_yes"),
        InlineKeyboardButton("No", callback_data="continue_no")
    )
    return markup

# Helper function to track messages
def track_message(chat_id, message_id):
    if chat_id not in chat_messages:
        chat_messages[chat_id] = []
    chat_messages[chat_id].append(message_id)

# Command Handlers
@bot.message_handler(commands=['start'])
def send_welcome(message):
    sent_msg = bot.send_message(message.chat.id, menu_text, reply_markup=create_main_menu())
    track_message(message.chat.id, sent_msg.message_id)

@bot.message_handler(commands=['content'])
def send_content(message):
    # Content keyboard with specific note links
    markup = InlineKeyboardMarkup(row_width=1)
    markup.add(
        InlineKeyboardButton("Python Note", callback_data="Python"),
        InlineKeyboardButton("NumPy Note", callback_data="NumPy"),
        InlineKeyboardButton("Pandas Note", callback_data="Pandas"),
        InlineKeyboardButton("Matplotlib Note", callback_data="Matplotlib"),
        InlineKeyboardButton("Seaborn Note", callback_data="Seaborn"),
        InlineKeyboardButton("SciPY Note", callback_data="SciPy")
    )
    sent_msg = bot.send_message(message.chat.id, "Choose a resource:", reply_markup=markup)
    track_message(message.chat.id, sent_msg.message_id)

# Dictionary of note links
notes_links = {
    'Python': "https://drive.google.com/file/d/1yO87Ly0yrmA2qNpa7cPknGbDA2e1r5nD/view?usp=drive_link",
    'NumPy': "https://colab.research.google.com/drive/1kYo7Wj7qwhVL4z4eu8FNk8eZbS5BW3IU?usp=drive_link",
    'Pandas': "https://colab.research.google.com/drive/1mPXuXHDgk3y9i5JxDS0SWRLy88s94lds?usp=drive_link",
    'Matplotlib': "https://colab.research.google.com/drive/1mPXuXHDgk3y9i5JxDS0SWRLy88s94lds?usp=drive_link",
    'Seaborn': "https://colab.research.google.com/drive/1AiKT-oMoAGRzb_zuDDxhsMGJjI-rVMnP?usp=drive_link",
    'SciPy': "https://colab.research.google.com/drive/1urFdNZiiZMJLE21z-PpLzUTHevUZyNrk?usp=drive_link",
}

@bot.message_handler(commands=['contact'])
def send_contact_info(message):
    sent_msg = bot.reply_to(message, "Contact us at: jayed2305101640@diu.edu.bd")
    track_message(message.chat.id, sent_msg.message_id)

# Callback handler for inline buttons
@bot.callback_query_handler(func=lambda call: True)
def callback_query(call):
    if call.data == "start":
        # Display main menu again after selecting "Start the bot"
        sent_msg = bot.send_message(call.message.chat.id, menu_text, reply_markup=create_main_menu())
        track_message(call.message.chat.id, sent_msg.message_id)
    elif call.data == "content":
        # Display content selection again after choosing "About Resources"
        send_content(call.message)
    elif call.data == "contact":
        # Display contact info, then main menu again
        send_contact_info(call.message)
        sent_msg = bot.send_message(call.message.chat.id, menu_text, reply_markup=create_main_menu())
        track_message(call.message.chat.id, sent_msg.message_id)
    elif call.data in notes_links:
        # Send the link for the selected note
        sent_msg = bot.send_message(call.message.chat.id, f"{call.data} Note Drive Link: {notes_links[call.data]}")
        track_message(call.message.chat.id, sent_msg.message_id)
        # Ask if the user wants to continue
        sent_msg = bot.send_message(call.message.chat.id, "Do you want to continue?", reply_markup=create_confirmation_menu())
        track_message(call.message.chat.id, sent_msg.message_id)
    elif call.data == "continue_yes":
        # Display the main menu
        sent_msg = bot.send_message(call.message.chat.id, menu_text, reply_markup=create_main_menu())
        track_message(call.message.chat.id, sent_msg.message_id)
    elif call.data == "continue_no":
            # Delete all previous messages
        if call.message.chat.id in chat_messages:
            for msg_id in chat_messages[call.message.chat.id]:
                try:
                    bot.delete_message(call.message.chat.id, msg_id)
                except Exception as e:
                    print(f"Failed to delete message {msg_id}: {e}")
            chat_messages[call.message.chat.id] = []  # Reset tracked messages
        # Inform the user that they can restart the bot with /start
        bot.send_message(call.message.chat.id, "Goodbye! If you want to start again, \ntype /start.")

# Start polling
try:
    bot.infinity_polling()
except Exception as e:
    print(f"An error occurred: {e}")

