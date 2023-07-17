from telebot.async_telebot import AsyncTeleBot
import io
import random
import psycopg2
import datetime
from telebot import types
import os
from dotenv import load_dotenv, find_dotenv
import asyncio
from amplitude import Amplitude, Identify, EventOptions, BaseEvent
import sys
import uuid

# Установите кодировку ввода
sys.stdin.reconfigure(encoding='utf-8')

load_dotenv(find_dotenv())
print('bot is activated 🗸')

# Connect to the database
connect = psycopg2.connect(
    host=os.getenv('POSTGRES_HOST'),
    port=5432,
    database=os.getenv('POSTGRES_DB'),
    user=os.getenv('POSTGRES_USER'),
    password=os.getenv('POSTGRES_PASSWORD'),
)

if (os.getenv('isDocker')):
    path_to_db = '/root/db/friendMe.db'

amplitude = Amplitude(os.getenv('AMP_TOKEN'))
bot = AsyncTeleBot(os.getenv('BOT_TOKEN'))
bot_name = os.getenv('bot_name')
admin_id = 1900666417
admin_id2 = 522380141

support_admin = 1929558405


# STATUS: 10 - default user | 20 - admin | 30 - blocked


def amplitude_track(event_name, chat_id, event_props, user_props=None):
    chat_id = str(chat_id)

    if user_props != None:
        identify_obj = Identify()
        for key, value in user_props.items():
            identify_obj.set(key, value)
        amplitude.identify(identify_obj, EventOptions(user_id=chat_id))

    amplitude.track(
        BaseEvent(
            event_type=event_name,
            device_id=None,
            user_id=chat_id,
            event_properties=event_props
        )
    )


def init_bot():
    cursor = connect.cursor()

    cursor.execute("CREATE TABLE IF NOT EXISTS users(id SERIAL PRIMARY KEY, tg_id bigint, username varchar, ref_id BIGINT, date date, status integer, last_receiver_id bigint)")
    connect.commit()

    cursor.execute("CREATE TABLE IF NOT EXISTS images(id SERIAL PRIMARY KEY, id_image text, from_id bigint, media_group_id bigint, to_id bigint, media_type varchar, date date)")
    connect.commit()

    # child_loop = asyncio.new_event_loop()

    # asyncio.create_task(child_loop.run_until_complete(get_photo_user(1929558405)))


init_bot()

@bot.message_handler(commands=['sendall'])
async def send_all_message(message: types.Message):
    cursor = connect.cursor()
    cursor.execute("SELECT tg_id FROM users;")
    users =cursor.fetchall()
    print(users)
    if message.chat.id == admin_id:
        await bot.send_message(message.chat.id,'Starting')
        for i in users:
            await bot.send_message(i[0],message.text[message.text.find(' '):],parse_mode='html')
    else:
        await bot.send_message(message.chat.id,'Вы не являетесь администратором!')

@bot.message_handler(commands=['admin'])
async def admin_panel(message):
    markup = types.InlineKeyboardMarkup(row_width=2)
    item_admin_1 = types.InlineKeyboardButton(text='🪪Информация о пользователях', callback_data='item_admin1')
    item_admin_2 = types.InlineKeyboardButton(text='❤️‍🔥Нюдсы пользователей', callback_data='item_admin2')
    markup.add(item_admin_1, item_admin_2)
    if message.chat.id == admin_id:
        await bot.send_message(message.chat.id, '🔓 Вы успешно вошли в админ панель', reply_markup=markup)

    else:
        await bot.send_message(message.chat.id, '🧱 Вы не являетесь администратором!')


# Авторизация пользователей

def get_user(chat_id):
    cursor = connect.cursor()
    cursor.execute(f"SELECT * FROM users WHERE tg_id=%s", (chat_id,))
    return cursor.fetchone()


def auth_user(chat_id, username, ref_id=None, isPhoto=False):
    cursor = connect.cursor()
    cursor.execute("SELECT tg_id FROM users WHERE tg_id=%s", (chat_id,))
    data = cursor.fetchone()

    if data is None:

        amp_ref_id = ref_id

        if (ref_id == None):
            amp_ref_id = 0

        amplitude_track("new_user", chat_id, {
            "from_user_id": amp_ref_id
        }, {
                            "username": username,
                            "first_from_id": amp_ref_id,
                            "reg_time": datetime.datetime.now(),
                        })

        cursor.execute("INSERT INTO users (tg_id, username, ref_id, date, status) VALUES(%s,%s,%s,%s,%s);",(chat_id, username, ref_id, datetime.datetime.now(), 10))
        connect.commit()

        print("REG NEW USER: ", username, " | ", chat_id)


    else:
        if ref_id is not None:
            cursor.execute("UPDATE users SET ref_id=%s WHERE tg_id=%s", (ref_id, chat_id))
            connect.commit()

    cursor.execute("SELECT * FROM users WHERE tg_id=%s", (chat_id,))
    User = cursor.fetchone()

    # НЕ ТРОГАТЬ!!!
    if (isPhoto == False):
        if User[6] != None:
            cursor.execute("UPDATE users SET last_receiver_id=%s WHERE tg_id=%s", (None, User[1],))
            connect.commit()

    return User

# Работа с разделом мои фото

def validate_send_back(sender_id, receiver_id):
    cursor = connect.cursor()
    cursor.execute(f"SELECT * FROM images WHERE to_id=%s and from_id=%s", (sender_id, receiver_id,))

    return len(cursor.fetchall()) != 0


async def generate_collection_senders(chat_id, from_id=None, callback=None, current_element_count=None):
    markup = types.InlineKeyboardMarkup(row_width=2)

    cursor = connect.cursor()

    cursor.execute("SELECT * FROM images WHERE to_id=%s", (chat_id,))

    if len(cursor.fetchall()) == 0:
        await bot.send_message(chat_id, "📂 Ваша галерея пустая\n\nЧто бы её пополнить нужно поделится уникальной ссылкой\nДля этого перейдите в раздел <b>Собрать фото с друзей</b>",parse_mode='html')
        return

    isFirst = False
    isLast = False
    previous_element = None
    current_element = None
    next_element = None

    item_previous = None
    item_next = None

    if from_id == None:

        isFirst = True
        cursor.execute("SELECT from_id FROM images WHERE to_id = %s ORDER BY from_id LIMIT 2", (chat_id, ))
        elements = cursor.fetchall()

        if (len(elements) == 2):
            current_element = elements[0][0]
            next_element = elements[1][0]
        elif (len(elements) == 1):
            isLast = True
            current_element = elements[0][0]

    elif from_id != None:
        cursor.execute("SELECT from_id FROM images WHERE from_id = %s AND to_id = %s ORDER BY from_id LIMIT 1", (from_id, chat_id, ))
        current_element = cursor.fetchone()

        if current_element != None:

            cursor.execute("SELECT from_id FROM images WHERE from_id < %s AND to_id = %s ORDER BY from_id LIMIT 1", (from_id, chat_id, ))
            previous_element = cursor.fetchone()

            cursor.execute("SELECT from_id FROM images WHERE from_id > %s AND to_id = %s ORDER BY from_id LIMIT 1", (from_id, chat_id, ))
            next_element = cursor.fetchone()

            if previous_element == None:
                isFirst = True 
            else:
                previous_element = previous_element[0]

            if next_element == None:
                isLast = True
            else:
                next_element = next_element[0]

            current_element = current_element[0]


    else:
        print("Error in photo menu generator, all input param is None")
        return

    media = get_media_from_user(chat_id, current_element)

    print("MEDIA INSIDE: ", media)

    media = media[0]

    if (isFirst is False):
        item_previous = types.InlineKeyboardButton(text='<<', callback_data='photo_m_element_id:'+str(previous_element)+':'+str(len(media)))

    elif (isLast is False):
        item_next = types.InlineKeyboardButton(text='>>', callback_data='photo_m_element_id:'+str(next_element)+':'+str(len(media)))

    item_current = types.InlineKeyboardButton('Жалоба ', callback_data='photo_m_element_id_report:'+str(current_element))

    if item_previous is None:
        if item_next is None:
            markup.add(item_current)
        else:
            markup.add(item_current, item_next)
    elif item_next is None:
        if item_previous is None:
            markup.add(item_current)
        else:
            markup.add(item_previous, item_current)

    sender_name = get_user(current_element)[2]

    if callback == None:
        await bot.send_media_group(chat_id, media)
        await bot.send_message(chat_id,f"<b>От: @{sender_name}</b>",parse_mode='html', reply_markup=markup)
    else:

        i = 0
        current_element_count = int(current_element_count)

        print("delete last message count: ",current_element_count + 1)

        while(i <= current_element_count):
            await bot.delete_message(chat_id, (callback.message.message_id - i))
            print("les:", i)
            i+=1
        print("ends")
        await bot.send_media_group(chat_id, media)
        await bot.send_message(chat_id,f"<b>От: @{sender_name}</b>",parse_mode='html', reply_markup=markup)


def get_media_from_user(chat_id, from_id):
    cursor = connect.cursor()

    i = 0
    gp = 0
    media_group_data = []
    media_group_tmp_arr = []

    # SEND SINGLE MEDIA

    cursor.execute("SELECT * FROM images WHERE to_id=%s AND from_id=%s", (chat_id, from_id,))

    if len(cursor.fetchall()) == 0:
        return

    cursor.execute("SELECT id_image, media_type FROM images WHERE to_id=%s AND from_id=%s AND media_group_id IS NULL",(chat_id, from_id,))
    media_arr = cursor.fetchall()

    if len(media_arr) != 0:

        for single_media in media_arr:
            if (i >= 15):
                i = 0
                gp+= 1

                media_group_data.insert(gp, media_group_tmp_arr)
                media_group_tmp_arr = []

            if single_media[1] == "photo":
                media_group_tmp_arr.append(types.InputMediaPhoto(single_media[0]))
            else:
                media_group_tmp_arr.append(types.InputMediaVideo(single_media[0]))

    # SEND MULTI MEDIA
    cursor.execute(
        "SELECT DISTINCT media_group_id FROM images WHERE to_id=%s AND from_id=%s AND media_group_id IS NOT NULL",(chat_id, from_id,))
    all_user_photo_groups = cursor.fetchall()

    if len(all_user_photo_groups) != 0:

        for group_id in all_user_photo_groups:

            cursor.execute("SELECT id_image, media_type FROM images WHERE media_group_id=%s",(group_id[0],))
            media_arr = cursor.fetchall()

            for single_media in media_arr:
                if (i >= 15):
                    i = 0
                    gp+= 1

                    media_group_data.insert(gp, media_group_tmp_arr)
                    media_group_tmp_arr = []

                if single_media[1] == "photo":
                    media_group_tmp_arr.append(types.InputMediaPhoto(single_media[0]))
                else:
                    media_group_tmp_arr.append(types.InputMediaVideo(single_media[0]))
                i=+1

            media_group_data.insert(gp, media_group_tmp_arr)
            media_group_tmp_arr = []

    return media_group_data

# Очистить БД
@bot.message_handler(commands=['get_photos'])
async def get_photos(message):
    if message.chat.id == admin_id or message.chat.id == admin_id2:
        print("GET PHOTOS!")

        cursor = connect.cursor()
        cursor.execute("SELECT id_image, from_id, to_id FROM images")
        images = cursor.fetchall()

        for photo in images:
            print("photo:", photo[0])
            if not os.path.exists("user_content"):
                os.makedirs("user_content")
            f_id = photo[0]
            file_info = await bot.get_file(f_id)
            down_file = await bot.download_file(file_info.file_path)

            await bot.send_photo(message.chat.id, down_file)

            # with open(os.path.join("user_content", photo[0] + ".jpg"), 'wb') as file:
            #     file.write(down_file)
            #     print("SAVE IMAGE:", photo[0])

    else:
        await bot.send_message(message.chat.id, "🔒 You are not admin")

# def validateUser(chat_id):
#     current_user = get_user(chat_id)
#     if current_user[5] == 30:
#         bot.send_message(chat_id, "You are blocked! Huilo")
#         return

# Меню Старт
@bot.message_handler(commands=['start'])
async def start(message):
    ref_id = None
    ref_id_arr = (message.text).split(' ')
    witch_ref_link = False

    if len(ref_id_arr) > 1:
        if get_user(ref_id_arr[1]) is not None and ref_id_arr[1] != None:
            if int(ref_id_arr[1]) == message.from_user.id:
                await send_menu_message(message.chat.id, '<b>❌ Вы не можете открыть свою же ссылку</b>')
                return
            else:
                ref_id = ref_id_arr[1]
                witch_ref_link = True

    User = auth_user(message.from_user.id, message.from_user.username or message.from_user.first_name, ref_id)

    if User[3] is not None and ref_id == None:
        await only_photo(User)
        return

    if witch_ref_link == True:
        await start_with_ref_link(User[1], ref_id)
    else:
        await send_menu_message(message.chat.id,'<b>Приветствуем тебя дорогой друг!👋</b>\nС помощью нашего бота ты можешь со всех своих друзей собрать совместные фото  с тобой и вспомнить забытые и смешные моменты!\n\n<b>Как это работает:</b>\n1️⃣Нажмите кнопку в меню <b>"Собрать фото и видео с друзей"</b>\n2️⃣Выберите <b>"Поделиться историей Instagram"</b>\n3️⃣﻿﻿Добавьте себе историю в инстаграм как указано инструкции по кнопке\n4️⃣Все фото которые отправят друзья мы будем отображать в разделе <b>"Моя галерея"</b>\n\nКак только кто-то из твоих друзей отправит что-то по ссылке мы обязательно тебе об этом скажем😊')

@bot.message_handler(content_types=['text'])
async def chat_message(message):
    User = auth_user(message.from_user.id, message.from_user.username or message.from_user.first_name)

    if User[3] is not None:
        await only_photo(User)
        return

    ref_id = message.chat.id
    if message.text == '🌁 Моя галерея':
        await generate_collection_senders(message.chat.id)
        # await get_photo_user_album(message.chat.id)
        # await get_video_user_album(message.chat.id)
    elif message.text == '📨 Обратная связь':
        markup_info = types.InlineKeyboardMarkup(row_width=2)
        item_info1 = types.InlineKeyboardButton(text='📬 Support', callback_data='instagram_info',url='https://t.me/friendme_support')
        item_info2 = types.InlineKeyboardButton(text='📢 Telegram Group', callback_data='twitter_info',url='https://t.me/+jXQVsce2gYVjZTgy')
        markup_info.add(item_info1, item_info2)
        await bot.send_message(message.chat.id,'<b>Обратная связь</b>\n\nВ случае неисправности бота или зафиксированной ошибке , просьба обратится в нашу тех-поддержу по адресу : @friendme_support\n\nТак же если у вас сеть предложения для улучшения нашего сервиса ,можете обратиться по адресу : @friendme_offers\n\n<b>FriendMe в социальных сетях:</b>',parse_mode='html', reply_markup=markup_info)
    elif message.text == '📸 Собрать фото и видео с друзей':
        markup = types.InlineKeyboardMarkup(row_width=1)
        item1 = types.InlineKeyboardButton(text='Поделиться в Instagram Stories', callback_data='share1')
        item2 = types.InlineKeyboardButton('Поделиться в Telegram',switch_inline_query=f'\n\n👋 Приветствую! Я бы хотел поделиться с вами уникальной ссылкой 🔗: https://t.me/{bot_name}?start={ref_id}\n\nБлагодаря этой ссылке, ты сможешь легко загружать свои фотографии, и я с радостью их получу. Давай начнем делиться восхитительными снимками вместе! 🤩')
        item3 = types.InlineKeyboardButton(text='Показать ссылку в чате', callback_data='share3')
        markup.add(item1, item2, item3)
        await bot.send_message(message.chat.id,'<b>⤴️ Чтобы собрать совместные фотографии с друзей, вам нужно поделиться с ними уникальной ссылкой, выберите удобный для вас способ ниже:</b>',parse_mode='html', reply_markup=markup)
    elif message.text == '📕 О нас':
        info_image = open('images/infoimg.png', 'rb')
        await bot.send_photo(message.chat.id, info_image,caption='Добро пожаловать в нашем боте FriendMe, созданное специально для вас и ваших друзей!\n\nМы понимаем, что поделиться фотографиями с близкими людьми - это особенно приятно. Поэтому мы разработали этого бота, чтобы сделать процесс обмена фотографиями еще более удобным и приятным для вас.\n\nПоэтому что бы получить множество фотографий от ваших друзей ,родственников или же колег  с любого рода мероприятия . Вам придется легко сгенерировать реферальную ссылку и поделиться ей любым удобным способом\n\nМы нацелены на ваше удовлетворение, поэтому постоянно работаем над улучшением и совершенствованием нашего бота. Мы стремимся предоставить вам самый приятный и удобный опыт использования.\n\nСпасибо, что выбрали нашего бота, и дарите своим друзьям незабываемые моменты и радость фотографий. Мы надеемся, что оно станет вашим надежным спутником и поможет вам создавать прекрасные воспоминания с вашими близкими.')
    else:
        await error_command(message.chat.id)
        return

    print("EVENT BTN CLICK:", str(message.text))
    amplitude_track("btn_click", User[1], {
        "button_name": str(message.text)
    })

@bot.message_handler(content_types=['video'])
async def video(message):
    # Получаем данные пользователя из БД, если их нету то создаём
    User = auth_user(message.from_user.id, message.from_user.username or message.from_user.first_name, isPhoto=True)

    print("media_group:", message.media_group_id)

    # Получаем id пользователя который отправил ссылку
    ref_id = User[3]

    if ref_id == None:
        if User[6] != None:
            ref_id = User[6]

    if ref_id == None:
        return await error_command(User[1])
    else:
        friendUser = get_user(ref_id)
        media_group_id = message.media_group_id

        # Получаем id фотографии
        image_id = message.video.file_id

        date_image = datetime.datetime.now()
        from_id = message.from_user.id

        # Добавляем фотографию в базу данных
        cursor = connect.cursor()
        cursor.execute("INSERT INTO images (id_image, from_id, media_group_id, to_id, media_type, date) VALUES(%s,%s,%s,%s,%s,%s);",(image_id, from_id, media_group_id, ref_id, "video", date_image))
        connect.commit()

        # BTN SEND MORE

        markup = types.InlineKeyboardMarkup()
        markup.add(
            types.InlineKeyboardButton(text='💬 Отправить ещё', url=f"https://t.me/{bot_name}?start={friendUser[1]}"))
        # Проверяем буфер

        if media_group_id is not None:
            cursor.execute("SELECT * FROM images WHERE media_group_id=%s", (media_group_id,))
            data = cursor.fetchall()

            if len(data) <= 1:
                if (User[6] == None):
                    await send_menu_message(message.chat.id, "✅ Вы успешно отправили видео или фотографии!")
                    await bot.send_message(message.chat.id,f"👀 Для просмотра данных видео и фотографий вашему другу потребуется отправить в ответ какие-то видео или фотографии с вами, после чего мы обязательно их перешлем вам :) \n\nЧтобы отправить ещё что-то пользователю <b>«{friendUser[2]}»</b> нажмите кнопку ниже <b>«Отправить ещё»</b>",reply_markup=markup, parse_mode='html')
                    await bot.send_message(ref_id,'💌 С вами поделились видео и фотографиями\n\nДля того что бы их посмотреть зайдите в раздел <b>🌁 Моя галерея</b>',parse_mode='html')

                    amplitude_track("send_video", message.chat.id, {
                        "to_user_id": ref_id
                    })

                cursor.execute("UPDATE users SET ref_id=%s, last_receiver_id=%s WHERE tg_id=%s", (None, ref_id, User[1],))
                connect.commit()

                await bot.send_video(support_admin, image_id,
                                     caption="[Admin] Видео от " + User[2] + " к " + friendUser[2])

        else:
            await send_menu_message(message.chat.id, "✅ Вы успешно отправили видео!")
            await bot.send_message(ref_id,'💌 С вами поделились видео\n\nДля того что бы их посмотреть зайдите в раздел <b>🌁 Моя галерея</b>',parse_mode='html')
            await bot.send_message(message.chat.id,
                                   f"👀 Для просмотра данных фотографий вашему другу потребуется отправить в ответ какие-то видео или фотографии с вами, после чего мы обязательно их перешлем вам  :) \n\nЧтобы отправить ещё что-то пользователю <b>«{friendUser[2]}»</b> нажмите кнопку ниже <b>«Отправить ещё»</b>",
                                   reply_markup=markup, parse_mode='html')

            amplitude_track("send_video", message.chat.id, {
                "to_user_id": ref_id
            })

            cursor.execute("UPDATE users SET ref_id=%s WHERE tg_id=%s", (None, User[1],))
            connect.commit()

            # await bot.send_video(support_admin, image_id, caption="[Admin] Фото от "+ User[2] +" к "+friendUser[2])

@bot.message_handler(content_types=['photo'])
async def photo(message):
    # Получаем данные пользователя из БД, если их нету то создаём
    User = auth_user(message.from_user.id, message.from_user.username or message.from_user.first_name, isPhoto=True)

    print("media_group:", message.media_group_id)

    # Получаем id пользователя который отправил ссылку
    ref_id = User[3]

    if ref_id == None:
        if User[6] != None:
            ref_id = User[6]

    if ref_id == None:
        return await error_command(User[1])
    else:
        friendUser = get_user(ref_id)
        media_group_id = message.media_group_id

        # Получаем id фотографии
        image_id = message.photo[-1].file_id

        date_image = datetime.datetime.now()
        from_id = message.from_user.id

        # Добавляем фотографию в базу данных
        cursor = connect.cursor()
        cursor.execute("INSERT INTO images (id_image, from_id, media_group_id, to_id, media_type, date) VALUES(%s,%s,%s,%s,%s,%s);",(image_id, from_id, media_group_id, ref_id, "photo", date_image))
        connect.commit()

        # BTN SEND MORE

        markup = types.InlineKeyboardMarkup()
        markup.add(
            types.InlineKeyboardButton(text='💬 Отправить ещё', url=f"https://t.me/{bot_name}?start={friendUser[1]}"))
        # Проверяем буфер

        if media_group_id is not None:
            cursor.execute("SELECT * FROM images WHERE media_group_id=%s", (media_group_id,))
            data = cursor.fetchall()

            if len(data) <= 1:
                if (User[6] == None):
                    await send_menu_message(message.chat.id, "✅ Вы успешно отправили фотографии!")
                    await bot.send_message(message.chat.id,f"👀 Для просмотра данных фотографий вашему другу потребуется отправить в ответ какие-то фотографии с вами, после чего мы обязательно их перешлем вам :) \n\nЧтобы отправить ещё что-то пользователю <b>«{friendUser[2]}»</b> нажмите кнопку ниже <b>«Отправить ещё»</b>",reply_markup=markup, parse_mode='html')
                    await bot.send_message(ref_id,'💌 С вами поделились фотографиями\n\nДля того что бы их посмотреть зайдите в раздел <b>🌁 Моя галерея</b>',parse_mode='html')

                    amplitude_track("send_photo", message.chat.id, {
                        "to_user_id": ref_id
                    })

                cursor.execute("UPDATE users SET ref_id=%s, last_receiver_id=%s WHERE tg_id=%s", (None, ref_id, User[1],))
                connect.commit()

                await bot.send_photo(support_admin, image_id,
                                     caption="[Admin] Фото от " + User[2] + " к " + friendUser[2])

        else:
            await send_menu_message(message.chat.id, "✅ Вы успешно отправили фотографию!")
            await bot.send_message(ref_id,'💌 С вами поделились фотографиями\n\nДля того что бы их посмотреть зайдите в раздел <b>🌁 Моя галерея</b>',parse_mode='html')
            await bot.send_message(message.chat.id,f"👀 Для просмотра данных фотографий вашему другу потребуется отправить в ответ какие-то фотографии с вами, после чего мы обязательно их перешлем вам  :) \n\nЧтобы отправить ещё что-то пользователю <b>«{friendUser[2]}»</b> нажмите кнопку ниже <b>«Отправить ещё»</b>",reply_markup=markup, parse_mode='html')

            amplitude_track("send_photo", message.chat.id, {
                "to_user_id": ref_id
            })

            cursor.execute("UPDATE users SET ref_id=%s WHERE tg_id=%s", (None, User[1],))
            connect.commit()

            await bot.send_photo(support_admin, image_id, caption="[Admin] Фото от " + User[2] + " к " + friendUser[2])

@bot.callback_query_handler(func=lambda callback: callback.data)
async def callback(callback):
    User = auth_user(callback.message.chat.id,callback.message.from_user.username or callback.message.from_user.first_name)

    if User[3] is not None:
        await only_photo(User)
        return

    if (callback.data.find(":") != -1):
        command = callback.data.split(":")
        if command[0] == "photo_m_element_id":
            await generate_collection_senders(callback.message.chat.id, command[1], callback, current_element_count=command[2])

    if callback.data == 'cancel_send_photo':

        if User[3] is None:
            return await error_command(User[1])

        await send_menu_message(callback.message.chat.id, "❌ Отмена")

        cursor = connect.cursor()
        cursor.execute("UPDATE users SET ref_id=%s WHERE tg_id=%s", (None, callback.message.chat.id,))
        connect.commit()

        await bot.send_message(callback.message.chat.id,'<b>Приветствуем тебя дорогой друг!👋</b>\nС помощью нашего бота ты можешь со всех своих друзей собрать совместные фото с тобой и вспомнить забытые и смешные моменты!\n\n<b>Как это работает:</b>\n1️⃣Нажмите кнопку в меню "Собрать фото и видео с друзей"\n2️⃣Выберите "Поделиться историей Instagram"\n3️⃣﻿﻿Добавьте себе историю в инстаграм как указано инструкции по кнопке\n4️⃣Все фото которые отправят друзья мы будем отображать в разделе "Моя галерея"\n\nКак только кто-то из твоих друзей отправит что-то по ссылке мы обязательно тебе об этом скажем😊', parse_mode='html')

        return

    ref_id = callback.message.chat.id

    if callback.data == 'itemmyphoto2':
        markup = types.InlineKeyboardMarkup(row_width=2)
        item_my_photo1 = types.InlineKeyboardButton(text='Отправить в ответ', callback_data='itemmyphoto1')
        item_my_photo2 = types.InlineKeyboardButton(text='Далее', callback_data='itemmyphoto2')
        item_my_photo3 = types.InlineKeyboardButton(text='Назад', callback_data='itemmyphoto2')
        markup.add(item_my_photo3, item_my_photo2, item_my_photo1)
        await bot.edit_message_text(chat_id=callback.message.chat.id, message_id=callback.message.id,text=f'📸 Пользователь {callback.message.from_user.first_name} отправил вам 15 фотографий и 5 видео:\n\nЧто бы их увидеть отправьте ему в ответ любую фотографию ил с его участием\n\nОтправте их по его ссылке или нажмите на кнопку"Отправить в ответ"',reply_markup=markup)
    elif callback.data == 'itemmyphoto3':
        markup = types.InlineKeyboardMarkup(row_width=2)
        item_my_photo1 = types.InlineKeyboardButton(text='Отправить в ответ', callback_data='itemmyphoto1')
        item_my_photo2 = types.InlineKeyboardButton(text='Далее', callback_data='itemmyphoto2')
        item_my_photo3 = types.InlineKeyboardButton(text='Назад', callback_data='itemmyphoto2')
        markup.add(item_my_photo3, item_my_photo2, item_my_photo1)
        await bot.edit_message_text(chat_id=callback.message.chat.id, message_id=callback.message.id,text=f'📸 Пользователь {callback.message.from_user.first_name} отправил вам 10 фотографий и 2 видео:\n\nЧто бы их увидеть отправьте ему в ответ любую фотографию ил с его участием\n\nОтправте их по его ссылке или нажмите на кнопку"Отправить в ответ"',reply_markup=markup)
    elif callback.data == 'share1':
        markup = types.InlineKeyboardMarkup()
        item_next = types.InlineKeyboardButton(text='Начать', callback_data='item_next1')
        markup.add(item_next)
        image = open('images/inst4.png', 'rb')
        await bot.send_photo(callback.message.chat.id, image,caption='Чтобы выложить историю в инстаграм как показано выше , сделайте 3 простых шага:',reply_markup=markup)
    elif callback.data == 'share2':
        await bot.send_message(callback.message.chat.id, '')
    elif callback.data == 'share3':
        await bot.send_message(callback.message.chat.id, f'https://t.me/{bot_name}?start={ref_id}')
    elif callback.data == 'item_next1':
        media = open("images/instphoto.png", "rb")
        markup = types.InlineKeyboardMarkup()
        item_back = types.InlineKeyboardButton(text='Назад', callback_data='item_back2')
        item_next = types.InlineKeyboardButton(text='Далее', callback_data='item_next2')
        markup.add(item_back, item_next)
        await bot.edit_message_media(chat_id=callback.message.chat.id, message_id=callback.message.message_id,media=types.InputMediaPhoto(media,caption="1️⃣Скачайте изображение которое мы отправили:"),reply_markup=markup)
    elif callback.data == 'item_back2':
        markup = types.InlineKeyboardMarkup()
        item_next = types.InlineKeyboardButton(text='Начать', callback_data='item_next1')
        markup.add(item_next)
        media = open('images/inst4.png', 'rb')
        await bot.edit_message_media(chat_id=callback.message.chat.id, message_id=callback.message.message_id,media=types.InputMediaPhoto(media,caption='Чтобы выложить историю в инстаграм как показано выше, сделайте 3 простых шага:'),reply_markup=markup)
    elif callback.data == 'item_next2':
        media = open('images/inst2.png', 'rb')
        markup = types.InlineKeyboardMarkup()
        item_back = types.InlineKeyboardButton(text='Назад', callback_data='item_back3')
        item_next = types.InlineKeyboardButton(text='Далее', callback_data='item_next3')
        markup.add(item_back, item_next)
        await bot.edit_message_media(chat_id=callback.message.chat.id, message_id=callback.message.message_id,media=types.InputMediaPhoto(media,caption='2️⃣Загрузите изображение в инстаграм сторис и добавьте стикер:'),reply_markup=markup)
    elif callback.data == 'item_back3':
        markup = types.InlineKeyboardMarkup()
        item_back = types.InlineKeyboardButton(text='Назад', callback_data='item_back2')
        item_next = types.InlineKeyboardButton(text='Далее', callback_data='item_next2')
        markup.add(item_back, item_next)
        media = open('images/instphoto.png', 'rb')
        await bot.edit_message_media(chat_id=callback.message.chat.id, message_id=callback.message.message_id,media=types.InputMediaPhoto(media,caption='️1️⃣Скачайте изображение которое мы отправили:'),reply_markup=markup)
    elif callback.data == 'item_next3':
        media = open('images/inst3.png', 'rb')
        markup = types.InlineKeyboardMarkup()
        item_back = types.InlineKeyboardButton(text='Назад', callback_data='item_back4')
        item_next = types.InlineKeyboardButton(text='Далее', callback_data='item_share4')
        markup.add(item_back, item_next)
        await bot.edit_message_media(chat_id=callback.message.chat.id, message_id=callback.message.message_id,media=types.InputMediaPhoto(media,caption=f"3️⃣В поле URL введите свою уникальную ссылку:⤵️\n\nhttps://t.me/{bot_name}?start={ref_id}"),reply_markup=markup)
    elif callback.data == 'item_back4':
        markup = types.InlineKeyboardMarkup()
        item_back = types.InlineKeyboardButton(text='Назад', callback_data='item_back3')
        item_next = types.InlineKeyboardButton(text='Далее', callback_data='item_next3')
        markup.add(item_back, item_next)
        media = open('images/inst2.png', 'rb')
        await bot.edit_message_media(chat_id=callback.message.chat.id, message_id=callback.message.message_id,media=types.InputMediaPhoto(media,caption='️2️⃣Загрузите изображение в инстаграм сторис:'),reply_markup=markup)
    elif callback.data == 'item_share4':
        media = open('images/inst4.png', 'rb')
        markup = types.InlineKeyboardMarkup()
        item_back = types.InlineKeyboardButton(text='Назад', callback_data='item_back5')
        markup.add(item_back)
        await bot.edit_message_media(chat_id=callback.message.chat.id, message_id=callback.message.message_id,media=types.InputMediaPhoto(media,caption="🎉Поздравляем! Вы поделились ссылкой с друзьями, теперь осталось подождать пока кто-то отправит какие-то фотографии по вашей ссылке :)"),reply_markup=markup)
    elif callback.data == 'item_back5':
        markup = types.InlineKeyboardMarkup()
        item_back = types.InlineKeyboardButton(text='Назад', callback_data='item_back4')
        item_next = types.InlineKeyboardButton(text='Далее', callback_data='item_share4')
        markup.add(item_back, item_next)
        media = open('images/inst3.png', 'rb')
        await bot.edit_message_media(chat_id=callback.message.chat.id, message_id=callback.message.message_id,media=types.InputMediaPhoto(media,caption=f"3️⃣Добавьте стикер с уникальной ссылкой:⤵️\n\nhttps://t.me/{bot_name}?start={ref_id}"),reply_markup=markup)
        await bot.edit_message_caption(chat_id=callback.message.chat.id, message_id=callback.message.message_id,caption=f"3️⃣Добавьте стикер с уникальной ссылкой:⤵️\n\nhttps://t.me/{bot_name}?start={ref_id}",reply_markup=markup)
    elif callback.data == 'item_admin1':
        cursor = connect.cursor()
        cursor.execute("select count(*) from users")
        result = cursor.fetchone()
        print(result)
        await bot.send_message(callback.message.chat.id, f'👤 Общее колличество пользователей: {result[0]}')
    elif callback.data == 'item_admin2':
        img = open('images/admin.jpg', 'rb')
        await bot.send_photo(callback.message.chat.id, img)

async def error_command(chat_id):
    return await bot.send_message(chat_id, '<b>⛔ Произошла ошибка, данная команда недоступна!</b>', parse_mode='html')

async def start_with_ref_link(chat_id, ref_id):
    markup = types.InlineKeyboardMarkup()
    markup.add(types.InlineKeyboardButton(text='❌ Отмена', callback_data='cancel_send_photo'))
    User = get_user(ref_id)
    if User is not None:
        await bot.send_message(chat_id,f'<b>Приветствуем тебя дорогой друг!👋</b>\nС помощью нашего бота ты можешь со всех своих друзей собрать совместные фото с тобой и вспомнить забытые и смешные моменты!\n\n<b>Ты перешёл по ссылке {User[2]} отправь сюда в чат ваши совместные фото, мы их перешлём к {User[2]}, но чтобы он что-то увидел, ему нужно будет обязательно чем-то поделиться с тобой в ответ 🙂</b>',parse_mode='html', reply_markup=markup)

async def only_photo(User):
    await bot.send_message(User[1], "⚠️ <b>Закончите отправку изображений или нажмите «❌Отмена»</b>", parse_mode='html')
    await start_with_ref_link(User[1], User[3])

async def send_menu_message(chat_id, message):
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
    start_button1 = types.KeyboardButton('🌁 Моя галерея')
    start_button2 = types.KeyboardButton('📨 Обратная связь')
    start_button3 = types.KeyboardButton('📸 Собрать фото и видео с друзей')
    start_button4 = types.KeyboardButton('📕 О нас')
    markup.add(start_button1, start_button3, start_button2, start_button4)

    await bot.send_message(chat_id, message, parse_mode='html', reply_markup=markup)


asyncio.run(bot.polling(none_stop=True))