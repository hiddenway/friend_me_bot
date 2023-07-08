import sqlite3
import telebot
from telebot import types
bot = telebot.TeleBot('6364066378:AAF0GRdEOpKfjZz36NhNSmiLeyNMtPVj27g')
connect = sqlite3.connect('database.db',check_same_thread=False,)
cursor = connect.cursor()
def init_bot():


    cursor.execute("""CREATE TABLE IF NOT EXISTS users(
                id integer PRIMARY KEY AUTOINCREMENT,
                id_user integer,
                username varchar
            )""")
    connect.commit()

init_bot()
@bot.message_handler(commands=['start'])
def start(message):
    markup = types.InlineKeyboardMarkup()
    item = types.InlineKeyboardButton(text='Next',callback_data='item_1')
    markup.add(item)

    tg_user_id = message.chat.id
    tg_username = message.from_user.username


    cursor.execute("INSERT INTO users (id_user,username) VALUES (?,?)",(tg_user_id,tg_username))
    connect.commit()

    bot.send_message(message.chat.id,'Приветствуем тебя дорогой друг!👋',reply_markup=markup)

@bot.callback_query_handler(func=lambda callback:callback.data)
def callback_main(callback):
    cursor.execute("SELECT username,id_user FROM users;")
    date = cursor.fetchone()
    if callback.data == 'item_1':
        bot.send_message(callback.message.chat.id,f'<b>Your person info:</b>\n\n<b>Your username:</b> {date[0]}\n<b>Your id:</b> {date[1]}',parse_mode='html')
    else:
        pass




print('//starting')
bot.infinity_polling()