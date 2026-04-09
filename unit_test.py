import unittest
import server as srv


class ServerCheccked(unittest.TestCase):

    def setUp(self):
        self.check = srv.Checked()

    #Полностью корректное имя
    def test_name_correct(self):
        name = "Ангелина"
        self.assertTrue(self.check.name(name))  # add assertion here

    #Слишком корроткое имя
    def test_name_short(self):
        name = "Анг"
        with self.assertRaises(AssertionError) as context:
            self.check.name(name)
            self.assertTrue('Имя слишком короткое' in context.exception)

    #Слишком длинное имя (65 символов)
    def test_name_bigger(self):
        name = "ангелинаангелинаангелинаангелинаангелинаангелинаангелинаангелинаф"
        with self.assertRaises(AssertionError) as context:
            self.check.name(name)
            self.assertTrue('Имя слишком длинное' in context.exception)

    #Все некорректные символы
    def test_name_incorrect_symbols(self):
        name = "First"
        with self.assertRaises(AssertionError) as context:
            self.check.name(name)
            self.assertTrue('Некорректные символы в имени' in context.exception)

    #Имя с маленькой буквы
    def test_name_small_first_symbol(self):
        name = "ангелина"
        with self.assertRaises(AssertionError) as context:
            self.check.name(name)
            self.assertTrue('Некорректные символы в имени' in context.exception)

    #Всё имя большими буквами
    def test_name_big_all_symbols(self):
        name = "АНГЕЛИНА"
        with self.assertRaises(AssertionError) as context:
            self.check.name(name)
            self.assertTrue('Некорректные символы в имени' in context.exception)

    #Проверка почты

    #Корректная почта
    def test_email_correct(self):
        email = "angelina_panfilova@bk.ru"
        self.assertTrue(self.check.email(email))  # add assertion here

    #Некорректный адрес электронной почты
    def test_email_incorrect(self):
        email = "angelina_panfilovabk.ru"
        with self.assertRaises(AssertionError) as context:
            self.check.email(email)
            self.assertTrue('Некорректные символы в адресе электронной почты' in context.exception)


if __name__ == '__main__':
    unittest.main()
