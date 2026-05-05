import database_records as db


def add_request(name, phone, email, business_type, comment, client_ip):
    return db.Request.add.add_request(name, phone, email, business_type, comment, client_ip)


def view_requests():
    return db.Request.select.request_list()


def view_request(id:""):
    return db.Request.select.by_id(id)

def edit_status(id,status):
    return db.Request.edit.edit_status(id,status)