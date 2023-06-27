from telebot.async_telebot import AsyncTeleBot
import io
import random
import sqlite3
import datetime
from telebot import types
import os
from dotenv import load_dotenv,find_dotenv
import asyncio

load_dotenv(find_dotenv())

print('bot is activated 🗸')

bot = AsyncTeleBot(os.getenv('TOKEN'))
connect = sqlite3.connect('friendMe.db', check_same_thread=False)
bot_name = "Friend_Me_bot"
admin_id = 1900666417


def init_bot():
    
    cursor = connect.cursor()

    cursor.execute("""CREATE TABLE IF NOT EXISTS users(
               id integer PRIMARY KEY AUTOINCREMENT,
               tg_id integer,
               username varchar,
               ref_id number,
               date date
           )""")
    connect.commit()

    cursor.execute("""CREATE TABLE IF NOT EXISTS images(
            id integer PRIMARY KEY AUTOINCREMENT,
            id_image integer,
            from_id integer,
            media_group_id integer,
            to_id integer,
            date date
    )""")
    connect.commit()


    #child_loop = asyncio.new_event_loop()

    #asyncio.create_task(child_loop.run_until_complete(get_photo_user(1929558405)))

init_bot()

def get_user(chat_id):
    cursor = connect.cursor()
    cursor.execute(f"SELECT * FROM users WHERE tg_id={chat_id}")
    return cursor.fetchone()

def auth_user(chat_id, username, ref_id=None):

    cursor = connect.cursor()
    cursor.execute("SELECT tg_id FROM users WHERE tg_id=?", (chat_id,))
    data = cursor.fetchone()

    if data is None:
        cursor.execute("INSERT INTO users VALUES(?,?,?,?,?);", (None, chat_id, username, ref_id, datetime.datetime.now()))
        connect.commit()

    else:
        if ref_id is not None:
            cursor.execute("UPDATE users SET ref_id=? WHERE tg_id=?", (ref_id, chat_id))
            connect.commit()

    cursor.execute("SELECT * FROM users WHERE tg_id=?", (chat_id, ))
    User = cursor.fetchone()

    print("User Data: ", User)

    return User

#Очистить БД
@bot.message_handler(commands=['clear'])
async def clear(message):
    print("CLEAR DB")
    cursor = connect.cursor()

    cursor.execute("DROP TABLE IF EXISTS users")
    connect.commit()

    cursor.execute("DROP TABLE IF EXISTS images")
    connect.commit()

    await bot.send_message(message.chat.id, "Clear DB Success")

    init_bot()

#Меню Старт
@bot.message_handler(commands=['start'])
async def start(message):

    markup = types.ReplyKeyboardMarkup(resize_keyboard=True,row_width=2)
    start_button1 = types.KeyboardButton('🌁 МОИ ФОТО')
    start_button2 = types.KeyboardButton('📨 ОБРАТНАЯ СВЯЗЬ')
    start_button3 = types.KeyboardButton('⛓️ ОТПРАВИТЬ ССЫЛКУ ДРУГУ')
    start_button4 = types.KeyboardButton('📕 О НАС')
    markup.add(start_button1,start_button3,start_button2,start_button4)

    ref_id = None
    ref_id_arr = (message.text).split(' ')
    witch_ref_link = False

    if len(ref_id_arr) > 1:
        ref_id = ref_id_arr[1]
        if get_user(ref_id) is not None and ref_id != None:
            if int(ref_id) != message.from_user.id:
                witch_ref_link = True

    User = auth_user(message.from_user.id, message.from_user.username, ref_id)

    if User[3] is not None and ref_id == None:
        await only_photo(User)
        return

    if witch_ref_link == True:
        if int(ref_id) is message.from_user.id:
            await bot.send_message(message.chat.id, '<b>❌ Вы не можете открыть свою же ссылку</b>',parse_mode='html',reply_markup=markup)
        else:
            await start_with_ref_link(User[1], ref_id)
    else:
        await bot.send_message(message.chat.id, '<b>Приветствуем тебя дорогой друг!👋</b>\nС помощью нашего бота ты можешь со всех своих друзей собрать совместные фото и видео с тобой и вспомнить забытые и смешные моменты!\n\nКак это работает:\n1️⃣Нажмите кнопку в меню "отправить ссылку другу"\n2️⃣Выберите "Поделиться историей Instagram"\n3️⃣﻿﻿Добавьте себе историю в инстаграм как указано инструкции по кнопке\n4️⃣Все фото которые отправят друзья мы будем отображать в разделе "Мои фото"\n\nКак только кто-то из твоих друзей отправит что-то по ссылке мы обязательно тебе об этом скажем😊',parse_mode='html',reply_markup=markup)

async def get_photo_user_album(chat_id):
    cursor = connect.cursor()
    
    #GET ALL GROUPS ID

    cursor.execute("SELECT DISTINCT media_group_id FROM images WHERE to_id=?", (chat_id,))
    all_user_photo_groups = cursor.fetchall()

    for group_id in all_user_photo_groups:
        album = []
        cursor.execute("SELECT id_image FROM images WHERE media_group_id=?", (group_id[0],))
        images = cursor.fetchall()

        for image_id in images:
            album.append(types.InputMediaPhoto(image_id[0]))

        await bot.send_media_group(chat_id, album)

@bot.message_handler(content_types=['text'])
async def chat_message(message):
    User = auth_user(message.from_user.id, message.from_user.username)

    if User[3] is not None:
        await only_photo(User)
        return

    ref_id = message.chat.id
    if message.text == '🌁 МОИ ФОТО':
        # markup = types.InlineKeyboardMarkup(row_width=2)
        # item_my_photo1 = types.InlineKeyboardButton(text='Отправить в ответ',callback_data='itemmyphoto1')
        # item_my_photo2 = types.InlineKeyboardButton(text='Далее',callback_data='itemmyphoto2')
        # item_my_photo3 = types.InlineKeyboardButton(text='Назад',callback_data='itemmyphoto2')
        # markup.add(item_my_photo3,item_my_photo2,item_my_photo1)
        # await bot.send_message(message.chat.id,f'📸 Пользователь {message.from_user.first_name} отправил вам 10 фотографий и 2 видео:\n\nЧто бы их увидеть отправьте ему в ответ любую фотографию или видео с его участием\n\nОтправте их по его ссылке или нажмите на кнопку"Отправить в ответ"',reply_markup=markup)
        await get_photo_user_album(message.chat.id)
    elif message.text == '📨 ОБРАТНАЯ СВЯЗЬ':
        markup_info = types.InlineKeyboardMarkup(row_width=2)
        item_info1 = types.InlineKeyboardButton(text='📬 Support',callback_data='instagram_info',url='https://t.me/friendme_support')
        item_info2 = types.InlineKeyboardButton(text='📢 Telegram Group', callback_data='twitter_info',url='https://twitter.com/')
        markup_info.add(item_info1,item_info2)
        await bot.send_message(message.chat.id,'<b>Обратная связь</b>\n\nВ случае неисправности бота или зафиксированной ошибке , просьба обратится в нашу тех-поддержу по адресу : @friendme_support\n\nТак же если у вас сеть предложения для улучшения нашего сервиса ,можете обратиться по адресу : @friendme_offers\n\n<b>FriendMe в социальных сетях:</b>',parse_mode='html',reply_markup=markup_info)
    elif message.text == '⛓️ ОТПРАВИТЬ ССЫЛКУ ДРУГУ':
        markup = types.InlineKeyboardMarkup(row_width=1)
        item1 = types.InlineKeyboardButton(text='Поделиться в Instagram Stories',callback_data='share1')
        item2 = types.InlineKeyboardButton('Поделиться в Telegram',switch_inline_query=f'\n\nhttps://t.me/{bot_name}?start={ref_id}')
        item3 = types.InlineKeyboardButton(text='Показать ссылку в чате',callback_data='share3')
        markup.add(item1,item2,item3)
        await bot.send_message(message.chat.id,'<b>⤴️Поделиться с друзьями удобным для вас способом:</b>',parse_mode='html',reply_markup=markup)
    elif message.text == '📕 О НАС':
        info_image = open('images/friendme_logo.jpg','rb')
        await bot.send_photo(message.chat.id,info_image,caption='Добро пожаловать в нашем боте FriendMe, созданное специально для вас и ваших друзей!\n\nМы понимаем, что поделиться фотографиями с близкими людьми - это особенно приятно. Поэтому мы разработали этого бота, чтобы сделать процесс обмена фотографиями еще более удобным и приятным для вас.\n\nПоэтому что бы получить множество фотографий от ваших друзей ,родственников или же колег  с любого рода мероприятия . Вам придется легко сгенерировать реферальную ссылку и поделиться ей любым удобным способом\n\nМы нацелены на ваше удовлетворение, поэтому постоянно работаем над улучшением и совершенствованием нашего бота. Мы стремимся предоставить вам самый приятный и удобный опыт использования.\n\nСпасибо, что выбрали нашего бота, и дарите своим друзьям незабываемые моменты и радость фотографий. Мы надеемся, что оно станет вашим надежным спутником и поможет вам создавать прекрасные воспоминания с вашими близкими.')

@bot.message_handler(content_types=['photo'])
async def photo(message):

    #Получаем данные пользователя из БД, если их нету то создаём
    User = auth_user(message.from_user.id, message.from_user.username)

    #Получаем id пользователя который отправил ссылку
    ref_id = User[3]
    if ref_id == None:
        return await error_command(User[1])
    else:
        friendUser = get_user(ref_id)
        media_group_id = message.media_group_id

        #Получаем id фотографии
        image_id = message.photo[-1].file_id
        
        date_image = datetime.datetime.now()
        from_id = message.from_user.id

        #Добавляем фотографию в базу данных
        cursor = connect.cursor()
        cursor.execute("INSERT INTO images VALUES(?,?,?,?,?,?);", (None, image_id, from_id, media_group_id, ref_id, date_image))
        connect.commit()

        #BTN SEND MORE

        markup = types.InlineKeyboardMarkup()
        markup.add(types.InlineKeyboardButton(text='💬 Отправить ещё' , url=f"https://t.me/{bot_name}?start={friendUser[1]}"))

        #Проверяем буфер
        if media_group_id is not None:
                cursor.execute("SELECT * FROM images WHERE media_group_id=?", (media_group_id, ))
                data = cursor.fetchall()

                print("MEDIA_GROUP:", len(data))

                if len(data) <= 1:
                    await send_menu_message(message.chat.id, "✅ Вы успешно отправили фотографии!")

                    await bot.send_message(message.chat.id, f"👀 Для просмотра данных фотографий вашему другу потребуется отправить в ответ какие-то фотографии с вами, после чего мы обязательно сообщим вам и порадуем вас фото :) \n\nЧтобы отправить ещё что-то пользователю <b>«{friendUser[2]}»</b> нажмите кнопку ниже <b>«Отправить ещё»</b>", reply_markup=markup, parse_mode='html')

                    cursor.execute("UPDATE users SET ref_id=? WHERE tg_id=?", (None, User[1], ))
                    connect.commit()
        else:
            await send_menu_message(message.chat.id, "✅ Вы успешно отправили фотографию!")
            cursor.execute("UPDATE users SET ref_id=? WHERE tg_id=?", (None, User[1], ))
            connect.commit()

@bot.callback_query_handler(func=lambda callback:callback.data)
async def callback_my_photo(callback):
    User = auth_user(callback.message.chat.id, callback.from_user.username)
    
    print("callback.data:",callback.data)
    if callback.data == 'cancel_send_photo':

        if User[3] is None:
            return await error_command(User[1])

        await send_menu_message(callback.message.chat.id, "❌ Отмена")

        cursor = connect.cursor()
        cursor.execute("UPDATE users SET ref_id=? WHERE tg_id=?", (None, callback.message.chat.id, ))
        connect.commit()

        await bot.send_message(callback.message.chat.id, '<b>Приветствуем тебя дорогой друг!👋</b>\nС помощью нашего бота ты можешь со всех своих друзей собрать совместные фото и видео с тобой и вспомнить забытые и смешные моменты!\n\nКак это работает:\n1️⃣Нажмите кнопку в меню "отправить ссылку другу"\n2️⃣Выберите "Поделиться историей Instagram"\n3️⃣﻿﻿Добавьте себе историю в инстаграм как указано инструкции по кнопке\n4️⃣Все фото которые отправят друзья мы будем отображать в разделе "Мои фото"\n\nКак только кто-то из твоих друзей отправит что-то по ссылке мы обязательно тебе об этом скажем😊',parse_mode='html')
        
        return

    if User[3] is not None:
        await only_photo(User)
        return

    ref_id = callback.message.chat.id

    if callback.data == 'itemmyphoto1':
       pass
    elif callback.data == 'itemmyphoto2':
        markup = types.InlineKeyboardMarkup(row_width=2)
        item_my_photo1 = types.InlineKeyboardButton(text='Отправить в ответ',callback_data='itemmyphoto1')
        item_my_photo2 = types.InlineKeyboardButton(text='Далее',callback_data='itemmyphoto2')
        item_my_photo3 = types.InlineKeyboardButton(text='Назад',callback_data='itemmyphoto2')
        markup.add(item_my_photo3,item_my_photo2,item_my_photo1)
        await bot.edit_message_text(chat_id=callback.message.chat.id,message_id=callback.message.id,text=f'📸 Пользователь {callback.message.from_user.first_name} отправил вам 15 фотографий и 5 видео:\n\nЧто бы их увидеть отправьте ему в ответ любую фотографию или видео с его участием\n\nОтправте их по его ссылке или нажмите на кнопку"Отправить в ответ"',reply_markup=markup)
    elif callback.data == 'itemmyphoto3':
        markup = types.InlineKeyboardMarkup(row_width=2)
        item_my_photo1 = types.InlineKeyboardButton(text='Отправить в ответ', callback_data='itemmyphoto1')
        item_my_photo2 = types.InlineKeyboardButton(text='Далее', callback_data='itemmyphoto2')
        item_my_photo3 = types.InlineKeyboardButton(text='Назад', callback_data='itemmyphoto2')
        markup.add(item_my_photo3, item_my_photo2, item_my_photo1)
        await bot.edit_message_text(chat_id=callback.message.chat.id, message_id=callback.message.id,text=f'📸 Пользователь {callback.message.from_user.first_name} отправил вам 10 фотографий и 2 видео:\n\nЧто бы их увидеть отправьте ему в ответ любую фотографию или видео с его участием\n\nОтправте их по его ссылке или нажмите на кнопку"Отправить в ответ"',reply_markup=markup)
    elif callback.data == 'share1':
        markup = types.InlineKeyboardMarkup()
        item_next = types.InlineKeyboardButton(text='Далее',callback_data='item_next1')
        markup.add(item_next)
        image = open('images/inst.jpg', 'rb')
        await bot.send_photo(callback.message.chat.id, image)
        await bot.send_message(callback.message.chat.id,'Для того чтобы корректно выложить историю с ссылкой в <b>Instagram stories</b>,вам потребуется выполнить 3 простых действия и ждите океан фото от своих друзей 😁',parse_mode='html',reply_markup=markup)
    elif callback.data == 'share2':
        await bot.send_message(callback.message.chat.id,'')
    elif callback.data == 'share3':
        await bot.send_message(callback.message.chat.id, f'https://t.me/{bot_name}?start={ref_id}')
    elif callback.data == 'item_next1':
        markup = types.InlineKeyboardMarkup()
        item_next = types.InlineKeyboardButton(text='Далее', callback_data='item_next2')
        markup.add(item_next)
        await bot.edit_message_text(chat_id=callback.message.chat.id, message_id=callback.message.message_id, text="1️⃣Скачайте фотографию которую мы отправили ниже, после нажмите далее",reply_markup=markup)
    elif callback.data == 'item_next2':
        markup = types.InlineKeyboardMarkup()
        item_next = types.InlineKeyboardButton(text='Далее', callback_data='item_next3')
        markup.add(item_next)
        await bot.edit_message_text(chat_id=callback.message.chat.id, message_id=callback.message.message_id,text="2️⃣Откройте вкладку истории и загрузите это фото, после нажмите далее",reply_markup=markup)
    elif callback.data == 'item_next3':
        markup = types.InlineKeyboardMarkup()
        item_next = types.InlineKeyboardButton(text='Поделиться', callback_data='item_share4')
        markup.add(item_next)
        await bot.edit_message_text(chat_id=callback.message.chat.id, message_id=callback.message.message_id,text=f"3️⃣Добавьте ссылку которую мы отправили ниже в рамку посередине как на скриншоте⤵️\n\nhttps://t.me/{bot_name}?start={ref_id}",reply_markup=markup)

async def error_command (chat_id):
    return await bot.send_message(chat_id,'<b>⛔ Произошла ошибка, данная команда недоступна!</b>',parse_mode='html')

async def start_with_ref_link (chat_id, ref_id):
        markup = types.InlineKeyboardMarkup()
        markup.add(types.InlineKeyboardButton(text='❌ Отмена' ,callback_data='cancel_send_photo'))
        User = get_user(ref_id)
        if User is not None:
            await bot.send_message(chat_id, f'<b>Приветствуем тебя дорогой друг!👋</b>\nС помощью нашего бота ты можешь со всех своих друзей собрать совместные фото и видео с тобой и вспомнить забытые и смешные моменты!\n\nКак это работает:\n1️⃣Нажмите кнопку в меню "отправить ссылку другу"\n2️⃣Выберите "Поделиться историей Instagram"\n3️⃣﻿﻿Добавьте себе историю в инстаграм как указано инструкции по кнопке\n4️⃣Все фото которые отправят друзья мы будем отображать в разделе "Мои фото"\n\nКак только кто-то из твоих друзей отправит что-то по ссылке мы обязательно тебе об этом скажем😊\n\n\n<b>Ты перешёл по ссылке {User[2]} отправь сюда в чат ваши совместные фото, мы их перешлём к {User[2]}, но чтобы он что-то увидел, ему нужно будет обязательно чем-то поделиться с тобой в ответ 🙂</b>',parse_mode='html',reply_markup=markup)

async def only_photo (User):
    await bot.send_message(User[1], "⚠️ <b>Закончите отправку изображений или нажмите «❌Отмена»</b>", parse_mode='html')
    await start_with_ref_link(User[1], User[3])

async def send_menu_message (chat_id, message):
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True,row_width=2)
    start_button1 = types.KeyboardButton('🌁 МОИ ФОТО')
    start_button2 = types.KeyboardButton('📨 ОБРАТНАЯ СВЯЗЬ')
    start_button3 = types.KeyboardButton('⛓️ ОТПРАВИТЬ ССЫЛКУ ДРУГУ')
    start_button4 = types.KeyboardButton('📕 О НАС')
    markup.add(start_button1,start_button3,start_button2,start_button4)

    await bot.send_message(chat_id, message, parse_mode='html',reply_markup=markup)

asyncio.run(bot.polling(none_stop=True))