from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField, TextAreaField, PasswordField, BooleanField, StringField
from wtforms.fields.html5 import EmailField
from wtforms.validators import DataRequired, Email, Optional, Length
from flask import render_template, redirect, Flask
from db import NewsModel, UsersModel, db

app = Flask(__name__)
app.config['SECRET_KEY'] = 'yandexlyceum_secret_key'
session = {}


class AddNewsForm(FlaskForm):
    title = StringField('Заголовок новости', validators=[DataRequired()])
    content = TextAreaField('Текст новости', validators=[DataRequired()])
    submit = SubmitField('Добавить')


class LoginForm(FlaskForm):
    username = StringField('Логин', validators=[DataRequired()])
    password = PasswordField('Пароль', validators=[DataRequired()])
    remember_me = BooleanField('Запомнить меня')
    submit = SubmitField('Войти')
    reg = SubmitField('Зарегестрироваться')


class RegistrationForm(FlaskForm):
    username = StringField('Логин', validators=[DataRequired()])
    password = PasswordField('Пароль', validators=[DataRequired()])
    password_once = PasswordField('Повторите пароль', validators=[DataRequired()])
    email = EmailField('Email', validators = [DataRequired(), Email()])
    about = TextAreaField('Немного о себе..', [Optional(), Length(min=10, max=100)])
    send = SubmitField('Отправить')
    back = SubmitField('Назад')


@app.route('/add_news', methods=['GET', 'POST'])
def add_news():
    if 'username' not in session:
        return redirect('/login')
    form = AddNewsForm()
    if form.validate_on_submit():
        title = form.title.data
        content = form.content.data
        nm = NewsModel(db.get_connection())
        nm.insert(title, content, session['user_id'])
        return redirect("/index")
    return render_template('add_news.html', title='Добавление новости',
                           form=form, username=session['username'])


@app.route('/delete_news/<int:news_id>', methods=['GET'])
def delete_news(news_id):
    if 'username' not in session:
        return redirect('/login')
    nm = NewsModel(db.get_connection())
    nm.delete(news_id)
    return redirect("/index")


@app.route('/')
@app.route('/index')
def index():
    if 'username' not in session:
        print(session)
        return redirect('/login')
    news = NewsModel(db.get_connection()).get_all(session['user_id'])
    return render_template('index.html', username=session['username'],
                           news=news, title='Новости')


@app.route('/logout')
def logout():
    session.pop('username', 0)
    session.pop('user_id', 0)
    return redirect('/login')


@app.route('/login', methods=['GET', 'POST'])
def login():
    form = LoginForm()
    if form.reg.data:
        return redirect("/registration")
    if form.validate_on_submit():
        user_name = form.username.data
        password = form.password.data
        user_model = UsersModel(db.get_connection())
        exists = user_model.exists(user_name, password)
        if (exists[0]):
            session['username'] = user_name
            session['user_id'] = exists[1]
        else:
            return render_template('login.html', title='Авторизация', form=form,
                                   err='Проверьте правильность введенных данных')
        return redirect("/index")
    return render_template('login.html', title='Авторизация', form=form)


@app.route('/registration', methods=['GET', 'POST'])
def registration():
    form = RegistrationForm()
    if form.back.data:
        email = form.email
        print(type(email))
        return redirect('/index')
    if form.validate_on_submit():
        user_name = form.username.data
        password = form.password.data
        email = form.email.data
        print(type(email))
    return render_template('registration.html', title='Регистрация', form=form, err='')


if __name__ == '__main__':
    app.run(port=8063, host='127.0.0.1')