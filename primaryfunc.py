import telegram
from telegram import ReplyKeyboardMarkup
from telegram.ext import Updater, CommandHandler, MessageHandler, Filters, ConversationHandler
import logging, re
from conf import *
from readdb import readmov, getmovie
import mysql.connector

connection = True
CHOOSING, TYPING_MOVIE, TYPING_CHOICE, TYPING_REPLY, TYPING_REQUEST, TYPING_GENRE = range(6)
logging.basicConfig(filename='app.log', filemode='a', level=logging.INFO,
                    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')

logger = logging.getLogger(__name__)

reply_keyboard = [[u'فیلم ها🎞', u'سریال ها🎬'],
                  [u'بر اساس ژانر🔫🕵', u'فیلم های اخیر📅'],
                  [u'پر طرفدار ها✅', u'ارسال درخواست📫']]

reply_keyboard_gen = [['⬅️', '🏠'], ['Action', 'Drama', 'Comedy'], ['Thriller', 'Documentary', 'Horror'],
                      ['Adventure', 'Romance', 'Sci-Fi'], ['Sport', 'History', 'Crime']]
markup = ReplyKeyboardMarkup(reply_keyboard, one_time_keyboard=True)

dbot = telegram.Bot(TOKEN)


def facts_to_str(user_data):
    facts = list()

    for key, value in user_data.items():
        facts.append('{} - {}'.format(key, value))

    return "\n".join(facts).join(['\n', '\n'])


def error(update, context):
    """Log Errors caused by Updates."""
    logger.warning('Update "%s" caused error "%s"', update, context.error)


def start(update, context):
    update.message.reply_text(
        "سلام به ربات جستجوی فیلم خوش آمدید یک گزینه را انتخاب کنید",
        reply_markup=markup)

    return CHOOSING


def readinput(context=None):
    custom_keyboard = []
    movs = readmov(connection, context)
    custom_keyboard.clear()
    if movs.__len__() != 0:
        custom_keyboard.append(['⬅️', '🏠'])
        for mov in movs:
            rspns = '#Tag' + str(mov[0]) + '\t'
            rspns += ' ' + mov[2] + '\t'
            # Check if the movie is serial
            if mov[10] is True:
                rspns += 'فصل : ' + str(mov[7]) + '\t'
                rspns += 'قسمت : ' + str(mov[8]) + '\t'

            temp = [rspns]
            custom_keyboard.append(temp)
    return custom_keyboard


# Triggering request input
def request_choice(update, context):
    text = update.message.text
    context.user_data['choice'] = text
    update.message.reply_text(
        'درخواست خود را به ما بدهید.'.format(text.lower()))
    return TYPING_REQUEST


# Handler for request input
def request_received(update, context):
    text = update.message.text
    dbot.send_message(ADMIN_REQUEST, update.effective_chat.username + " " +text)
    update.message.reply_text(
        'درخواست {} شما در دست بررسی قرار خواهد گرفت. \nبا تشکر'.format(text.lower()))
    return CHOOSING


# Handler for search input
def regular_choice(update, context):
    text = update.message.text
    context.user_data['choice'] = text

    if text == 'فیلم های اخیر📅':
        reply_keyboard_in = readinput(context.user_data)
        newmarkup = ReplyKeyboardMarkup(reply_keyboard_in, one_time_keyboard=True)
        update.message.reply_text(
            "۲۰ تا کار آخر ایناست",
            reply_markup=newmarkup)
        return TYPING_REPLY

    if text == 'بر اساس ژانر🔫🕵':
        newmarkup = ReplyKeyboardMarkup(reply_keyboard_gen, one_time_keyboard=True)
        update.message.reply_text(
            "یکی از ژانر ها را انتخاب کنید",
            reply_markup=newmarkup)
        return TYPING_GENRE

    update.message.reply_text(
        'جستجوی {} : '.format(text.lower()))
    return TYPING_REPLY


def genre_received(update, context):
    text = update.message.text

    if text == '⬅️':
        update.message.reply_text(
            "انتخاب دسته بندی",
            reply_markup=markup)
        return CHOOSING
    if text == '🏠':
        update.message.reply_text(
            "فیلم گیگ\n در حال حاضر تازه شروع کردیم لطفا درخواست تون رو بدید میاریم، کانال هم دنبال کنید اونجا هم خبر میدیم\nکانال ما @filmgig\n ارتباط با ادمین @filmgigadmin",
            reply_markup=markup)
        return CHOOSING

    context.user_data[context.user_data['choice']] = text
    reply_keyboard_in = readinput(context.user_data)
    newmarkup = ReplyKeyboardMarkup(reply_keyboard_in, one_time_keyboard=True)
    update.message.reply_text(
        "آخرین کارهای {}".format(text),
        reply_markup=newmarkup)
    return TYPING_REPLY


# Handler for searching archive and making the list of available movies
def received_information(update, context):
    user_data = context.user_data
    pattern = re.compile('^(پر طرفدار ها✅|فیلم های اخیر📅|بر اساس ژانر🔫🕵|سریال ها🎬|فیلم ها🎞)$')
    if pattern.match(update.message.text) is not None:
        return regular_choice(update, context)

    pattern = re.compile('^#Tag[0-9]{0,}')
    if pattern.match(update.message.text) is not None:
        return movie_choice(update, context)

    text = update.message.text
    category = user_data['choice']
    user_data[category] = text

    if text == '⬅️':
        update.message.reply_text(
            "انتخاب دسته بندی",
            reply_markup=markup)
        return CHOOSING
    if text == '🏠':
        update.message.reply_text(
            "فیلم گیگ\n در حال حاضر تازه شروع کردیم لطفا درخواست تون رو بدید میاریم، کانال هم دنبال کنید اونجا هم خبر میدیم\nکانال ما @filmgig\n ارتباط با ادمین @filmgigadmin",
            reply_markup=markup)
        return CHOOSING

    reply_keyboard_in = readinput(user_data)
    if reply_keyboard_in.__len__() is 0:
        user_data[user_data['choice']] = ""
        reply_keyboard_in = readinput(user_data)
        newmarkup = ReplyKeyboardMarkup(reply_keyboard_in, one_time_keyboard=True)
        update.message.reply_text(
            "اثری پیدا نشد! ۲۰ تا کار آخر ایناست",
            reply_markup=newmarkup)
        return TYPING_REPLY

    newmarkup = ReplyKeyboardMarkup(reply_keyboard_in, one_time_keyboard=True)

    update.message.reply_text(
        "یکی از آثار را انتخاب کنید",
        reply_markup=newmarkup)

    return TYPING_MOVIE


# Handler for giving user the desired movie link
def movie_choice(update, context):
    chat_id = update._effective_chat._id_attrs[0]
    text = update.message.text

    if text == '⬅️':
        update.message.reply_text(
            "انتخاب دسته بندی",
            reply_markup=markup)
        return CHOOSING
    if text == '🏠':
        update.message.reply_text(
            "فیلم گیگ\n در حال حاضر تازه شروع کردیم لطفا درخواست تون رو بدید میاریم، کانال هم دنبال کنید اونجا هم خبر میدیم\nکانال ما @filmgig\n ارتباط با ادمین @filmgigadmin",
            reply_markup=markup)
        return CHOOSING

    ID = re.findall("^#Tag[0-9]{0,}", text)[0][4:]
    # if check_user(update):
    link = getmovie(connection, ID)[0]
    dbot.send_photo(chat_id=chat_id, photo=WEB_URL + 'mov/' + str(ID) + '/' + str(ID) + '.jpg',
                    caption="لینک:⛓ \n" + WEB_URL + 'mov/' + str(ID) +
                            '\n' + ' نام فیلم🎥' + str(link[0]) + '\n' +
                            '\n' + ' ژانر🔫🕵' + str(link[1]) + '\n' +
                            '\n' + ' امتیاز⭐️' + str(link[3]) + '\n' +
                            '\n' + ' آدرس کانال ما 🙋‍♂' + CHANNEL + '\n'
                    )
    return CHOOSING
    # else:
    #     update.message.reply_text(
    #         "برای دانلود باید در کانال م ا🙋‍♂ عضو باشید. لینک  " + CHANNEL,
    #         reply_markup=markup)
    #     return TYPING_REPLY


# THE END
def done(update, context):
    user_data = context.user_data
    if 'choice' in user_data:
        del user_data['choice']

    update.message.reply_text("I learned these facts about you:"
                              "{}"
                              "Until next time!".format(facts_to_str(user_data)))

    user_data.clear()
    return ConversationHandler.END


def check_user(update):
    temp = dbot.get_chat_member(CHANNEL, update.effective_user.id)
    if temp.status != 'left':
        return True
    else:
        return False


def main():
    updater = Updater(TOKEN, use_context=True)
    dp = updater.dispatcher

    conv_handler = ConversationHandler(
        entry_points=[
            MessageHandler(Filters.regex('^(پر طرفدار ها✅|فیلم های اخیر📅|بر اساس ژانر🔫🕵|سریال ها🎬|فیلم ها🎞)$'),
                           regular_choice),
            MessageHandler(Filters.regex('^(#Tag[0-9]{0,})|(⬅️)$'),
                           movie_choice),
            MessageHandler(Filters.regex('^(ارسال درخواست📫)$'),
                           request_choice),
            MessageHandler(Filters.text,
                           regular_choice)],

        states={
            # Creating the main menu
            CHOOSING: [
                MessageHandler(
                    Filters.regex('^(پر طرفدار ها✅|فیلم های اخیر📅|بر اساس ژانر🔫🕵|سریال ها🎬|فیلم ها🎞)$'),
                    regular_choice),
                MessageHandler(Filters.regex('^(ارسال درخواست📫)$'),
                               request_choice),
                MessageHandler(Filters.regex('^(#Tag[0-9]{0,})|(⬅️)|(🏠)$'),
                               movie_choice)
            ],
            # Choosing the movie from available list
            TYPING_MOVIE: [
                MessageHandler(Filters.regex('^(#Tag[0-9]{0,})|(⬅️)|(🏠)$'),
                               movie_choice)],
            # Creating input ready for writing search text
            TYPING_CHOICE: [MessageHandler(Filters.text,
                                           regular_choice)
                            ],
            # Searching over the input text
            TYPING_REPLY: [MessageHandler(Filters.text,
                                          received_information),
                           ],
            # User request received
            TYPING_REQUEST: [MessageHandler(Filters.text,
                                            request_received)
                             ],
            TYPING_GENRE: [MessageHandler(Filters.text,
                                          genre_received)]

        },

        fallbacks=[CommandHandler('stop', done)]
    )
    dp.add_handler(CommandHandler('start', start))
    dp.add_handler(conv_handler)
    dp.add_error_handler(error)
    updater.start_polling()
    updater.idle()


def db_init():
    global connection
    try:
        connection = mysql.connector.connect(user=USER_MY, password=PASS_MY, host=HOST_MY, database=DB_MY)

        print("You are connected to MySql \n")

    except (Exception, mysql.Error) as error:
        print("Error while connecting to MySql", error)
