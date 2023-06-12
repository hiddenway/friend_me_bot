import telebot
import random
from telebot import types

bot = telebot.TeleBot('6199788488:AAFQt9ndMV1AL5lAuxnA0WZ5v3lUtAtgB9A')

lower = "abcdfghjklmnpqrstvwxz"
upper = "ABCDFGHJKLMNPQRSTVWXZ"
numbers = "0123456789"
string = lower + upper + numbers
lenght = 16
link = "".join(random.sample(string,lenght))
#Меню Старт
@bot.message_handler(commands=['start'])
def start(message):
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True,row_width=2)
    start_button1 = types.KeyboardButton('🖼️ МОИ ФОТО')
    start_button2 = types.KeyboardButton('📨 ОБРАТНАЯ СВЯЗЬ')
    start_button3 = types.KeyboardButton('⛓️ ОТПРАВИТЬ ССЫЛКУ ДРУГУ')
    test_bd =types.InlineKeyboardButton('ТЕСТ MYSQL')
    markup.add(start_button1,start_button2,start_button3,test_bd)
    bot.send_message(message.chat.id,'<b>Приветствуем тебя дорогой друг!👋</b>\nС помощью нашего бота ты можешь со всех своих друзей собрать совместные фото и видео с тобой и вспомнить забытые и смешные моменты!\n\nКак это работает:\n1️⃣Нажмите кнопку в меню "отправить ссылку другу"\n2️⃣Выберите "Поделиться историей Instagram"\n3️⃣﻿﻿Добавьте себе историю в инстаграм как указано инструкции по кнопке\n4️⃣Все фото которые отправят друзья мы будем отображать в разделе "Мои фото"\n\nКак только кто-то из твоих друзей отправит что-то по ссылке мы обязательно тебе об этом скажем😊',parse_mode='html',reply_markup=markup)

@bot.message_handler(content_types=['text'])
def chat_message(message):
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
        bot.send_message(message.chat.id,'testing...')
@bot.callback_query_handler(func=lambda callback:callback.data)
def callback_my_photo(callback):
    if callback.data == 'itemmyphoto1':
        bot.send_message(callback.message.chat.id,'b1')
    elif callback.data == 'itemmyphoto2':
        bot.send_message(callback.message.chat.id, 'b2')
    elif callback.data == 'share1':
        bot.send_message(callback.message.chat.id, '1')
    elif callback.data == 'share2':
        bot.send_message(callback.message.chat.id, '2')
    elif callback.data == 'share3':
        bot.send_message(callback.message.chat.id,f'https://t.me/Friend_Me_bot/{link}ID{callback.message.from_user.id}')



bot.polling(non_stop=True)