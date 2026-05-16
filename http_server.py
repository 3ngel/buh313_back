# import socket
from http.cookies import SimpleCookie
import uuid

import config as cfg
from http.server import HTTPServer, BaseHTTPRequestHandler, ThreadingHTTPServer
from http import cookies
import json
import database_records as db
import server as srv
from urllib.parse import urlparse, parse_qs
import re
import hashlib
import module_service as service
import module_user as user
import module_request as req
import log

module_name = "http_server"

email_validate = r"^\S+@\S+\.\S+$"
phone_validate = r"^((8|\+7)[\- ]?)?(\(?\d{3}\)?[\- ]?)?[\d\- ]{7}$"

# Глобальное хранилище сессий
sessions = {

}


class RoutingHandler(BaseHTTPRequestHandler):
    routes = {}

    def set_handler(self):
        self.send_response(200)
        self.send_header('Content-type', 'application/json')
        self.send_header('Access-Control-Allow-Origin', '*')
        self.end_headers()

    def set_403_handler(self):
        self.send_response(403)
        self.send_header('Content-type', 'text/html')
        self.end_headers()
        self.wfile.write("Отказано в правах доступа")

    def set_404_handler(self):
        self.send_response(404)
        self.send_header('Content-type', 'text/html')
        self.end_headers()
        self.wfile.write("Страница не найдена")

    def set_handler_with_cookies(self, email, session_id):
        print("Возвращаем куки")
        print(f"""Email: {email}, Session: {session_id}""")
        self.send_response(200)
        self.send_header('Content-type', 'application/json')
        self.send_header('Access-Control-Allow-Origin', '*')
        cookie = SimpleCookie()
        cookie["authorization"] = 'True'
        # cookies['authorization']['secure'] = True
        cookie['authorization']['max-age'] = 1800  # 30 минут
        cookie["email"] = email
        cookie['session_id'] = session_id
        # self.send_header('Set-Cookie', cookie.output(header=''))
        for morsel in cookie.values():
            self.send_header("Set-Cookie", morsel.OutputString())
            # self.send_header('Set-Cookie', cookie.output(header=''))
        self.end_headers()

    @classmethod
    def route(cls, path):
        def decorator(func):
            cls.routes[path] = func
            return func

        return decorator

    # Обработка GET-запросов
    def do_GET(self):
        parsed_url = urlparse(self.path)
        path = parsed_url.path
        query_params = parse_qs(parsed_url.query)
        handler = self.routes.get(path)
        client_ip = self.client_address
        # Перебираем заголовки
        # Заголовки, которым нужны куки
        req = ["/authorization/requests", "/authorization/check_roles", "/authorization/users"]
        if not handler:
            self.set_404_handler()
        elif path in req:
            # Получение кук:
            cookie = SimpleCookie(self.headers.get('Cookie', ''))
            if 'session_id' not in cookie:
                self.set_403_handler()
            else:
                session_id = cookie['session_id'].value
                email = cookie['email'].value
                self.set_handler_with_cookies(email=email, session_id=session_id)
                dic = handler(handler, query_params, email)
                self.wfile.write(json.dumps({'result': dic}).encode('utf-8'))
        else:
            self.set_handler()
            dic = handler(handler, query_params)
            self.wfile.write(json.dumps({'result': dic}).encode('utf-8'))

    # Обработка POST-запросов
    def do_POST(self):
        parsed_url = urlparse(self.path)
        path = parsed_url.path
        # query_params = parse_qs(parsed_url.query)
        handler = self.routes.get(path)
        content_length = int(self.headers.get('Content-Length', 0))
        post_data = self.rfile.read(content_length)  # Returns bytes
        post_body = post_data.decode('utf-8')
        json_data = json.loads(post_body)
        client_ip = self.client_address
        req = ['/add_request', '/authorization']
        # Запрос не найден
        if not handler:
            self.set_404_handler()
        # Запросы, которым не нужны персанолизированные куки
        elif path in req:
            self.set_handler()
            dic = handler(handler, json_data, client_ip)
            self.wfile.write(json.dumps({'result': dic}).encode('utf-8'))
        # Запрос, в котором впервые устанавливаются куки
        elif path == '/check_code':
            dic = handler(handler, json_data, client_ip)
            print(dic)
            # Если код не проверен, то куки не устанавливаем
            if dic != "Success":
                print("Error нашли")
                self.set_handler()
            # Код проверен, куки устанавливаем
            else:
                print("Error не нашли")
                session_id = str(uuid.uuid4())
                email = json_data.get('email')
                self.set_handler_with_cookies(email=email, session_id=session_id)
            self.wfile.write(json.dumps({'result': dic}).encode('utf-8'))
        else:
            cookie = SimpleCookie(self.headers.get('Cookie', ''))
            if 'session_id' not in cookie:
                self.set_403_handler()
            else:
                session_id = cookie['session_id'].value
                email_sender = cookie['email'].value
                self.set_handler_with_cookies(email=email_sender, session_id=session_id)
                dic = handler(handler, json_data, email_sender)
                self.wfile.write(json.dumps({'result': dic}).encode('utf-8'))


@RoutingHandler.route('/authorization')
def authorization(handler, json_data, email_sender):
    email = json_data.get('email')
    password = json_data.get('password')
    password_bytes = password.encode("utf-8")
    password_hash = hashlib.sha256(password_bytes).hexdigest()
    if re.match(email_validate, email) is None:
        return {"error": "Неверно указан email"}
    if db.Authorization.check_login(email, password_hash):
        srv.EmailOTP.send_code(email)
        return "Success"
    else:
        return {"error": "Ошибка аутентификации"}


@RoutingHandler.route('/check_code')
def check_code(handler, json_data, email_sender):
    email = json_data.get('email')
    code = json_data.get('code')
    if re.match(email_validate, email) is None:
        return {"error": "Неверно указан email"}
    if srv.EmailOTP.check_code(email, code, None, None):
        return "Success"
    else:
        return {"error": "Неверный код"}


def get_roles(email):
    return user.Access.get_roles_by_email(email)


@RoutingHandler.route('/authorization/check_roles')
def check_roles(handler, query_params, email_sender):
    roles = get_roles(email_sender)
    return {"roles": roles}


@RoutingHandler.route('/authorization/users')
def view_all_users(handler, query_params, email_sender:str):
    print(email_sender)
    if "users" not in get_roles(email_sender):
        return {"error": "Ошибка прав доступа"}
    user_list = user.users_list()
    new_user_list = []
    for email, firstname, lastname in user_list:
        new_user_list.append({
            "username": f"{lastname} {firstname}",
            "email": email,
            "roles": get_roles(email)
        })
    return new_user_list


@RoutingHandler.route('/authorization/users/view')
def view_user(handler, json_data, email_sender):
    if "users" not in get_roles(email_sender):
        return {"error": "Ошибка прав доступа"}
    user_list = user.users_list()
    user_email = json_data.get('email')
    for email, firstname, lastname in user_list:
        if email == user_email:
            return {
                "username": f"{lastname} {firstname}",
                "email": email,
                "roles": get_roles(email)
            }


@RoutingHandler.route('/authorization/users/add')
def add_user(handler, json_data, email_sender):
    if "users" not in get_roles(email_sender):
        return {"error": "Ошибка прав доступа"}
    email = json_data.get('email')
    firstname = json_data.get('firstname')
    lastname = json_data.get('lastname')
    roles = json_data.get('roles')
    if re.match(email_validate, email) is None:
        return {"error": "Неверно указан email"}
    if user.add_user(email, firstname, lastname, roles):
        return "Success"
    else:
        return {"error": "Ошибка при добавлении пользователя"}


@RoutingHandler.route('/authorization/users/delete')
def delete_user(handler, json_data, email_sender):
    if "users" not in get_roles(email_sender):
        return {"error": "Ошибка прав доступа"}
    email = json_data.get('email')
    if re.match(email_validate, email) is None:
        return {"error": "Неверно указан email"}
    if user.delete_user(email):
        return "Success"
    else:
        return {"error": "Ошибка при удалении пользователя"}


@RoutingHandler.route('/authorization/users/edit')
def edit_user(handler, json_data, email_sender):
    if "users" not in get_roles(email_sender):
        return {"error": "Ошибка прав доступа"}
    email = json_data.get('email')
    new_email = json_data.get('email')
    firstname = json_data.get('firstname')
    lastname = json_data.get('lastname')
    new_roles = json_data.get('roles')
    old_roles = get_roles(email)

    # Если почта не изменилась, оставляем как было
    if new_email == "": new_email = email
    print(new_email)
    #Пользователь не может редактировать о самом себе информацию
    if email == email_sender:
        return {"error": "Ошибка прав доступа"}
    if re.match(email_validate, email) is None or re.match(email_validate, new_email) is None:
        return {"error": "Неверно указан email"}

    #Если список ролей не изменился, то не будем делать лишние запросы в БД
    if new_roles == old_roles:
        new_roles = []
    # Удлаяем все роли по старой почте
    if not user.delete_all_roles(email):
        return {"error": "Ошибка при изменении пользователя"}
    # Редактируем пользователя
    if user.edit_user(email, new_email, firstname, lastname, new_roles):
        return "Success"
    else:
        return {"error": "Ошибка при изменении пользователя"}


@RoutingHandler.route('/all_services')
def all_services(handler, query_params):
    list = db.Services.select.servises_list()
    response = []
    for name, price in list:
        response.append({
            "name": name,
            "price": price
        })
    return response


@RoutingHandler.route('/authorization/service/delete')
def delete_services(handler, json_data, email_sender):
    name = json_data.get('name')
    if "services" not in get_roles(email_sender):
        return {"error": "Ошибка прав доступа"}
    if service.delete_service(name):
        return "Success"
    else:
        return {"error": "Ошибка удаления услуги"}


@RoutingHandler.route('/authorization/service/view')
def view_service(handler, json_data, email_sender):
    if "services" not in get_roles(email_sender):
        return {"error": "Ошибка прав доступа"}
    name = json_data.get('name')
    name, price, types = service.get_service_by_name(name)
    return {
        "name": name,
        "price": price,
        "type": types
    }


@RoutingHandler.route('/authorization/service/add')
def service_add(handler, json_data, email_sender):
    name = json_data.get('name')
    price = json_data.get('price')
    type = json_data.get('type')
    if "services" not in get_roles(email_sender):
        return {"error": "Ошибка прав доступа"}
    if name == "" or name is None:
        return {"error": "Имя услуги не должно быть пустым"}
    try:
        price = int(price)
    except ValueError:
        return {"error": "Цена должна быть целым числом"}
    if service.add_service(name, price, type):
        return "Success"
    else:
        return {"error": "Ошибка при сохранении в базу данных"}


@RoutingHandler.route('/authorization/service/edit')
def service_add(handler, json_data, email_sender):
    # Имя услуги, по которой мы дальше будем ориентироваться
    name = json_data.get('name')
    # Оно может быть, а может и нет
    new_name = json_data.get('new_name') or ""
    price = json_data.get('price')
    type = json_data.get('type')
    if "services" not in get_roles(email_sender):
        return {"error": "Ошибка прав доступа"}
    if name == "" or name is None:
        return {"error": "Имя услуги не должно быть пустым"}
    try:
        price = int(price)
    except ValueError:
        return {"error": "Цена должна быть целым числом"}
    if new_name == "":
        new_name = name
    if service.full_edit_service(name, new_name, price, type):
        return "Success"
    else:
        return {"error": "Ошибка при сохранении в базу данных"}


@RoutingHandler.route('/authorization/requests')
def view_requests(handler, query_params, email_sender):
    if "requests" not in get_roles(email_sender):
        return {"error": "Ошибка прав доступа"}
    return {"response": req.view_requests()}


@RoutingHandler.route('/authorization/request/view')
def view_requests(handler, json_data, email_sender):
    id = json_data.get('id')
    if "requests" not in get_roles(email_sender):
        return {"error": "Ошибка прав доступа"}
    id, name, phone, email, business_type, comment, status = req.view_request(id)
    return {
        "id": id,
        "name": name,
        "phone": phone,
        "email": email,
        "business_type": business_type,
        "comment": comment,
        "status": status
    }


@RoutingHandler.route('/authorization/request/edit_status')
def view_requests(handler, json_data, email_sender):
    id = json_data.get('id')
    status = json_data.get('status')
    if "requests" not in get_roles(email_sender):
        return {"error": "Ошибка прав доступа"}
    if req.edit_status(id, status):
        return "Success"
    else:
        return {"error": "Ошибка при сохранении в базу данных"}


@RoutingHandler.route('/add_request')
def add_request(handler, json_data, client_ip):
    name = json_data.get('name')
    phone = json_data.get('phone')
    email = json_data.get('email')
    if re.match(phone_validate, phone) is None:
        return {"error": "Неверно указан номер телефона"}
    if re.match(email_validate, email) is None:
        return {"error": "Неверно указан email"}

    business_type = json_data.get('business_type')
    if business_type not in ["IP", "SE", "UL"]:
        return {"error": "Неверно указан вид бизнеса"}

    comment = json_data.get('comment')
    if comment is None or comment == "":
        return {"error": "Не указан комментарий"}

    # Добавить передачу IP
    if req.add_request(name, phone, email, business_type, comment, client_ip):
        return "Success"
    else:
        return {"error": "Ошибка сохранения в БД"}


webserver = ThreadingHTTPServer((cfg.server_host, cfg.server_port), RoutingHandler)
print(f"Server startning : http://{cfg.server_host}:{cfg.server_port}")

try:
    webserver.serve_forever()
except KeyboardInterrupt:
    # Stop after Ctrl+C
    print("Server work was abort")

webserver.server_close()
print("Server stopped")
