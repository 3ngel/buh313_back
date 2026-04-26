import database_records as db
import send_email as Email
import log

module_name = "server_user"

def add_user(email, firstname, lastname):
    # Информация для отправки письма сотруднику после регистрации
    topic = "Регистрация сотрудника БухгалтерИя"
    message = f"""Здравствуйте, {firstname} {lastname}!\n
    Вы были зарегистрированы как сотрудник организации БухгалтерИя. \n
    Для завершения регистрации перейдите в бот https://t.me/buh313_bot"""
    if db.Users.create(email.lower(), firstname, lastname):
        Email.send_email(email.lower(), topic, message)
        return True
    else:
        return False


# Удаление пользователя
def delete_user(email):
    return db.Users.delete(email.lower())


# Получение ФИ и почты пользователя
def users_list(self=""):
    return db.Users.Get.list()


# Проверка доступа пользователей
class Access:
    # Получение списка доступных ролей
    def get_roles_by_id(user_id):
        return db.Users.Get.roles_by_id(user_id)

    def get_roles_by_email(email):
        return db.Users.Get.roles_by_email(email)

    # Проверяет наличие адреса электронной почты
    def check_email(email):
        if db.Users.Get.name_by_email(email.lower()) is None:
            return False
        else:
            return True


# Класс получения чего либо
class Get:
    # Получение статуса пользоваеля по его тг-идентификатору
    def get_user_activated_by_id(user_id):
        if db.Users.Get.by_user_id(user_id) is None:
            return False, False
        else:
            authorized, deleted = db.Users.Get.by_user_id(user_id)
            return authorized, deleted

    # Получение ФИ сотрудника по его почте
    def get_name_by_email(email):
        if db.Users.Get.name_by_email(email.lower()) is None:
            return False, False
        else:
            firstname, lastname = db.Users.Get.name_by_email(email.lower())
            return firstname, lastname


    # def get_user_id_by_email(email):