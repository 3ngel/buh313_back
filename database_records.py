import psycopg2
import config as cfg

conn = psycopg2.connect(dbname=cfg.database_name, host=cfg.database_url, user=cfg.database_user,
                        password=cfg.database_password, port=cfg.database_port)
cur = conn.cursor()


class Authorization:
    # def check_email(email):
    #     try:
    #         cur.execute(f"SELECT * FROM public.users WHERE email = '{email}' LIMIT 1")
    #         records = cur.fetchall()
    #     except psycopg2.DatabaseError as err:
    #         print("Error: ", err)
    #         return False
    #     else:
    #         conn.commit()
    #         return False if records == [] else True
    def check_login(email, password_hash):
        cur.execute(
            f"SELECT email FROM public.users WHERE email = '{email}' and password_hash='{password_hash}'")
        records = cur.fetchall()
        if not records:
            return False
        else:
            return True

    def save_code(email, code):
        try:
            cur.execute(f"INSERT INTO public.sms_codes(email, sms_code) VALUES (%s,%s)",
                        (email, code))
        except psycopg2.DatabaseError as err:
            print("Error: ", err)
            return False
        else:
            conn.commit()
            return True

    def get_code(email):
        cur.execute(
            f"SELECT sms_code FROM public.sms_codes WHERE email = '{email}' order by tm_stamp desc limit 1")
        records = cur.fetchall()
        if not records:
            return None
        else:
            for sms_code in records:
                return sms_code[0]

    def delete_code(email):
        try:
            cur.execute(f"DELETE FROM public.sms_codes WHERE email = '{email}'")
        except psycopg2.DatabaseError as err:
            print("Error: ", err)
            return False
        else:
            conn.commit()
            return True


class Users:
    def activated_user(email, user_id, user_name):
        try:
            cur.execute(
                f"UPDATE public.users SET user_id=%s, user_name=%s, authorized = true WHERE email=%s",
                (user_id, user_name, email))
        except psycopg2.DatabaseError as err:
            print("Error: ", err)
            return False
        else:
            conn.commit()
            return True

    class Get:
        def list(self=""):
            cur.execute(f"SELECT email, firstname, lastname FROM public.users")
            records = cur.fetchall()
            answer = []
            for email, firstname, lastname in records:
                answer.append([email, firstname, lastname])
            return answer

        def by_user_id(user_id):
            cur.execute(
                f"SELECT authorized, deleted FROM public.users WHERE user_id = '{user_id}' LIMIT 1")
            records = cur.fetchall()
            if records == "":
                return "", ""
            for authorized, deleted in records:
                return authorized, deleted

        def by_email(email):
            try:
                cur.execute(f"SELECT authorized, deleted FROM public.users WHERE email = '{email}' LIMIT 1")
                records = cur.fetchall()
                print(records)
            except psycopg2.DatabaseError as err:
                print("Error: ", err)
                return "", ""
            else:
                conn.commit()
                if records == "":
                    return "", ""
                for authorized, deleted in records:
                    return authorized, deleted

        def name_by_email(email):
            try:
                cur.execute(f"SELECT firstname, lastname FROM public.users WHERE email = '{email}' LIMIT 1")
                records = cur.fetchall()
            except psycopg2.DatabaseError as err:
                print("Error: ", err)
                return "", ""
            else:
                conn.commit()
                if records == "":
                    return "", ""
                for firstname, lastname in records:
                    return firstname, lastname

        def roles_by_id(user_id):
            cur.execute(f"""select ur.role_id from public.user_roles ur where ur.user_id in 
                                (select u.email from users u where u.user_id = '{user_id}')""")
            records = cur.fetchall()
            answer = []
            for roles in records:
                answer.append(roles[0])
            return answer

        def roles_by_email(email):
            cur.execute(f"""select ur.role_id from public.user_roles ur where ur.user_id = '{email}'""")
            records = cur.fetchall()
            answer = []
            for roles in records:
                answer.append(roles[0])
            return answer

    class edit:
        def save(self):
            return

    def create(email, firstname, lastname):
        try:
            cur.execute(
                f"INSERT INTO public.users (email, firstname, lastname, authorized, deleted) values (%s,%s,%s,%s, %s)",
                (email, firstname, lastname, False, False)
            )
        except psycopg2.DatabaseError as err:
            print("Error: ", err)
            return False
        else:
            conn.commit()
            return True

    # "Удаление" пользователя
    def delete(email):
        try:
            # Не удаляем, а помечаем их удалёнными
            cur.execute(f"UPDATE public.users SET deleted=true WHERE email='{email}'")
        except psycopg2.DatabaseError as err:
            print("Error: ", err)
            return False
        else:
            conn.commit()
            return True


class Services:
    class select:
        def servises_list(self=""):
            cur.execute(f"SELECT service_name, price FROM public.services")
            records = cur.fetchall()
            answer = []
            for name, price in records:
                answer.append([name, price])
            return answer

        def service(name):
            cur.execute(f"SELECT service_name, price FROM public.services WHERE service_name = '{name}'")
            records = cur.fetchall()
            for name, price in records:
                return name, price

        def full_service(name):
            cur.execute(f"SELECT service_name, price, type FROM public.services WHERE service_name = '{name}'")
            records = cur.fetchall()
            for name, price, type in records:
                return name, price, type

    class add:
        def add_service(name, price, type):
            # Вставить проверки значений
            try:
                cur.execute(f"INSERT INTO public.services(service_name, price, type) VALUES (%s,%s,%s)",
                            (name, price, type))
            except psycopg2.DatabaseError as err:
                print("Error: ", err)
                return False
            else:
                conn.commit()
                return True

    class edit:
        def edit_service(name, type, new_value):
            t = "service_name" if type == "name" else "price"
            try:
                cur.execute(f"UPDATE public.services SET {t}=%s WHERE service_name=%s", (new_value, name))
            except psycopg2.DatabaseError as err:
                print("Error: ", err)
                return False
            else:
                conn.commit()
                return True

        def full_edit_service(name, new_name, price, type):
            try:
                cur.execute(f"UPDATE public.services SET service_name=%s, price=%s, type=%s WHERE service_name=%s",
                            (new_name, price, type, name))
            except psycopg2.DatabaseError as err:
                print("Error: ", err)
                return False
            else:
                conn.commit()
                return True

    class delete:
        def delete_service(name):
            try:
                cur.execute(f"DELETE FROM public.services WHERE service_name='{name}'")
            except psycopg2.DatabaseError as err:
                print("Error: ", err)
                return False
            else:
                conn.commit()
                return True


class Request:
    class select:
        def request_list(self=""):
            cur.execute(f"SELECT id, name, phone, status FROM public.requests")
            records = cur.fetchall()
            answer = []
            for id, name, phone, status in records:
                answer.append([id, name, phone, status])
            return answer

        def by_id(request_id: str):
            cur.execute(
                f"SELECT id,name,phone, email, business_type, comment, status FROM public.requests WHERE id = '{request_id}'")
            records = cur.fetchall()
            for id, name, phone, email, business_type, comment, status in records:
                return id, name, phone, email, business_type, comment, status

    class add:
        def add_request(name, phone, email, business_type, comment, client_ip):
            # Вставить проверки значений
            try:
                cur.execute(
                    f"INSERT INTO public.requests (name, phone, email, business_type, comment, status) values (%s, %s, %s, %s, %s, \'NEW\' );",
                    (name, phone, email, business_type, comment))
            except psycopg2.DatabaseError as err:
                print("Error: ", err)
                return False
            else:
                conn.commit()
                return True
            return

    class edit:
        def edit_status(id, status):
            try:
                cur.execute(f"UPDATE public.requests SET status=%s WHERE ud=%s", (status, id))
            except psycopg2.DatabaseError as err:
                print("Error: ", err)
                return False
            else:
                conn.commit()
                return True


if __name__ == '__main__':
    print(Users.Get.roles('470402973'))
    # print(Authorization.check_email("angelina_panfilova@bk.ru"))
