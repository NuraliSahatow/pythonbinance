import telebot

bot = telebot.TeleBot('6265387611:AAEUcwtVljQnrKBaeWieu5UlLvDRSpHqRqg')


@bot.message_handler(commands=['start'])
def start(message):
    chat_id = message.chat.id
    bot.reply_to(message, f'Привет! ID вашего чата: {chat_id}')

bot.polling()