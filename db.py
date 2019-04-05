import sqlite3


# Создание базы данных
class DB:
    def __init__(self):
        conn = sqlite3.connect('news.db', check_same_thread=False)
        self.conn = conn

    def get_connection(self):
        return self.conn

    def __del__(self):
        self.conn.close()


# Работа с пользователями
class UsersModel:
    def __init__(self, connection):
        self.connection = connection

    def init_table(self):
        # Таблица для пользователей
        cursor = self.connection.cursor()
        cursor.execute('''CREATE TABLE IF NOT EXISTS users 
                            (id INTEGER PRIMARY KEY AUTOINCREMENT, 
                             user_name VARCHAR(50),
                             email VARCHAR(128),
                             password_hash VARCHAR(128),                    
                             about VARCHAR(128),
                             position VARCHAR(100)
                             )''')
        cursor.close()
        self.connection.commit()

    # Добавление пользователя
    def insert(self, user_name, password_hash, email, about):
        cursor = self.connection.cursor()
        cursor.execute('''INSERT INTO users 
                          (user_name, email, password_hash, about, position) 
                          VALUES (?,?,?,?,?)''', (user_name, email, password_hash, about, 'user'))
        cursor.close()
        self.connection.commit()

    # Получение информации о пользователе
    def get(self, user_id):
        cursor = self.connection.cursor()
        cursor.execute("SELECT * FROM users WHERE id = ?", (str(user_id),))
        row = cursor.fetchone()
        return row

    # Получение информации о всех пользователях
    def get_all(self):
        cursor = self.connection.cursor()
        cursor.execute("SELECT * FROM users")
        rows = cursor.fetchall()
        return rows

    # Существует ли пользователь?
    def exists(self, user_name, password_hash):
        cursor = self.connection.cursor()
        with_name = cursor.execute("SELECT * FROM users WHERE user_name = ? AND password_hash = ?",
                                   (user_name, password_hash))
        with_name = with_name.fetchone()
        with_email = cursor.execute("SELECT * FROM users WHERE email = ? AND password_hash = ?",
                                    (user_name, password_hash))
        with_email = with_email.fetchone()
        if with_name:
            return (True, with_name[0], with_name[1])
        elif with_email:
            return (True, with_email[0], with_email[1])
        return (False, )

    # Должность (пользователь или админ)
    def return_position(self, user_id):
        cursor = self.connection.cursor()
        cursor.execute("SELECT * FROM users WHERE id = ? AND position = ?", (str(user_id), 'adm'))
        row = cursor.fetchone()
        return True if row else False

    # Сущетсвует ли уже такое имя пользователя
    def user_name_exists(self, user_name):
        cursor = self.connection.cursor()
        cursor.execute("SELECT * FROM users WHERE user_name=?", (str(user_name),))
        row = cursor.fetchone()
        return True if row else False

    # Занят ли email
    def user_email_exists(self, email):
        cursor = self.connection.cursor()
        cursor.execute("SELECT * FROM users WHERE email=?", (str(email),))
        row = cursor.fetchone()
        return True if row else False


# Новости
class NewsModel:
    def __init__(self, connection):
        self.connection = connection

    # Создание таблицы
    def init_table(self):
        cursor = self.connection.cursor()
        cursor.execute('''CREATE TABLE IF NOT EXISTS news 
                            (id INTEGER PRIMARY KEY AUTOINCREMENT, 
                             title VARCHAR(100),
                             content VARCHAR(1000),
                             user_id INTEGER,
                             data VARCHAR(100)
                             )''')
        cursor.execute('''CREATE TABLE IF NOT EXISTS top 
                                            (id_user INTEGER, 
                                             id_news INTEGER,
                                             data_time
                                             )''')
        cursor.close()
        self.connection.commit()

    # Добавление лайка
    def add_like(self, user_id, news_id, data):
        self.delete_like(user_id, news_id)
        cursor = self.connection.cursor()
        cursor.execute('''INSERT INTO top 
                                  (id_user, id_news, data_time) 
                                  VALUES (?,?,?)''', (str(user_id), str(news_id), data))
        cursor.close()
        self.connection.commit()

    # Удаление лайка
    def delete_like(self, user_id, news_id):
        cursor = self.connection.cursor()
        cursor.execute('''DELETE FROM top 
                                  WHERE id_user = ? and id_news = ?''', (str(user_id), str(news_id), ))
        cursor.close()
        self.connection.commit()

    # Добавление новости
    def insert(self, title, content, user_id, data):
        cursor = self.connection.cursor()
        cursor.execute('''INSERT INTO news 
                          (title, content, user_id, data) 
                          VALUES (?,?,?,?)''', (title, content, str(user_id), data))
        cursor.close()
        self.connection.commit()

    # Получение новости
    def get(self, news_id):
        cursor = self.connection.cursor()
        cursor.execute("SELECT * FROM news WHERE id = ?", (str(news_id),))
        row = cursor.fetchone()
        return row

    # Получение всех новостей
    def get_all(self, user_id=None):
        cursor = self.connection.cursor()
        cursor.execute('''SELECT news.*, count(top.id_user) as likes_cnt , top2.id_user as liked
                        FROM news 
                        LEFT JOIN top ON news.id=top.id_news 
                        LEFT JOIN top as top2 ON news.id=top2.id_news and top2.id_user=? 
                        GROUP BY news.id''', (str(user_id),))
        rows = cursor.fetchall()
        return rows

    # Данные для админа
    def get_all_likes(self):
        cursor = self.connection.cursor()
        cursor.execute('''SELECT users.user_name, users.id, news.title, news.id, top.data_time 
        FROM users, news, top 
        WHERE users.id = top.id_user AND news.id = top.id_news 
        ORDER by data_time desc''')
        rows = cursor.fetchall()
        return rows

    # Удаление новости
    def delete(self, news_id):
        cursor = self.connection.cursor()
        cursor.execute('''DELETE FROM news WHERE id = ?''', (str(news_id),))
        cursor.execute('''DELETE FROM top WHERE id_news = ?''', (str(news_id),))
        cursor.close()
        self.connection.commit()

    # Лайкнутые пользователем новости
    def get_my(self, user_id):
        cursor = self.connection.cursor()
        cursor.execute('''SELECT news.*, count(top.id_user) as likes_cnt , top2.id_user as liked
                        FROM news
                        LEFT JOIN top ON news.id=top.id_news 
                        JOIN top as top2 ON news.id=top2.id_news and top2.id_user=?
                        GROUP BY news.id''', (str(user_id),))
        rows = cursor.fetchall()
        return rows

    # Получение популярных новостей (неделя, месяц, все время
    def get_popular_week(self, user_id):
        cursor = self.connection.cursor()
        cursor.execute('''SELECT news.*, count(top.id_user) as likes_cnt , top2.id_user as liked
                        FROM news
                        JOIN top ON news.id=top.id_news and date(top.data_time) > date('now', '-7 days')
                        LEFT JOIN top as top2 ON news.id=top2.id_news and top2.id_user=?
                        GROUP BY news.id
						ORDER BY likes_cnt DESC''', (str(user_id),))
        rows = cursor.fetchall()
        return rows

    def get_popular_month(self, user_id):
        cursor = self.connection.cursor()
        cursor.execute('''SELECT news.*, count(top.id_user) as likes_cnt , top2.id_user as liked
                                FROM news
                                JOIN top ON news.id=top.id_news and date(top.data_time) > date('now', '-30 days')
                                LEFT JOIN top as top2 ON news.id=top2.id_news and top2.id_user=?
                                GROUP BY news.id
        						ORDER BY likes_cnt DESC''', (str(user_id),))
        rows = cursor.fetchall()
        return rows

    def get_popular_alltime(self, user_id):
        cursor = self.connection.cursor()
        cursor.execute('''SELECT news.*, count(top.id_user) as likes_cnt , top2.id_user as liked
                                FROM news
                                JOIN top ON news.id=top.id_news
                                LEFT JOIN top as top2 ON news.id=top2.id_news and top2.id_user=?
                                GROUP BY news.id
        						ORDER BY likes_cnt DESC''', (str(user_id),))
        rows = cursor.fetchall()
        return rows


# Темы
class TopicModel:
    def __init__(self, connection):
        self.connection = connection

    # Создание таблицы
    def init_table(self):
        cursor = self.connection.cursor()
        cursor.execute('''CREATE TABLE IF NOT EXISTS topic 
                            (id INTEGER PRIMARY KEY AUTOINCREMENT, 
                             title VARCHAR(100),
                             content VARCHAR(1000),
                             user_id INTEGER,
                             data VARCHAR(100)
                             )''')
        cursor.close()
        self.connection.commit()

    # Добавление темы
    def insert(self, title, content, user_id, data):
        cursor = self.connection.cursor()
        cursor.execute('''INSERT INTO topic 
                          (title, content, user_id, data) 
                          VALUES (?,?,?,?)''', (title, content, str(user_id), data))
        cursor.close()
        self.connection.commit()

    # Получение всех тем
    def get_all(self, user_id=None):
        cursor = self.connection.cursor()
        if user_id:
            cursor.execute("SELECT * FROM topic WHERE user_id = ?",
                           (str(user_id),))
        else:
            cursor.execute("SELECT * FROM topic")
        rows = cursor.fetchall()
        return rows

    # Удаление темы
    def delete(self, topic_id):
        cursor = self.connection.cursor()
        cursor.execute('''DELETE FROM topic WHERE id = ?''', (str(topic_id),))
        cursor.close()
        self.connection.commit()


db = DB()
user = UsersModel(db.conn)
user.init_table()
topics = TopicModel(db.conn)
topics.init_table()
news = NewsModel(db.conn)
news.init_table()