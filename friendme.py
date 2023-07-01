from telebot.async_telebot import AsyncTeleBot
import io
import random
import sqlite3
import datetime
from telebot import types
import os
from dotenv import load_dotenv,find_dotenv
import asyncio
from amplitude import Amplitude
from amplitude import BaseEvent

load_dotenv(find_dotenv())
print('bot is activated 🗸')


amplitude = Amplitude(os.getenv('AMP_TOKEN'))
bot = AsyncTeleBot(os.getenv('BOT_TOKEN'))
connect = sqlite3.connect('friendMe.db', check_same_thread=False)
bot_name = "friend_me_bot"
admin_id = 1900666417
admin_id2 = 522380141

#STATUS: 10 - default user | 20 - admin | 30 - blocked


def init_bot():
    
    cursor = connect.cursor()

    cursor.execute("""CREATE TABLE IF NOT EXISTS users(
               id integer PRIMARY KEY AUTOINCREMENT,
               tg_id integer,
               username varchar,
               ref_id number,
               date date,
               status number
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
        cursor.execute("INSERT INTO users VALUES(?,?,?,?,?,?);", (None, chat_id, username, ref_id, datetime.datetime.now(), 10))
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



    if message.chat.id == admin_id:
        print("CLEAR DB")
        cursor = connect.cursor()

        cursor.execute("DROP TABLE IF EXISTS users")
        connect.commit()

        cursor.execute("DROP TABLE IF EXISTS images")
        connect.commit()

        await bot.send_message(message.chat.id, "🗑 Clear DB Success")

        init_bot()
    else:
        await bot.send_message(message.chat.id, "🔒 You are not admin")

# def validateUser(chat_id):
#     current_user = get_user(chat_id)
#     if current_user[5] == 30:
#         bot.send_message(chat_id, "You are blocked! Huilo")
#         return


#Меню Старт
@bot.message_handler(commands=['start'])
async def start(message):

    print("TESTING /START")

    firstStart = False
    ref_id = None
    ref_id_arr = (message.text).split(' ')
    witch_ref_link = False

    if get_user(message.from_user.id) is None:
        firstStart = True

    if len(ref_id_arr) > 1:
        ref_id = ref_id_arr[1]
        if get_user(ref_id) is not None and ref_id != None:
            if int(ref_id) != message.from_user.id:
                witch_ref_link = True

    User = auth_user(message.from_user.id, message.from_user.username, ref_id)

    if User[3] is not None and ref_id == None:
        print("ONLY PHOTO")
        await only_photo(User)
        return

    if witch_ref_link == True:
        if int(ref_id) is message.from_user.id:
            await send_menu_message(message.chat.id, '<b>❌ Вы не можете открыть свою же ссылку</b>')
        else:
            print("IS FIRST?: ", firstStart)
            await start_with_ref_link(User[1], ref_id, firstStart)
    else:
        await send_menu_message(message.chat.id, '<b>Приветствуем тебя дорогой друг!👋</b>\nС помощью нашего бота ты можешь со всех своих друзей собрать совместные фото и видео с тобой и вспомнить забытые и смешные моменты!\n\n<b>Как это работает:</b>\n1️⃣Нажмите кнопку в меню "Собрать фото с друзей"\n2️⃣Выберите "Поделиться историей Instagram"\n3️⃣﻿﻿Добавьте себе историю в инстаграм как указано инструкции по кнопке\n4️⃣Все фото которые отправят друзья мы будем отображать в разделе "Мои фото"\n\nКак только кто-то из твоих друзей отправит что-то по ссылке мы обязательно тебе об этом скажем😊')

async def get_photo_user_album(chat_id):
    cursor = connect.cursor()
    
    #SEND SINGLE PHOTO

    cursor.execute("SELECT * FROM images WHERE to_id=?", (chat_id,))

    if len(cursor.fetchall()) == 0:
        await bot.send_message(chat_id, "📂 Ваша галерея  пока что пуста\n\nЧто бы её пополнить нужно поделится уникальной ссылкой\nДля этого перейдите в раздел <b>Собрать фото с друзей</b>",parse_mode='html')
        return

    cursor.execute("SELECT id_image, from_id FROM images WHERE to_id=? AND media_group_id IS NULL", (chat_id,))
    single_photo = cursor.fetchall()


    if len(single_photo) != 0:
        for photo_id in single_photo:

            # GET USERNAME WITH FROM_ID
            from_user_data = get_user(photo_id[1])
            
            markup = types.InlineKeyboardMarkup()
            item1 = types.InlineKeyboardButton(text='Отправить в ответ', url=f"https://t.me/{bot_name}?start={from_user_data[1]}")
            markup.add(item1)

            await bot.send_photo(chat_id, photo_id[0],caption=f'📸 Пользователь {from_user_data[2]} поделился с вами фотографиями:\n\nЧто бы их увидеть отправьте ему в ответ любую фотографию или видео с его участием\n\nОтправте их по его ссылке или нажмите на кнопку"Отправить в ответ"',reply_markup=markup)

    #SEND MULTI PHOTO
    cursor.execute("SELECT DISTINCT media_group_id FROM images WHERE to_id=? AND media_group_id IS NOT NULL", (chat_id,))
    all_user_photo_groups = cursor.fetchall()

    if len(all_user_photo_groups) != 0:
        for group_id in all_user_photo_groups:
            album = []

            cursor.execute("SELECT id_image FROM images WHERE media_group_id=?", (group_id[0],))
            images = cursor.fetchall()

            for image_id in images:
                album.append(types.InputMediaPhoto(image_id[0]))
                markup = types.InlineKeyboardMarkup()
                item1 = types.InlineKeyboardButton(text='Отправить в ответ',url=f"https://t.me/{bot_name}?start={from_user_data[1]}")
                markup.add(item1)
                await bot.send_media_group(chat_id, album)
                await  bot.send_message(chat_id,f'📸 Пользователь {from_user_data[2]} поделился с вами фотографиями:\n\nЧто бы их увидеть отправьте ему в ответ любую фотографию или видео с его участием\n\nОтправте их по его ссылке или нажмите на кнопку"Отправить в ответ"',reply_markup=markup)


@bot.message_handler(content_types=['text'])
async def chat_message(message):

    User = auth_user(message.from_user.id, message.from_user.username)

    if User[3] is not None:
        await only_photo(User)
        return

    ref_id = message.chat.id
    if message.text == '🌁 Фото со мной':
        await get_photo_user_album(message.chat.id)
         #markup = types.InlineKeyboardMarkup(row_width=2)
         #item_my_photo1 = types.InlineKeyboardButton(text='Отправить в ответ',callback_data='itemmyphoto1')
         #item_my_photo2 = types.InlineKeyboardButton(text='Далее',callback_data='itemmyphoto2')
         #item_my_photo3 = types.InlineKeyboardButton(text='Назад',callback_data='itemmyphoto2')
         #markup.add(item_my_photo1)
         #await bot.send_message(message.chat.id,f'📸 Пользователь {message.from_user.first_name} поделился с вами фотограиями:\n\nЧто бы их увидеть отправьте ему в ответ любую фотографию или видео с его участием\n\nОтправте их по его ссылке или нажмите на кнопку"Отправить в ответ"')

    elif message.text == '📨 Обратная связь':
        markup_info = types.InlineKeyboardMarkup(row_width=2)
        item_info1 = types.InlineKeyboardButton(text='📬 Support',callback_data='instagram_info',url='https://t.me/friendme_support')
        item_info2 = types.InlineKeyboardButton(text='📢 Telegram Group', callback_data='twitter_info',url='https://t.me/+jXQVsce2gYVjZTgy')
        markup_info.add(item_info1,item_info2)
        await bot.send_message(message.chat.id,'<b>Обратная связь</b>\n\nВ случае неисправности бота или зафиксированной ошибке , просьба обратится в нашу тех-поддержу по адресу : @friendme_support\n\nТак же если у вас сеть предложения для улучшения нашего сервиса ,можете обратиться по адресу : @friendme_offers\n\n<b>FriendMe в социальных сетях:</b>',parse_mode='html',reply_markup=markup_info)
    elif message.text == '📸 Собрать фото с друзей':
        markup = types.InlineKeyboardMarkup(row_width=1)
        item1 = types.InlineKeyboardButton(text='Поделиться в Instagram Stories',callback_data='share1')
        item2 = types.InlineKeyboardButton('Поделиться в Telegram',switch_inline_query=f'\n\n👋 Приветствую! Я бы хотел поделиться с вами уникальной ссылкой 🔗: https://t.me/{bot_name}?start={ref_id}\n\nБлагодаря этой ссылке, ты сможешь легко загружать свои фотографии, и я с радостью их получу. Давай начнем делиться восхитительными снимками вместе! 🤩')
        item3 = types.InlineKeyboardButton(text='Показать ссылку в чате',callback_data='share3')
        markup.add(item1,item2,item3)
        await bot.send_message(message.chat.id,'<b>⤴️ Чтобы собрать совместные фотографии с друзей, вам нужно поделиться с ними уникальной ссылкой, выберите удобный для вас способ ниже:</b>',parse_mode='html',reply_markup=markup)
    elif message.text == '📕 О нас':
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
                    await bot.send_message(message.chat.id, f"👀 Для просмотра данных фотографий вашему другу потребуется отправить в ответ какие-то фотографии с вами, после чего мы обязательно их перешлем вам :) \n\nЧтобы отправить ещё что-то пользователю <b>«{friendUser[2]}»</b> нажмите кнопку ниже <b>«Отправить ещё»</b>", reply_markup=markup, parse_mode='html')
                    await bot.send_message(ref_id,'💌 С вами поделились фотографиями\n\nДля того что бы их посмотреть зайдите в раздел <b>🌁 Фото со мной</b>',parse_mode='html')

                    cursor.execute("UPDATE users SET ref_id=? WHERE tg_id=?", (None, User[1], ))
                    connect.commit()
        else:
            await send_menu_message(message.chat.id, "✅ Вы успешно отправили фотографию!")
            await bot.send_message(ref_id,'💌 С вами поделились фотографиями\n\nДля того что бы их посмотреть зайдите в раздел <b>🌁 Фото со мной</b>',parse_mode='html')
            await bot.send_message(message.chat.id, f"👀 Для просмотра данных фотографий вашему другу потребуется отправить в ответ какие-то фотографии с вами, после чего мы обязательно их перешлем вам  :) \n\nЧтобы отправить ещё что-то пользователю <b>«{friendUser[2]}»</b> нажмите кнопку ниже <b>«Отправить ещё»</b>", reply_markup=markup, parse_mode='html')

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

        await bot.send_message(callback.message.chat.id, '<b>Приветствуем тебя дорогой друг!👋</b>\nС помощью нашего бота ты можешь со всех своих друзей собрать совместные фото и видео с тобой и вспомнить забытые и смешные моменты!\n\n<b>Как это работает:</b>\n1️⃣Нажмите кнопку в меню "Собрать фото с друзей"\n2️⃣Выберите "Поделиться историей Instagram"\n3️⃣﻿﻿Добавьте себе историю в инстаграм как указано инструкции по кнопке\n4️⃣Все фото которые отправят друзья мы будем отображать в разделе "Мои фото"\n\nКак только кто-то из твоих друзей отправит что-то по ссылке мы обязательно тебе об этом скажем😊',parse_mode='html')
        
        return

    if User[3] is not None:
        await only_photo(User)
        return

    ref_id = callback.message.chat.id

    if callback.data == 'itemmyphoto1':
       #await get_photo_user_album(callback.message.chat.id)
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
        item_next = types.InlineKeyboardButton(text='Начать',callback_data='item_next1')
        markup.add(item_next)
        image = open('images/inst.jpg', 'rb')
        await bot.send_photo(callback.message.chat.id,image,caption='Чтобы выложить историю в инстаграм как показано ниже, сделайте 3 простых шага:',reply_markup=markup)
    elif callback.data == 'share2':
        await bot.send_message(callback.message.chat.id,'')
    elif callback.data == 'share3':
        await bot.send_message(callback.message.chat.id, f'https://t.me/{bot_name}?start={ref_id}')
    elif callback.data == 'item_next1':
        media = open("images/img_inst.jpg", "rb")
        markup = types.InlineKeyboardMarkup()
        item_back = types.InlineKeyboardButton(text='Назад',callback_data='item_back2')
        item_next = types.InlineKeyboardButton(text='Далее', callback_data='item_next2')
        markup.add(item_back,item_next)
        await bot.edit_message_media(chat_id =callback.message.chat.id, message_id=callback.message.message_id, media=types.InputMediaPhoto(media))
        await bot.edit_message_caption(chat_id=callback.message.chat.id, message_id=callback.message.message_id,caption="1️⃣Скачайте изображение которое мы отправили:",reply_markup=markup)
    elif callback.data == 'item_back2':
        markup = types.InlineKeyboardMarkup()
        item_next = types.InlineKeyboardButton(text='Начать', callback_data='item_next1')
        markup.add(item_next)
        media = open('images/inst.jpg', 'rb')
        await bot.edit_message_media(chat_id=callback.message.chat.id, message_id=callback.message.message_id,media=types.InputMediaPhoto(media))
        await bot.edit_message_caption(chat_id=callback.message.chat.id, message_id=callback.message.message_id,caption='Чтобы выложить историю в инстаграм как показано ниже, сделайте 3 простых шага:', reply_markup=markup)
    elif callback.data == 'item_next2':
        media = open('images/inst.jpg','rb')
        markup = types.InlineKeyboardMarkup()
        item_back = types.InlineKeyboardButton(text='Назад', callback_data='item_back3')
        item_next = types.InlineKeyboardButton(text='Далее', callback_data='item_next3')
        markup.add(item_back,item_next)
        await bot.edit_message_media(chat_id =callback.message.chat.id, message_id=callback.message.message_id, media=types.InputMediaPhoto(media))
        await bot.edit_message_caption(chat_id=callback.message.chat.id,message_id=callback.message.message_id,caption='2️⃣Загрузите изображение в инстаграм сторис:',reply_markup=markup)
    elif callback.data == 'item_back3':
        markup = types.InlineKeyboardMarkup()
        item_back = types.InlineKeyboardButton(text='Назад', callback_data='item_back2')
        item_next = types.InlineKeyboardButton(text='Далее', callback_data='item_next2')
        markup.add(item_back, item_next)
        media = open('images/img_inst.jpg', 'rb')
        await bot.edit_message_media(chat_id=callback.message.chat.id, message_id=callback.message.message_id,media=types.InputMediaPhoto(media))
        await bot.edit_message_caption(chat_id=callback.message.chat.id, message_id=callback.message.message_id,caption='️1️⃣Скачайте изображение которое мы отправили:',reply_markup=markup)
    elif callback.data == 'item_next3':
        media = open('images/img_inst.jpg','rb')
        markup = types.InlineKeyboardMarkup()
        item_back = types.InlineKeyboardButton(text='Назад', callback_data='item_back4')
        item_next = types.InlineKeyboardButton(text='Далее', callback_data='item_share4')
        markup.add(item_back,item_next)
        await bot.edit_message_media(chat_id=callback.message.chat.id, message_id=callback.message.message_id,media=types.InputMediaPhoto(media))
        await bot.edit_message_caption(chat_id=callback.message.chat.id, message_id=callback.message.message_id,caption=f"3️⃣Добавьте стикер с уникальной ссылкой:⤵️\n\nhttps://t.me/{bot_name}?start={ref_id}",reply_markup=markup)
    elif callback.data == 'item_back4':
        markup = types.InlineKeyboardMarkup()
        item_back = types.InlineKeyboardButton(text='Назад', callback_data='item_back3')
        item_next = types.InlineKeyboardButton(text='Далее', callback_data='item_next3')
        markup.add(item_back, item_next)
        media = open('images/inst.jpg', 'rb')
        await bot.edit_message_media(chat_id=callback.message.chat.id, message_id=callback.message.message_id,media=types.InputMediaPhoto(media))
        await bot.edit_message_caption(chat_id=callback.message.chat.id, message_id=callback.message.message_id,caption='️2️⃣Загрузите изображение в инстаграм сторис:',reply_markup=markup)
    elif callback.data == 'item_share4':
        media = open('images/inst.jpg','rb')
        markup = types.InlineKeyboardMarkup()
        item_back = types.InlineKeyboardButton(text='Назад', callback_data='item_back5')
        markup.add(item_back)
        await bot.edit_message_media(chat_id=callback.message.chat.id, message_id=callback.message.message_id,media=types.InputMediaPhoto(media))
        await bot.edit_message_caption(chat_id=callback.message.chat.id, message_id=callback.message.message_id,caption="🎉Поздравляем! Вы поделились ссылкой с друзьями, теперь осталось подождать пока кто-то отправит какие-то фотографии по вашей ссылке :)",reply_markup=markup)
    elif callback.data == 'item_back5':
        markup = types.InlineKeyboardMarkup()
        item_back = types.InlineKeyboardButton(text='Назад', callback_data='item_back4')
        item_next = types.InlineKeyboardButton(text='Далее', callback_data='item_share4')
        markup.add(item_back, item_next)
        media = open('images/img_inst.jpg','rb')
        await bot.edit_message_media(chat_id=callback.message.chat.id, message_id=callback.message.message_id,media=types.InputMediaPhoto(media))
        await bot.edit_message_caption(chat_id=callback.message.chat.id, message_id=callback.message.message_id,caption=f"3️⃣Добавьте стикер с уникальной ссылкой:⤵️\n\nhttps://t.me/{bot_name}?start={ref_id}", reply_markup=markup)
async def error_command (chat_id):
    return await bot.send_message(chat_id,'<b>⛔ Произошла ошибка, данная команда недоступна!</b>',parse_mode='html')

async def start_with_ref_link (chat_id, ref_id, isFirstStart=False):
        markup = types.InlineKeyboardMarkup()
        markup.add(types.InlineKeyboardButton(text='❌ Отмена' ,callback_data='cancel_send_photo'))
        User = get_user(ref_id)
        if User is not None:
            if isFirstStart:
                await bot.send_message(chat_id, f'<b>Приветствуем тебя дорогой друг!👋</b>\nС помощью нашего бота ты можешь со всех своих друзей собрать совместные фото и видео с тобой и вспомнить забытые и смешные моменты!\n\n<b>Как это работает:</b>\n1️⃣Ты отправляешь в чат-бота FriendMe ваши совместные фото с <b>{User[2]}</b>\n2️⃣Мы пересылаем отправленные тобою фото к <b>{User[2]}</b>\n3️⃣Ждём пока <b>{User[2]}</b> отправит тебе тоже что-то в ответ ☺️\n\n\n<b>Ты перешёл по ссылке <b>{User[2]}</b> отправь сюда в чат ваши совместные фото, мы их перешлём к <b>{User[2]}</b>, но чтобы он что-то увидел, ему нужно будет обязательно чем-то поделиться с тобой в ответ 🙂</b>',parse_mode='html',reply_markup=markup)
            else:
                await bot.send_message(chat_id, f'<b>Ты перешёл по ссылке <b>{User[2]}</b> отправь сюда в чат ваши совместные фото, мы их перешлём к <b>{User[2]}</b>, но чтобы он что-то увидел, ему нужно будет обязательно чем-то поделиться с тобой в ответ 🙂</b>',parse_mode='html',reply_markup=markup)

async def only_photo (User):
    await bot.send_message(User[1], "⚠️ <b>Закончите отправку изображений или нажмите «❌Отмена»</b>", parse_mode='html')
    await start_with_ref_link(User[1], User[3])

async def send_menu_message (chat_id, message):
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True,row_width=2)
    start_button1 = types.KeyboardButton('🌁 Фото со мной')
    start_button2 = types.KeyboardButton('📨 Обратная связь')
    start_button3 = types.KeyboardButton('📸 Собрать фото с друзей')
    start_button4 = types.KeyboardButton('📕 О нас')
    markup.add(start_button1,start_button3,start_button2,start_button4)

    await bot.send_message(chat_id, message, parse_mode='html',reply_markup=markup)

asyncio.run(bot.polling(none_stop=True))