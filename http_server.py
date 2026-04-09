# import socket
import config as cfg
from http.server import HTTPServer, BaseHTTPRequestHandler, ThreadingHTTPServer
import json
import database_records as db
from urllib.parse import urlparse, parse_qs
import re
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

    @classmethod
    def route(cls, path):
        def decorator(func):
            cls.routes[path] = func
            return func

        return decorator

    #Обработка GET-запросов
    def do_GET(self):
        parsed_url = urlparse(self.path)
        path = parsed_url.path
        query_params = parse_qs(parsed_url.query)
        handler = self.routes.get(path)
        client_ip = self.client_address

        #Перебираем заголовки
        if not handler:
            self.send_response(404)
            self.send_header('Content-type', 'text/html')
            self.end_headers()
            self.wfile.write("Страница не найдена")
        else:
            self.set_handler()
            dic = handler(handler, query_params)
            self.wfile.write(json.dumps({'result': dic}).encode('utf-8'))

    #Обработка POST-запросов
    def do_POST(self):
        parsed_url = urlparse(self.path)
        path = parsed_url.path
        query_params = parse_qs(parsed_url.query)
        handler = self.routes.get(path)
        content_length = int(self.headers.get('Content-Length', 0))
        post_data = self.rfile.read(content_length)  # Returns bytes
        post_body = post_data.decode('utf-8')
        json_data = json.loads(post_body)

        if not handler:
            self.send_response(404)
            self.send_header('Content-type', 'text/html')
            self.end_headers()
            self.wfile.write("Страница не найдена")
        else:
            self.set_handler()
            dic = handler(handler, json_data)
            self.wfile.write(json.dumps({'result': dic}).encode('utf-8'))


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
