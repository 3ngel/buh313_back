# import socket
import http.cookies

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
import log

module_name = "http_server"

email_validate = r"^\S+@\S+\.\S+$"


class RoutingHandler(BaseHTTPRequestHandler):
    routes = {}

    def set_handler(self):
        self.send_response(200)
        self.send_header('Content-type', 'application/json')
        self.send_header('Access-Control-Allow-Origin', '*')
        self.end_headers()

    # def set_cookies(self):
    #     cookies = http.cookies.SimpleCookie()
    #     cookies["authorization"] = 'True'
    #     cookies['authorization']['secure'] = True
    #     cookies['authorization']['max-age'] = 1800  # 30 минут
    #     for morsel in cookies.values():
    #         self.send_header("Set-Cookie", morsel.OutputString())
    #     self.end_headers()

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
        if not handler:
            self.send_response(404)
            self.send_header('Content-type', 'text/html')
            self.end_headers()
            self.wfile.write("Страница не найдена")
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
        if not handler:
            self.send_response(404)
            self.send_header('Content-type', 'text/html')
            self.end_headers()
            self.wfile.write("Страница не найдена")
        else:
            self.set_handler()
            dic = handler(handler, json_data)
            self.wfile.write(json.dumps({'result': dic}).encode('utf-8'))


@RoutingHandler.route('/authorization')
def authorization(handler, json_data):
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
def check_code(handler, json_data):
    email = json_data.get('email')
    code = json_data.get('code')
    if re.match(email_validate, email) is None:
        return {"error": "Неверно указан email"}
    if srv.EmailOTP.check_code(email, code, None, None):
        return "Success"
    else:
        return {"error": "Неверный код"}


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

@RoutingHandler.route('/services/delete')
def delete_services(handler, json_data):
    name = json_data.get('name')
    if service.delete_service(name):
        return "Success"
    else:
        return {"error": "Ошибка удаления услуги"}

@RoutingHandler.route('/services/view')
def view_service(handler, json_data):
    name = json_data.get('name')
    list = db.Services.select.full_service(name)
    response = {}
    for name, price, type in list:
        response = {
            "name": name,
            "price": price,
            "type": type
        }
        break
    return response


@RoutingHandler.route('/add_request')
def add_request(handler, json_data):
    name = json_data.get('name')
    phone = json_data.get('phone')
    email = json_data.get('email')
    if re.match(email_validate, email) is None:
        return {"error": "Неверно указан email"}

    business_type = json_data.get('business_type')
    if business_type not in ["IP", "SE", "UL"]:
        return {"error": "Неверно указан вид бизнеса"}

    comment = json_data.get('comment')
    if comment is None or comment == "":
        return {"error": "Не указан комментарий"}

    if db.Request.add.add_request(name, phone, email, business_type, comment):
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
