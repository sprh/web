from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField, TextAreaField, PasswordField, BooleanField, StringField
from wtforms.fields.html5 import EmailField
from wtforms.validators import DataRequired, Email, Optional, Length
from flask import render_template, redirect, Flask, request
from db import NewsModel, UsersModel, db
import json
import datetime

app = Flask(__name__)
app.config['SECRET_KEY'] = 'yandexlyceum_secret_key'
session = {}
recent = '/login'
now = datetime.datetime.now()


class AddNewsForm(FlaskForm):
    title = StringField('Заголовок новости', validators=[DataRequired()])
    content = TextAreaField('Текст новости', validators=[DataRequired()])
    submit = SubmitField('Добавить')


class LoginForm(FlaskForm):
    username = StringField('Логин или email', validators=[DataRequired()])
    password = PasswordField('Пароль', validators=[DataRequired()])
    submit = SubmitField('Войти')
    reg = SubmitField('Зарегестрироваться')


class RegistrationForm(FlaskForm):
    username = StringField('Логин', validators=[DataRequired()])
    password = PasswordField('Пароль', validators=[DataRequired()])
    email = EmailField('Email', validators = [DataRequired(), Email()])
    about = TextAreaField('Немного о себе..', [Optional(), Length(min=10, max=100)])
    send = SubmitField('Отправить')
    back = SubmitField('Назад')


@app.route('/add_news', methods=['GET', 'POST'])
def add_news():
    global recent
    recent = '/add_news'
    if 'username' not in session:
        return redirect('/login')
    form = AddNewsForm()
    if form.validate_on_submit():
        title = form.title.data
        content = form.content.data
        nm = NewsModel(db.get_connection())
        data = '-'.join([str(now.day), str(now.month), str(now.year)])
        nm.insert(title, content, session['user_id'], data)
        return redirect("/index")
    return render_template('add_news.html', title='Добавление новости',
                           form=form, username=session['username'], about_page='')


@app.route('/delete_news/<int:news_id>', methods=['GET'])
def delete_news(news_id):
    if 'username' not in session:
        return redirect('/login')
    nm = NewsModel(db.get_connection())
    nm.delete(news_id)
    return redirect("/index")


@app.route('/')
@app.route('/index', methods=['GET', 'POST'])
def index():
    global recent
    recent = '/index'
    if 'username' not in session:
        return redirect('/login')
    if request.method == 'POST':
        if 'perenap' in request.form:
            return redirect('/add_news')
    news = NewsModel(db.get_connection()).get_all(session['user_id'])
    return render_template('index.html', username=session['username'],
                           news=news, title='Новости', about_page='')


@app.route('/logout')
def logout():
    session.pop('username', 0)
    session.pop('user_id', 0)
    return redirect('/login')


@app.route('/login', methods=['GET', 'POST'])
def login():
    global recent
    recent = 'login'
    form = LoginForm()
    if form.reg.data:
        return redirect("/registration")
    if form.validate_on_submit():
        user_name = form.username.data
        password = form.password.data
        user_model = UsersModel(db.get_connection())
        exists = user_model.exists(user_name, password)
        if exists[0]:
            session['username'] = user_name
            session['user_id'] = exists[1]
        else:
            return render_template('login.html', title='Авторизация', form=form,
                                   err='Проверьте правильность введенных данных')
        return redirect("/index")
    return render_template('login.html', title='Авторизация', form=form,
                           about_page='')


@app.route('/registration', methods=['GET', 'POST'])
def registration():
    global recent
    recent = '/registration'
    form = RegistrationForm()
    if form.back.data:
        return redirect('/index')
    if form.send.data:
        print('done')
        user_name = form.username.data
        password = form.password.data
        user_model = UsersModel(db.get_connection())
        email = form.email.data
        about = form.about.data
        user_model.insert(user_name, email, password, about)
        exists = user_model.exists(user_name, password)
        if (exists[0]):
            session['username'] = user_name
            session['user_id'] = exists[1]
        else:
            return redirect('/registration')
        return redirect("/index")
    return render_template('registration.html', title='Регистрация', form=form, err='',
                           about_page='Расскажите нам немного о себе!')


@app.route('/about_us')
def about_us():
    file = open('templates/about_us.txt', 'r')
    text = file.readlines()
    return render_template('about_us.html', title='О проекте', text=text, href=recent)


@app.route('/contacts')
def contacts():
    with open("templates/contacts.json", "rt", encoding="utf8") as f:
        text = json.loads(f.read())
    return render_template('contacts.html', title='Контакты', href=recent, text=text)


@app.route('/cooperation')
def cooperation():
    with open("templates/contacts.json", "rt", encoding="utf8") as f:
        text = json.loads(f.read())
    return render_template('cooperation.html', title='Сотрудничество', href=recent, text=text)


@app.errorhandler(404)
def page_not_found(e):
    return render_template('404.html', title='Упс, ошибка!'), 404


@app.errorhandler(405)
def page_not_found(e):
    return render_template('404.html', title='Упс, ошибка!'), 405


if __name__ == '__main__':
    app.run(port=8057, host='127.0.0.1')