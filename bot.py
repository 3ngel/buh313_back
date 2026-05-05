import re

import requests
import telebot
from telebot import types
import config as cfg
import server as srv
import log
import module_service as service
import module_user as user

module_name = "tg_bot"

service_add_list = {
    'service_name': '',
    'service_price': ''
}
service_edit = {
    'type': '',
    'name': ''
}

# regex
regex_price = r'^[0-9]{3,}$'

# указываем токен для доступа к боту
bot = telebot.TeleBot(cfg.bot_key)
start_txt = 'Привет! \n\nТеперь можете работать с ботом "БухгалтерИя".'


class Authorization:
    def send_code(message):
        email = message.text
        # Проверяем есть ли пользователь с такой почтой
        if user.Access.check_email(email):
            #Отправляем кодик
            if srv.EmailOTP.send_code(email):
                add = bot.send_message(message.chat.id, "Введите отправленный код доступа")
                bot.register_next_step_handler(add, Authorization.check_code, email)
            else:
                return
        else:
            Messages.send_with_markup(message, "Вы не можете авторизоваться", Menu.zero_button())

    def check_code(message, email):
        code = message.text
        if srv.EmailOTP.check_code(email, code, message.chat.id, message.chat.username):
            log.record("info", f"Авторизовался пользователь почты:{email}, ник: {message.chat.username}", module_name)
            Messages.send_with_markup(message, "Вы успешно прошли авторизацию", Menu.start(message.chat.id))
        else:
            Messages.send_with_markup(message, "Ты лох, попробуй заново", Menu.zero_button())


# Вариации кнопок в боте
class Menu:
    # Пустая форма
    def zero_button(self=""):
        return types.InlineKeyboardMarkup(row_width=2)

    # Набор кнопок для старта
    def start(user_id):
        markup = types.InlineKeyboardMarkup(row_width=2)
        roles = user.Access.get_roles_by_id(user_id)
        services = types.InlineKeyboardButton("Услуги", callback_data='services')
        requests = types.InlineKeyboardButton("Заявки", callback_data='requests')
        users = types.InlineKeyboardButton("Пользователи", callback_data='users')
        if not roles:
            return Menu.zero_button()
        if "services" in roles:
            markup.add(services)
        if "requests" in roles:
            markup.add(requests)
        if "users" in roles:
            markup.add(users)

        return markup

    # Кнопка "Назад", которая ведёт к стартовому меню
    def to_start():
        markup = types.InlineKeyboardMarkup(row_width=2)
        to_start_menu = types.InlineKeyboardButton("\U00002B05 Назад", callback_data='to_start_menu')
        markup.add(to_start_menu)
        return markup

    # Набор кнопок для "Услуги"
    def servises():
        markup = types.InlineKeyboardMarkup(row_width=2)
        services_list = types.InlineKeyboardButton("\U0001F4C3 Список услуг", callback_data='service_list')
        services_add = types.InlineKeyboardButton("\U0000270D Добавить услугу", callback_data='service_add')
        service_edit = types.InlineKeyboardButton("\U0000270F Редактировать услугу", callback_data='service_edit')
        service_delete = types.InlineKeyboardButton("\U0001F5D1 Удалить услугу", callback_data='service_delete')
        to_start_menu = types.InlineKeyboardButton("\U00002B05 Назад", callback_data='to_start_menu')
        markup.add(services_list, services_add, service_edit, service_delete, to_start_menu)
        return markup

    # Кнопка "Назад", которая ведёт к меню Услуг
    def to_service():
        markup = types.InlineKeyboardMarkup(row_width=2)
        to_services = types.InlineKeyboardButton("Назад", callback_data='services')
        markup.add(to_services)
        return markup

    def users():
        markup = types.InlineKeyboardMarkup(row_width=2)
        user_list = types.InlineKeyboardButton("\U0001F4C3 Список пользователей", callback_data='user_list')
        user_add = types.InlineKeyboardButton("\U0000270D Добавить пользователя", callback_data='user_add')
        user_edit = types.InlineKeyboardButton("\U0000270F Редактировать пользователя", callback_data='user_edit')
        user_delete = types.InlineKeyboardButton("\U0001F5D1 Удалить пользователя", callback_data='user_delete')
        to_start_menu = types.InlineKeyboardButton("\U00002B05 Назад", callback_data='to_start_menu')
        markup.add(user_list, user_add, user_edit, user_delete, to_start_menu)
        return markup

    # Кнопка "Назад" до меню Пользователи
    def to_users():
        markup = types.InlineKeyboardMarkup(row_width=2)
        to_users = types.InlineKeyboardButton("Назад", callback_data='users')
        markup.add(to_users)
        return markup

    # Набор кнопок для "Заявки"
    def requests():
        markup = types.InlineKeyboardMarkup(row_width=1)
        request_list = types.InlineKeyboardButton("Список заявок", callback_data='request_list')
        to_start_menu = types.InlineKeyboardButton("\U00002B05 Назад", callback_data='to_start_menu')
        markup.add(request_list, to_start_menu)
        return markup

    def to_requests():
        markup = types.InlineKeyboardMarkup(row_width=2)
        to_request = types.InlineKeyboardButton("Назад", callback_data='requests')
        markup.add(to_request)
        return markup


class Services:
    class add:
        def name(message):
            service_add_list['service_name'] = message.text
            add = bot.send_message(message.chat.id, "Введите стоимость")
            bot.register_next_step_handler(add, Services.add.price)

        def price(message):
            # bot.register_next_step_handler(send_message(message, "Неверный формат цены", zero_button()), service_price)
            price = message.text
            if re.match(regex_price, price):
                service_add_list['service_price'] = message.text
                markup = Menu.zero_button()
                services_buh = types.InlineKeyboardButton("Бухгалтерия", callback_data='buh')
                services_law = types.InlineKeyboardButton("Юриспруденция", callback_data="law")
                markup.add(services_buh, services_law)
                Messages.send_with_markup(message, "Выберите вид услуги", markup)
            else:
                add = bot.send_message(message.chat.id, "Только цифры. Введите стоимость")
                bot.register_next_step_handler(add, Services.add.price)

        def save(name, price, type):
            return service.add_service(name, int(price), type)

    class edit:
        def name(message):
            if message.text == "Отмена":
                Messages.send_with_markup(message, "Список доступных услуг", Menu.servises())
            service_edit['name'] = message.text
            name, price = service.get_service_by_name(message.text)
            if name != "":
                markup = Menu.zero_button()
                service_edit_name = types.InlineKeyboardButton("Название", callback_data="service_edit_name")
                service_edit_price = types.InlineKeyboardButton("Цена", callback_data="service_edit_price")
                markup.add(service_edit_name, service_edit_price)
                Messages.send_with_markup(message, "Выберите что изменить", markup)
            else:
                edit = bot.send_message(message.chat.id,
                                        " Услуга не найдена \n Введите название услуги или напишите \"Отмена\"")
                bot.register_next_step_handler(edit, Services.edit.name)

        def save(message):
            if service.edit_services(service_edit['name'], service_edit['type'], message.text):
                Messages.send_with_markup(message, "\U00002705 Изменнения успешно сохранены", Menu.to_service())
            else:
                Messages.send_with_markup(message, '\U0001F625 Возникли ошибки при сохранении изменений',
                                          Menu.to_service())

    class delete:
        def name(message):
            name_delete = message.text
            if name_delete == "Отмена":
                Messages.send_with_markup(message, "Меню услуги", Menu.servises())
                return
            name, price = service.get_service_by_name(name_delete)
            if name != "":
                delete = bot.send_message(message.chat.id,
                                          f"Вы уверенны, что хотите удалить следующую услугу \"{name}\" (напишите Да)? \n")
                bot.register_next_step_handler(delete, Services.delete.save, message.text)
            else:
                delete = bot.send_message(message.chat.id,
                                          "Услуга не найдена \n Введите название услуги или напишите \"Отмена\"")
                bot.register_next_step_handler(delete, Services.delete.name)

        def save(message, name):
            if message.text == "Да":
                if service.delete_service(name):
                    Messages.send_with_markup(message, "\U00002705 Услуга удалена", Menu.to_service())
                else:
                    Messages.send_with_markup(message, '\U0001F625 Возникли ошибки при удалении', Menu.to_service())
            else:
                Messages.send_with_markup(message, "Выберите вариант", Menu.servises())


class Users:
    class add:
        def firstname(message):
            firstname = message.text
            user_add_first = bot.send_message(message.chat.id,
                                              f"Введите фамилию пользователя")
            bot.register_next_step_handler(user_add_first, Users.add.lastname, firstname)

        def lastname(message, firstname):
            lastname = message.text
            user_add_last = bot.send_message(message.chat.id,
                                             f"Введите почту пользователя")
            bot.register_next_step_handler(user_add_last, Users.add.save, firstname, lastname)

        def save(message, firstname, lastname):
            if user.add_user(message.text, firstname, lastname):
                log.record("info", f"Пользователь {message.chat.username} добавил пользователя {lastname} {firstname}, с почтой {message.text}", module_name)
                Messages.send_with_markup(message, "Пользователь успешно добавлен", Menu.users())
            else:
                Messages.send_with_markup(message, "Пользователь НЕ добавлен", Menu.users())
            return

    # class list:
    #     def save(message):
    #         return
    class edit:
        # Кого редактировать
        def who_edit(message):
            message_text = "Что хотите изменить?" # Можно изменить ФИ
            return

        # Что редактировать
        def what_edit(message):
            return

        # Сохранить изменения
        def save(message):
            # log.record("info", f"Пользователь {message.chat.username} добавил пользователя {lastname} {firstname}, с почтой {message.text}", module_name)
            return

    class delete:
        # Кого удалять
        def who_delete(message):
            email = message.text
            if user.Access.check_email(email):
                ###Сделать доработку, что нелья удалять самого себя
                firstname, lastname = user.Get.get_name_by_email(email)
                text = f"Вы уверенны, что хотите удалить пользователя \n {firstname} {lastname}? \n (Напишите Да)"
                access = bot.send_message(message.chat.id, text)
                bot.register_next_step_handler(access, Users.delete.save, email)
            else:
                text = "Пользователь не найден"
                Messages.send_with_markup(message, text, Menu.to_users())

        def save(message, email):
            text = "Пользователь НЕ удалён"
            if message.text == "Да":
                log.record("info", "Она сказала Да", module_name)
                if user.delete_user(email):
                    text = "Пользователь удалён"

            Messages.send_with_markup(message, text, Menu.to_users())


    class add_role:
        #Выбираем кому добавить роль
        def who(message):
            email = message.text
            # Проверяем, чтоб выбранный пользователь не действующий, чтоб не мог сам себе роль менять
            message_myself = "Вы не можете сами себе добавлять роль"
            # Проверяем, какие роли не заняты
            message_succes = "Выберите роль для добавления"

            # У пользователя уже есть все роли(
            message_error = "Нет доступных ролей для данного пользователя"
            return

        #Какую роль добавить
        def what_role(message, email):
            role = message.text
            #Проверяем, что роль существует
            #Добавляем роль
            success = "Роль успешно добавлена"
            return

    class delete_role:
        def who(message):
            #Проверяем, чтоб выбранный пользователь не действующий, чтоб не мог сам себе роль менять
            email = message.text
            message_myself = "Вы не можете сами себе удалить роль"
            # Проверяем, какие роли есть у пользователя
            message_succes = "Выберите роль для удаления"

            # У пользователя не было ролей
            message_error = "У пользователя нет ролей. Вы можете её добавить"

        def what_role(message, email):
            #Проверяем корректная ли роль
            role = message.text
            #Удаляем роль
            success = "Роль удалена"

            return

class Messages:
    def send_with_markup(message, text, markup):
        bot.send_message(message.chat.id, text, reply_markup=markup)

    def edit_with_markup(message, text, markup):
        bot.edit_message_text(text, message.chat.id, message.message_id,
                              reply_markup=markup)

    def register_next_step(message, text, function_name, **args):
        msg = bot.send_message(message.chat.id, text)
        bot.register_next_step_handler(msg, function_name, args)


# Запуск бота
@bot.message_handler(commands=['start'])
def start(message):
    print("Старт")
    authorized, deleted = user.Get.get_user_activated_by_id(message.chat.id)
    # Пользователя нашли и он авторизован, но не удалён
    if authorized == True and deleted == False:
        Messages.send_with_markup(message, start_txt, Menu.start(message.chat.id))
    # Пользователя не нашли или нашли, но он не авторизован, и не удалён
    elif authorized == deleted == False:
        start = bot.send_message(message.chat.id, "Введите свою электронную почту")
        bot.register_next_step_handler(start, Authorization.send_code)
    # Пользователь помечен, как удалённый
    else:
        Messages.send_with_markup(message, "У вас нет прав для дальнейших действий", Menu.zero_button())


# Обработчик нажатых кнопок
@bot.callback_query_handler(func=lambda call: True)
def check_callback_data(call):
    # Набор списков
    services_methods = ["services", "service_list", "service_add", "buh", "law", "service_edit",
                        "service_edit_name", "service_edit_price", "service_delete"]

    requests_methods = ["requests", "request_list"]

    users_method = ["users", "user_add", "user_list", "user_delete"]

    # Кнопки Услуги:
    if call.data in services_methods:
        if call.data == "services":
            Messages.edit_with_markup(call.message, "Выберите вариант", Menu.servises())
        elif call.data == "service_list":
            list_ = service.services_list()
            message = f"Список \n"
            for name, price in list_:
                message += f"Услуга: {name}, стоимость: {price};\n"
            Messages.edit_with_markup(call.message, message, Menu.to_service())

        elif call.data == "service_add":
            add = bot.send_message(call.message.chat.id, "Введите название услуги")
            bot.register_next_step_handler(add, Services.add.name)

        elif call.data in ("buh", "law"):
            name = service_add_list['service_name']
            price = service_add_list['service_price']
            if Services.add.save(name, price, call.data):
                Messages.send_with_markup(call.message, "\U00002705 Услуга добавлена", Menu.to_service())
            else:
                Messages.send_with_markup(call.message, "\U0001F625 Ошибка добавления услуги", Menu.to_service())

        elif call.data == "service_edit":
            edit = bot.send_message(call.message.chat.id, "Введите название услуги")
            bot.register_next_step_handler(edit, Services.edit.name)

        elif call.data in ("service_edit_name", "service_edit_price"):
            service_edit["type"] = "name" if call.data == "service_edit_name" else "price"
            edit = bot.send_message(call.message.chat.id, "Введите новое значение")
            bot.register_next_step_handler(edit, Services.edit.save)

        elif call.data == "service_delete":
            delete = bot.send_message(call.message.chat.id, "Введите название услуги")
            bot.register_next_step_handler(delete, Services.delete.name)


    # Кнопки с запросами
    elif call.data in requests_methods:
        if call.data == "requests":
            Messages.edit_with_markup(call.message, "Выберите вариант", Menu.requests())
        #Доработать с аналогией с сайтом
        elif call.data == "request_list":
            return
            # Messages.edit_with_markup(call.message, "Список пуст", Menu.to_start())

    # Кнопки Пользователь
    elif call.data in users_method:
        if call.data == "users":
            Messages.edit_with_markup(call.message, "Выберите подходящий вариант", Menu.users())

        elif call.data == "user_add":
            add = bot.send_message(call.message.chat.id, "Введите имя пользователя")
            bot.register_next_step_handler(add, Users.add.firstname)

        elif call.data == "user_list":
            list = user.users_list()
            message = f"Список \n"
            for email, firstname, lastname in list:
                message += f"Пользователь: {firstname} {lastname}, почта {email};\n"
            Messages.edit_with_markup(call.message, message, Menu.to_users())
        elif call.data == "user_delete":
            add = bot.send_message(call.message.chat.id, "Введите электронную почту")
            bot.register_next_step_handler(add, Users.delete.who_delete)

    # Другое
    elif call.data == "to_start_menu":
        Messages.edit_with_markup(call.message, start_txt, Menu.start(call.message.chat.id))
    # Ничего не подошло
    else:
        Messages.edit_with_markup(call.message, "Список пуст", Menu.to_start())


@bot.message_handler(content_types="text")
def comands(message):
    text = message.text


if __name__ == '__main__':
    log.record("info", ">>>>>>>>Запуск бота <<<<<<<<", module_name)
    bot.send_message(cfg.admin_id, "Чтоб не расслаблялся (проверка бота)", parse_mode='Markdown')
    while True:
        # в бесконечном цикле постоянно опрашиваем бота — есть ли новые cообщения
        try:
            bot.polling(none_stop=True, interval=0)
        # если возникла ошибка — сообщаем про исключение и продолжаем работу
        except Exception as e:
            error = f"Ошибка {str(e)}. Попробуйте позже"
            log.record("error", error, module_name)
