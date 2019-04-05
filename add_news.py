from flask_wtf import FlaskForm
from wtforms import ValidationError, SubmitField, TextAreaField, PasswordField, BooleanField, StringField
from wtforms.fields.html5 import EmailField
from wtforms.validators import DataRequired, Email, Optional, Length
from flask import render_template, redirect, Flask, request
from db import NewsModel, UsersModel, db, TopicModel
import json
from datetime import datetime

app = Flask(__name__)
app.config['SECRET_KEY'] = 'yandexlyceum_secret_key'
session = {}
recent = '/login'


# Возвращение даты в формате год-месяц-день для сортирвки новостей по популярности
def data_return():
    return datetime.today().strftime('%Y-%m-%d')


# Классы для шаблонов
class AddNewsForm(FlaskForm):
    title = StringField('Заголовок новости', validators=[DataRequired()])
    content = TextAreaField('Текст новости', validators=[DataRequired()])
    submit = SubmitField('Добавить')
    back = SubmitField('Назад')


class LoginForm(FlaskForm):
    username = StringField('Логин или email', validators=[DataRequired()])
    password = PasswordField('Пароль', validators=[DataRequired()])
    submit = SubmitField('Войти')
    reg = SubmitField('Зарегистрироваться')


# Проверка, существует ли уже имя пользователя (для регистрации
def validate_user_name(form, field):
    if len(field.data) == 0:
        raise ValidationError('Поле не заполнено')
    user_model = UsersModel(db.get_connection())
    if user_model.user_name_exists(field.data):
        raise ValidationError("Пользователь существует")


# Проверка, существует ли аккуаун с таким email (для регистрации)
def validate_user_email(form, field):
    if len(field.data) == 0:
        raise ValidationError('Поле не заполнено')
    user_model = UsersModel(db.get_connection())
    if user_model.user_email_exists(field.data):
        raise ValidationError("Email уже занят")


class RegistrationForm(FlaskForm):
    username = StringField('Логин', validators=[validate_user_name])
    password = PasswordField('Пароль', validators=[DataRequired('Вы оставили поле пустым!')])
    email = EmailField('Email', validators=[Email("Не email"), validate_user_email])
    about = TextAreaField('Немного о себе..', [Optional()])
    submit = SubmitField('Отправить')
    back = SubmitField('Назад')


class AddTopicForm(FlaskForm):
    title = StringField('Заголовок темы', validators=[DataRequired()])
    content = TextAreaField('Что случилось?', validators=[DataRequired()])
    submit = SubmitField('Добавить')
    back = SubmitField('Назад')


# Авторизация
@app.route('/login', methods=['GET', 'POST'])
def login():
    global recent
    recent = '/login'
    form = LoginForm()
    # Переход к регистрации
    if form.reg.data:
        return redirect("/registration")
    elif form.validate_on_submit():
        user_name = form.username.data
        password = form.password.data
        user_model = UsersModel(db.get_connection())
        # Проверка, существует ли аккаунт
        exists = user_model.exists(user_name, password)
        if exists[0]:
            session['username'] = exists[2]
            session['user_id'] = exists[1]
        else:
            return render_template('login.html', title='Авторизация', form=form,
                                   err='Проверьте правильность введенных данных')
        # Переход к новостям
        return redirect("/index")
    return render_template('login.html', title='Авторизация', form=form,
                           about_page='')


# Добавление лайка
@app.route('/api/add_like/<int:id>', methods=['PUT', "POST"])
def add_like(id):
    if 'username' not in session:
        return 'not ok'
    nm = NewsModel(db.get_connection())
    nm.add_like(session['user_id'], id, data_return())
    return 'ok'


# Удаление лайка (нельзя ставить лайк больше 1 раза --> при попытке поставить второй раз первый удаляется. 1-1+1 = 1)
@app.route('/api/delete_like/<int:id>', methods=['PUT', "POST"])
def delete_like(id):
    if 'username' not in session:
        return 'not ok'
    nm = NewsModel(db.get_connection())
    nm.delete_like(session['user_id'], id)
    return 'ok'


# Удаление новости
@app.route('/delete_news/<int:news_id>', methods=['GET'])
def delete_news(news_id):
    if 'username' not in session:
        return redirect('/login')
    nm = NewsModel(db.get_connection())
    nm.delete(news_id)
    return redirect("/index")


# Удаление темы
@app.route('/delete_topic/<int:topic_id>', methods=['GET'])
def delete_topic(topic_id):
    if 'username' not in session:
        return redirect('/login')
    nm = TopicModel(db.get_connection())
    nm.delete(topic_id)
    return redirect("/topics")


# Регистрация
@app.route('/registration', methods=['GET', 'post'])
def registration():
    global recent
    recent = 'registration'
    form = RegistrationForm()
    user_model = UsersModel(db.get_connection())
    if form.back.data:
        return redirect('/login')
    elif form.validate_on_submit():
        user_name = form.username.data
        password = form.password.data
        email = form.email.data
        about = form.about.data
        user_model.insert(user_name, password, email, about)
        # Проверка, точно ли все в базе
        exists = user_model.exists(user_name, password)
        if exists[0]:
            session['username'] = user_name
            session['user_id'] = exists[1]
        # Переход к новостям
        return redirect('/index')
    return render_template('registration.html', title='Регистрация', form=form, err='',
                           about_page='Расскажите нам немного о себе!')


# Новости, которые пользователь лайкнул
@app.route('/lk')
def lk():
    global recent
    recent = '/lk'
    if 'username' not in session:
        return redirect('/login')
    news = NewsModel(db.get_connection())
    news = news.get_my(session['user_id'])
    return render_template('all_news.html', title='Сохраненные новости',
                           news=news)


# Все новости
@app.route('/')
@app.route('/index', methods=['GET', 'POST'])
def index():
    global recent
    recent = '/index'
    if 'username' not in session:
        return redirect('/login')
    if request.method == 'POST':
        # Добавление новости. Только для админа
        if 'perenap' in request.form:
            return redirect('/add_news')
    user = UsersModel(db.get_connection())
    # Проверка. User или adm (пользователь или админ)
    position = user.return_position(session['user_id'])
    news = NewsModel(db.get_connection())
    news = news.get_all(session['user_id'])
    return render_template('all_news.html', title='Новости',
                           news=news, position=position)


# Добавдение новости
@app.route('/add_news', methods=['GET', 'POST'])
def add_news():
    if 'username' not in session:
        return redirect('/login')
    form = AddNewsForm()
    if form.back.data:
        return redirect('/index')
    elif form.validate_on_submit():
        title = form.title.data
        content = form.content.data
        nm = NewsModel(db.get_connection())
        nm.insert(title, content, session['user_id'], data_return())
        return redirect("/index")
    user = UsersModel(db.get_connection())
    position = user.return_position(session['user_id'])
    # Если пользователь случайно вбил, проверяется, имеет ли он права
    if not position:
        return render_template('indifferent/not_for_admin.html', title='У вас недостаточно прав!')
    else:
        return render_template('add_news.html', title='Добавление новости',
                               form=form, username=session['username'], about_page='')


# Популярные новости. Сортировка по лайкам
@app.route('/popular/<string:period>')
def popular(period):
    global recent
    recent = '/popular/' + period
    news = NewsModel(db.get_connection())
    # + сортировка по дате. За последнюю неделю, месяц, все время
    if period == 'week':
        if 'username' not in session:
            return redirect('/login')
        news = news.get_popular_week(session['user_id'])
        return render_template('all_news.html', title='Популярное',
                               news=news)
        return 'week'
    elif period == 'month':
        if 'username' not in session:
            return redirect('/login')
        news = news.get_popular_month(session['user_id'])
        return render_template('all_news.html', title='Популярное',
                               news=news)
    elif period == 'all_time':
        if 'username' not in session:
            return redirect('/login')
        news = news.get_popular_alltime(session['user_id'])
        return render_template('all_news.html', title='Популярное',
                               news=news)


# Вывод тем
@app.route('/topics', methods=['GET', 'POST'])
def topics():
    global recent
    recent = '/topics'
    if 'username' not in session:
        return redirect('/login')
    if request.method == 'POST':
        if 'perenap' in request.form:
            return redirect('/add_topic')
    user = UsersModel(db.get_connection())
    position = user.return_position(session['user_id'])
    topics = TopicModel(db.get_connection())
    topics = topics.get_all()
    return render_template('topics.html', title='Наиболее актуальные и волнующие темы',
                           topics=topics, position=position)


# Добавление темы. Только для админа
@app.route('/add_topic', methods=['GET', 'POST'])
def add_topic():
    if 'username' not in session:
        return redirect('/login')
    form = AddTopicForm()
    if form.back.data:
        return redirect('/topics')
    elif form.validate_on_submit():
        title = form.title.data
        content = form.content.data
        nm = TopicModel(db.get_connection())
        nm.insert(title, content, session['user_id'], data_return())
        return redirect("/topics")
    user = UsersModel(db.get_connection())
    position = user.return_position(session['user_id'])
    # Проверка, имеет ли пользователь права
    if not position:
        return render_template('indifferent/not_for_admin.html', title='У вас недостаточно прав!')
    else:
        return render_template('add_topic.html', title='Добавление темы',
                               form=form, username=session['username'], about_page='')


# Контактная информация
@app.route('/contacts/<string:for_what>')
def contacts(for_what):
    # Если выбрали рекламу
    if for_what == 'advertising':
        with open("templates/indifferent/contacts.json", "rt", encoding="utf8") as f:
            text = json.loads(f.read())
        return render_template('indifferent/contacts.html', title='По поводу рекламы..', href=recent, text=text)
    # Сотрудничество
    if for_what == 'cooperation':
        with open("templates/indifferent/contacts.json", "rt", encoding="utf8") as f:
            text = json.loads(f.read())
        return render_template('indifferent/cooperation.html', title='Сотрудничество с нами', href=recent, text=text)


# Вакансии
@app.route('/jobs')
def jobs():
    with open("templates/indifferent/jobs.json", "rt", encoding="utf8") as f:
        text = json.loads(f.read())
    return render_template('indifferent/jobs.html', title='Вакансии', text=text, href=recent)


# О новостях (описания нет)
@app.route('/about_us')
def about_us():
    file = open('templates/indifferent/about_us.txt', 'r')
    text = file.readlines()
    return render_template('indifferent/about_us.html', title='О проекте', text=text, href=recent)


# Обработка ошибок
@app.errorhandler(404)
def page_not_found(e):
    return render_template('indifferent/404.html', title='Упс, ошибка!'), 404


@app.errorhandler(405)
def page_not_found(e):
    return render_template('indifferent/404.html', title='Упс, ошибка!'), 405


@app.errorhandler(500)
def page_not_found(e):
    return render_template('indifferent/404.html', title='Упс, ошибка!'), 500


# Страница только для админа
@app.route('/for_adm')
def for_adm():
    if 'username' not in session:
        return redirect('/login')
    um = UsersModel(db.get_connection())
    user = um.return_position(session['user_id'])
    # Проверка, есть ли права
    if user:
        nm = NewsModel(db.get_connection())
        news = nm.get_all_likes()
        print(news)
        return render_template('for_admin.html', mas=news, title='Информация о лайках')
    else:
        return render_template('indifferent/not_for_admin.html', title='У вас недостаточно прав!')


if __name__ == '__main__':
    app.run(port=8054, host='127.0.0.1')
