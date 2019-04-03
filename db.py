import sqlite3


class DB:
    def __init__(self):
        conn = sqlite3.connect('news.db', check_same_thread=False)
        self.conn = conn

    def get_connection(self):
        return self.conn

    def __del__(self):
        self.conn.close()


class UsersModel:
    def __init__(self, connection):
        self.connection = connection

    def init_table(self):
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

    def insert(self, user_name, email, password_hash, about):
        cursor = self.connection.cursor()
        cursor.execute('''INSERT INTO users 
                          (user_name, email, password_hash, about, position) 
                          VALUES (?,?,?,?,?)''', (user_name, email, password_hash, about, 'user'))
        cursor.close()
        self.connection.commit()

    def get(self, user_id):
        cursor = self.connection.cursor()
        cursor.execute("SELECT * FROM users WHERE id = ?", (str(user_id),))
        row = cursor.fetchone()
        return row

    def get_all(self):
        cursor = self.connection.cursor()
        cursor.execute("SELECT * FROM users")
        rows = cursor.fetchall()
        return rows

    def exists(self, user_name, password_hash):
        cursor = self.connection.cursor()
        with_name = cursor.execute("SELECT * FROM users WHERE user_name = ? AND password_hash = ?",
                       (user_name, password_hash))
        with_name = with_name.fetchone()
        with_email = cursor.execute("SELECT * FROM users WHERE email = ? AND password_hash = ?",
                           (user_name, password_hash))
        with_email = with_email.fetchone()
        if with_name:
            return (True, with_name[0], )
        elif with_email:
            return (True, with_email[0], )
        return (False, )

    def return_position(self, user_id):
        cursor = self.connection.cursor()
        cursor.execute("SELECT * FROM users WHERE id = ? AND position = ?", (str(user_id), 'adm'))
        row = cursor.fetchone()
        return (True, row[0]) if row else (False,)


class NewsModel:
    def __init__(self, connection):
        self.connection = connection

    def init_table(self):
        cursor = self.connection.cursor()
        cursor.execute('''CREATE TABLE IF NOT EXISTS news 
                            (id INTEGER PRIMARY KEY AUTOINCREMENT, 
                             title VARCHAR(100),
                             content VARCHAR(1000),
                             user_id INTEGER,
                             data VARCHAR(100)
                             )''')
        cursor.close()
        self.connection.commit()

    def insert(self, title, content, user_id, data):
        cursor = self.connection.cursor()
        cursor.execute('''INSERT INTO news 
                          (title, content, user_id, data) 
                          VALUES (?,?,?,?)''', (title, content, str(user_id), data))
        self.sort_news()
        cursor.close()
        self.connection.commit()

    def get(self, news_id):
        cursor = self.connection.cursor()
        cursor.execute("SELECT * FROM news WHERE id = ?", (str(news_id),))
        row = cursor.fetchone()
        return row

    def sort_news(self):
        tab = self.get_all()
        news = sorted(tab, key=lambda tup: tup[1].lower())
        news = sorted(news, key=lambda tup: tup[4])
        cursor = self.connection.cursor()
        for el in news:
            cursor.execute('''DELETE FROM news WHERE id = ?''', (str(el[0]),))
        for el in news:
            cursor.execute('''INSERT INTO news 
                                      (title, content, user_id, data) 
                                      VALUES (?,?,?,?)''', el[1:])
        cursor.close()
        self.connection.commit()

    def get_all(self, user_id=None):
        cursor = self.connection.cursor()
        if user_id:
            cursor.execute("SELECT * FROM news WHERE user_id = ?",
                           (str(user_id),))
        else:
            cursor.execute("SELECT * FROM news")
        rows = cursor.fetchall()
        return rows

    def delete(self, news_id):
        cursor = self.connection.cursor()
        cursor.execute('''DELETE FROM news WHERE id = ?''', (str(news_id),))
        cursor.close()
        self.connection.commit()


db = DB()
user = UsersModel(db.conn)
user.init_table()
news = NewsModel(db.conn)
news.init_table()