from base64 import b64encode
from flask import Flask, render_template, request, Blueprint, redirect, url_for
from flask_paginate import Pagination, get_page_parameter
from flask_material import Material
from flask_wtf import FlaskForm
from flask_wtf.file import FileField
from wtforms import TextField, HiddenField, ValidationError, RadioField,\
    BooleanField, SubmitField, PasswordField, FormField, validators
from wtforms.validators import Required
import psycopg2

app = Flask(__name__)
Material(app)
app.config['SECRET_KEY'] = 'USE-YOUR-OWN-SECRET-KEY-DAMNIT'
app.config['RECAPTCHA_PUBLIC_KEY'] = 'TEST'

# straight from the wtforms docs:
class LoginForm(FlaskForm): 
    username = TextField('Username', [validators.required()])
    password = PasswordField('Password', [validators.required()])
    submit = SubmitField(label="Log In")
class RegisterForm(FlaskForm): 
    username = TextField('Username', [validators.required()])
    password = PasswordField('Password', [validators.required()])
    submit = SubmitField(label="Create Account")
class ExampleForm(FlaskForm):
    field1 = TextField('First Field', description='This is field one.')
    field2 = TextField('Second Field', description='This is field two.',
                       validators=[Required()])
    checkbox_field = BooleanField('This is a checkbox',
                                  description='Checkboxes can be tricky.')

    photo = FileField('Sample upload')
    submit_button = SubmitField('Submit Form')

class Image():
    def __init__(self, description):
        self.description = description

def get_database():
    conn = psycopg2.connect("dbname='flask' user='flask' host='db'")
    conn.autocommit = True
    return conn, conn.cursor()

@app.route('/', methods=['GET', 'POST'])
def login():
    form = LoginForm()
    if request.method == 'POST':
        app.logger.info(request.values)
        username = request.values.get('username')
        password = request.values.get('password')
        conn, cur = get_database()
        cur.execute('SELECT password FROM public.users WHERE username=%s', (username,))
        check = cur.fetchone()
        if check != None and check[0] == password:
            return redirect(url_for('home'))
    return render_template('login.html', form=form)

@app.route('/register', methods=['GET', 'POST'])
def register():
    form = RegisterForm()
    if request.method == 'POST':
        app.logger.info(request.values)
        con, cursor = get_database()
        cursor.execute("""INSERT INTO public.users VALUES(%s, %s)""", (request.values.get('username')
        , request.values.get('password')))
        cursor.close()
        return redirect(url_for('login'))
    return render_template('register.html', form=form)

@app.route('/home')
def home(page=1):
    
    page = request.args.get(get_page_parameter(), type=int, default=1)
    pagination = Pagination(page=page, per_page=10, total=len(images), search=False, record_name='images')
    return render_template('home.html', images=images, per_page=10, pagination=pagination)

@app.route('/upload', methods=['GET','POST'])
def upload():
    if request.method == 'POST':
        conn, cursor = get_database()
        new = conn.lobject()
        oid = new.oid
        new.write(request.files.photo)
        image = b64encode(new.read())
        return render_template('image.html', image=image)
        app.logger.info(request.files.photo)
    form = ExampleForm()
    return render_template('upload.html', form=form)


if __name__ == '__main__':
    app.run(host='0.0.0.0', debug=True)
  