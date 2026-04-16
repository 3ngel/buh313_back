# import socket
import config as cfg
import database_records as db
import random
import send_email as Email
import log
import module_service as service
import re

module_name = "server"

# regex
regex_name = r'^[А-Я]{1}[а-я]{2,63}$'
regex_email = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'


# Класс работы с услугами
# class Service:
#
#     # Добавление услуги
#     def add_service(name, price: int, type="buh"):
#         return db.Services.add.add_service(name, price, type)
#
#     # Редактирование услуги
#     def edit_services(name, type, new_value):
#         return db.Services.edit.edit_service(name, type, new_value)
#
#     # удаление услуги
#     def delete_service(name):
#         return db.Services.delete.delete_service(name)
#
#     # Список всех услуг
#     def services_list(self=""):
#         return db.Services.select.servises_list()
#
#     def get_service_by_name(name):
#         return db.Services.select.service(name)


# Класс работы с пользователями
# class User:
#     # Добавление пользователя
#     def add_user(email, firstname, lastname):
#         # Информация для отправки письма сотруднику после регистрации
#         topic = "Регистрация сотрудника БухгалтерИя"
#         message = f"""Здравствуйте, {firstname} {lastname}!\n
#         Вы были зарегистрированы как сотрудник организации БухгалтерИя. \n
#         Для завершения регистрации перейдите в бот https://t.me/buh313_bot"""
#         if db.Users.create(email.lower(), firstname, lastname):
#             Email.send_email(email.lower(), topic, message)
#             return True
#         else:
#             return False
#
#     # Удаление пользователя
#     def delete_user(email):
#         return db.Users.delete(email.lower())
#
#     # Получение ФИ и почты пользователя
#     def users_list(self=""):
#         return db.Users.Get.list()
#
#     # Проверка доступа пользователей
#     class Access:
#         #Получение списка доступных ролей
#         def get_roles_by_id(user_id):
#             return []
#
#         # Проверяем может ли пользователь авторизоваться
#         def check_authoraztion_by_email(email):
#             if db.Users.Get.by_email(email.lower()) is None:
#                 return False, False
#             else:
#                 authorized, deleted = db.Users.Get.by_email(email)
#                 return authorized, deleted
#
#         # Проверяет наличие адреса электронной почты
#         def check_email(email):
#             if db.Users.Get.name_by_email(email.lower()) is None:
#                 return False
#             else:
#                 return True
#
#     # Класс получения чего либо
#     class Get:
#         # Получение статуса пользоваеля по его тг-идентификатору
#         def get_user_activated_by_id(user_id):
#             if db.Users.Get.by_user_id(user_id) is None:
#                 return False, False
#             else:
#                 authorized, deleted = db.Users.Get.by_user_id(user_id)
#                 return authorized, deleted
#
#         # Получение ФИ сотрудника по его почте
#         def get_name_by_email(email):
#             if db.Users.Get.name_by_email(email.lower()) is None:
#                 return False, False
#             else:
#                 firstname, lastname = db.Users.Get.name_by_email(email.lower())
#                 return firstname, lastname
# Возвращает код и сообщение
class Checked:
    def __init__(self):
        pass

    def name(self, name):

        assert len(name) >= 4, "Имя слишком короткое"

        assert len(name) <= 64, "Имя слишком длинное"

        assert re.match(regex_name, name), "Некорректные символы в имени"

        return True

    def email(self, email):

        assert re.match(regex_email, email), "Некорректные символы в адресе электронной почты"

        return True


class EmailOTP:
    # Отправка одноразового года на почту
    def send_code(email):
        code = random.randint(100000, 999999)
        if db.Authorization.save_code(email.lower(), code):
            Email.send_email(email.lower(), "Код проверки", f"Ваш код проверки: {code}. \n Никому не сообщайте его")
            return True
        else:
            return False

    # Проверка одноразового кода
    def check_code(email, code, user_id, username):
        sended_code = db.Authorization.get_code(email.lower())
        if sended_code == code:
            # Удаление всех кодов в БД
            db.Authorization.delete_code(email.lower())
            # Авторизация в тг боте
            if user_id and username:
                # Активация пользователя, сохранение информации о тг
                db.Users.activated_user(email.lower(), user_id, username)
            return True
        else:
            return False
