import database_records as db

# Добавление услуги
def add_service(name, price: int, type="buh"):
    return db.Services.add.add_service(name, price, type)


# Редактирование услуги
def edit_services(name, type, new_value):
    return db.Services.edit.edit_service(name, type, new_value)


# удаление услуги
def delete_service(name):
    return db.Services.delete.delete_service(name)


# Список всех услуг
def services_list():
    return db.Services.select.servises_list()


def get_service_by_name(name):
    return db.Services.select.service(name)