import logging
from telegram import ReplyKeyboardMarkup, ReplyKeyboardRemove
from telegram.ext import CommandHandler, MessageHandler, filters, ConversationHandler
from telegram.ext import CallbackQueryHandler, ContextTypes, Application
from datetime import datetime, timedelta
import json
import random


logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO
)

logger = logging.getLogger(__name__)


def get_reminder(user):
    with open("reminder.json") as file:
        content = json.load(file)
        element = content["reminder"][user]["reminder"][0]
        name = element["name"]
        date = element["date"]
        _time = element["time"]
        r_id = element["id"]
        return name, date, _time, r_id


def del_reminder(user, r_id=None, current=False):
    with open("reminder.json", "r+") as file:
        content = json.load(file)
        reminder = content["reminder"][user]["reminder"]
        if not current:
            for i in range(len(reminder)):
                if reminder[i]["id"] == r_id:
                    del reminder[i]
                    break
        else:
            del reminder[0]
        file.seek(0)
        json.dump(content, file)
        file.truncate()
        
        
def edit_notes(user, key, value):
    user = str(user)
    with open("reminder.json", "r+") as file:
        content = json.load(file)
        if user not in content["reminder"].keys():
            content["reminder"][user] = {"reminder": []}
        if key == "name":
            content["reminder"][user]["reminder"].insert(0, {})
        content["reminder"][user]["reminder"][0][key] = value
        file.seek(0)
        json.dump(content, file)
        file.truncate()


async def list_reminder(update, context: ContextTypes.DEFAULT_TYPE):
    reply_keyboard = [["/start", "/list"]]
    username = str(update.message["chat"]["id"])
    with open("reminder.json") as file:
        content = json.load(file)
        reminder = content["reminder"][username]["reminder"]
        if len(reminder) == 0:
            await update.message.reply_text(f"*Список напоминаний*\n\nНет напоминаний!",
                                            reply_markup=ReplyKeyboardMarkup(reply_keyboard, one_time_keyboard=True, resize_keyboard=True),
                                            parse_mode="markdown")
        else:
            await update.message.reply_text("*Список напоминаний*", parse_mode="markdown")
            for i, v in enumerate(reminder):
                name = v["name"]
                date = v["date"]
                _time = v["time"]
                if "opt_inf" in v.keys():
                    information = v["opt_inf"]
                    if i == len(reminder) - 1:
                        await update.message.reply_text(f"{i + 1}:   Имя: {name}\n      Дата: {date}\n      Время: {_time}\n      Информация: {information}",
                                                        reply_markup=ReplyKeyboardMarkup(reply_keyboard, one_time_keyboard=True, resize_keyboard=True))
                    else:
                        await update.message.reply_text(f"{i + 1}:  Имя: {name}\n      Дата: {date}\n      Время: {_time}\n      Информация: {information}")
                else:
                    if i == len(reminder) - 1:
                        await update.message.reply_text(f"{i + 1}:   Имя: {name}\n      Дата: {date}\n      Время: {_time}",
                                                        reply_markup=ReplyKeyboardMarkup(reply_keyboard, one_time_keyboard=True, resize_keyboard=True))
                    else:
                        await update.message.reply_text(f"{i + 1}:   Имя: {name}\n      Дата: {date}\n      Время: {_time}")


async def notification(context: ContextTypes.DEFAULT_TYPE):
    job = context.job
    if len(job.data) == 6:
         name, date, time, username, r_id = job.data[1], job.data[2], job.data[3], job.data[4], job.data[5]
         await context.bot.send_message(job.data[0], text=f"*Напоминание*\n\nИмя: {name}\nНазначено к {date} - {time}.", parse_mode="markdown")
    else:
        name, date, time, username, r_id, information = job.data[1], job.data[2], job.data[3], job.data[4], job.data[5], job.data[6]
        await context.bot.send_message(job.data[0], text=f"*Напоминание*\n\nИмя: {name}\nИнформация: {information}\n\nНазначено к {date} - {time}.",
                                       parse_mode="markdown")
    del_reminder(username, r_id=r_id)


async def start(update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("*Настройка напоминания*\n\nВведите имя напоминания", parse_mode="markdown")
    return 1


async def askname(update, context: ContextTypes.DEFAULT_TYPE):
    name = update.message.text
    if name == "/cancel":
        cancel(update, context)
        return ConversationHandler.END
    username = update.message["chat"]["id"]
    edit_notes(username, "name", name)
    logger.info("Name: %s", update.message.text)
    await update.message.reply_text(f"*Настройка напоминания*\n\nВ какой день вы хотите получить напоминание о *{name}*?", parse_mode="markdown")
    await update.message.reply_text(f"Введите дату в формате день/месяц/год")
    return 2


async def askdate(update, context: ContextTypes.DEFAULT_TYPE):
     date = datetime.strptime(update.message.text.strip(), "%d/%m/%Y")
     edit_notes(update.message["chat"]["id"], "date", date.strftime("%d/%m/%Y"))
     await update.message.reply_text("Вы выбрали %s" % (date.strftime("%d/%m/%Y")))
     await update.message.reply_text("*Настройка напоминания*\n\nВ какое время вы хотите получить напоминание?", parse_mode="markdown")
     await update.message.reply_text(f"Введите время в формате час:минута")
     return 3


async def asktime(update, context: ContextTypes.DEFAULT_TYPE):
    _time = list(map(int, update.message.text.strip().split(':')))
    chat_id = update.message["chat"]["id"]
    r_id = random.randint(0, 100000)
    format_time = f"{_time[0]}:{_time[1]}"
    edit_notes(chat_id, "time", format_time)
    edit_notes(chat_id, "id", r_id)

    await update.message.reply_text(f"Вы выбрали {format_time}")
    reply_keyboard = [["Да", "Нет"]]
    await context.bot.send_message(chat_id, text=f"*Настройка напоминания*\n\nВы желаете добавить информацию о напоминании",
                                   reply_markup=ReplyKeyboardMarkup(reply_keyboard, one_time_keyboard=True, resize_keyboard=True), parse_mode="markdown")
    return 4


async def info(update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text
    if text == "Да":
        await update.message.reply_text(f"*Настройка напоминания*\n\nОтправьте информацию о напоминии", parse_mode="markdown")
        return 5
    else:
        reply_keyboard = [["/start", "/list"]]
        chat_id = str(update.message["chat"]["id"])
        name, date, format_time, r_id = get_reminder(chat_id)
        hour, minute = int(format_time.split(":")[0]), int(format_time.split(":")[1])

        seconds = datetime.timestamp(datetime.strptime(date, "%d/%m/%Y") + timedelta(hours=hour, minutes=minute)) - (datetime.timestamp(datetime.now()))
        print(seconds)
        if seconds < 0:
            await context.bot.send_message(chat_id=chat_id, text=f"*Настройка напоминания*\n\nВы попытались установить напоминание на прошедшую дату.\nВыберите корректную дату и время.",
                                           parse_mode="markdown", reply_markup=ReplyKeyboardMarkup(reply_keyboard, one_time_keyboard=True, resize_keyboard=True))
            del_reminder(chat_id, r_id=r_id)
        else:
            await context.bot.send_message(chat_id=chat_id,
                                           text=f"*Напоминание сохранено*\n\nИмя: {name}\nДата: {date}\nВремя: {hour}:{minute}",
                                           parse_mode="markdown",
                                           reply_markup=ReplyKeyboardMarkup(reply_keyboard, one_time_keyboard=True,
                                                                            resize_keyboard=True))
            context.job_queue.run_once(notification, seconds, data=[chat_id, name, date, format_time, chat_id, r_id], name=chat_id)
        return ConversationHandler.END


async def opt_info(update, context: ContextTypes.DEFAULT_TYPE):
    reply_keyboard = [["/start", "/list"]]
    information = update.message.text
    chat_id = str(update.message["chat"]["id"])
    edit_notes(chat_id, "opt_inf", information)
    name, date, format_time, r_id = get_reminder(chat_id)
    hour, minute = int(format_time.split(":")[0]), int(format_time.split(":")[1])

    seconds = datetime.timestamp(datetime.strptime(date, "%d/%m/%Y") + timedelta(hours=hour, minutes=minute)) - (datetime.timestamp(datetime.now()))
    print(seconds)
    if seconds < 0:
        await context.bot.send_message(chat_id=chat_id, text=f"*Ошибка*\n\nДата, на которую вы попытались поставить напоминание уже прошла",
                                       parse_mode="markdown", reply_markup=ReplyKeyboardMarkup(reply_keyboard, one_time_keyboard=True, resize_keyboard=True))
        del_reminder(chat_id, r_id=r_id)
    else:
        await context.bot.send_message(chat_id=chat_id,
                                 text=f"*Напоминание сохранено*\n\nИмя: {name}\nДата: {date}\nВремя: {hour}:{minute}",
                                 parse_mode="markdown",
                                 reply_markup=ReplyKeyboardMarkup(reply_keyboard, one_time_keyboard=True,
                                                                  resize_keyboard=True))
        context.job_queue.run_once(notification, seconds, data=[chat_id, name, date, format_time, chat_id, r_id, information], name=chat_id)
    return ConversationHandler.END


async def cancel(update, context: ContextTypes.DEFAULT_TYPE):
    username = str(update.message["chat"]["id"])
    logger.info("Пользователь %s отменил настройку напоминания.", username)
    del_reminder(username, current=True)
    await update.message.reply_text('*Настройка напоминания*'
                              '\n\nОтмена', reply_markup=ReplyKeyboardRemove(), parse_mode="markdown")
    return ConversationHandler.END


def main():
    application = Application.builder().token('5828963184:AAGl70_XCrVJtHb1Lhxdx6n875vgro-nkag').build()

    list_reminder_handler = CommandHandler("list", list_reminder)

    conv_handler = ConversationHandler(
        entry_points=[CommandHandler('start', start)],
        states={
            1: [MessageHandler(filters.TEXT, askname)],
            2: [MessageHandler(filters.TEXT, askdate)],
            3: [MessageHandler(filters.TEXT, asktime)],
            4: [MessageHandler(filters.TEXT, info)],
            5: [MessageHandler(filters.TEXT, opt_info)],
        },
        fallbacks=[CommandHandler('cancel', cancel)],
    )

    application.add_handler(list_reminder_handler)

    application.add_handler(conv_handler)

    application.run_polling()


if __name__ == '__main__':
    main()
