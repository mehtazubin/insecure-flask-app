from base64 import b64encode
from flask import Flask, render_template, request, Blueprint, redirect, url_for
from flask_paginate import Pagination, get_page_args
from flask_material import Material
from flask_wtf import FlaskForm
from flask_wtf.file import FileField
from wtforms import TextField, HiddenField, ValidationError, RadioField,\
    BooleanField, SubmitField, PasswordField, FormField, validators
from wtforms.validators import Required
import psycopg2, os

app = Flask(__name__, static_url_path='/web/static')
Material(app)
app.config['WTF_CSRF_ENABLED'] = False

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
    def __init__(self, path):
        self.path = path

def get_database():
    conn = psycopg2.connect("dbname='flask' user='flask' host='db'")
    return conn, conn.cursor()

@app.route('/', methods=['GET', 'POST'])
def login():
    form = LoginForm()
    if request.method == 'POST':
        app.logger.info(request.values)
        username = request.values.get('username')
        password = request.values.get('password')
        con, cur = get_database()
        cur.execute('SELECT password FROM public.users WHERE username=%s', (username,))
        check = cur.fetchone()
        con.close()
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
        con.commit()
        con.close()
        return redirect(url_for('login'))
    return render_template('register.html', form=form)

@app.route('/home')
def home(page=1):
    
    page, per_page, offset = get_page_args(page_parameter='page',
                                           per_page_parameter='per_page')
    con, cursor = get_database()
    cursor.execute("""SELECT oid FROM public.images limit %s offset %s""", (per_page, offset))
    fetched = cursor.fetchall()
    cursor.execute("""SELECT COUNT(*) FROM public.images""")
    result = cursor.fetchone()
    images = []
    for i in range(0,len(fetched),2):
        l = con.lobject(fetched[i][0])
        path1 = os.path.join('/web/static/images', str(fetched[i][0]))
        app.logger.info(path1)
        l.export(path1)
        l.close()
        if i + 1 < len(fetched):
            l = con.lobject(fetched[i + 1][0])
            path2 = os.path.join('/web/static/images', str(fetched[i + 1][0]))
            l.export(path2)
            l.close()
            images.append((path1,path2))
        else:
            images.append((path1,))
    con.close()
    app.logger.info(images)
    pagination = Pagination(page=page, per_page=10, total=int(result[0]), search=False, record_name='images')
    return render_template('home.html', images=images, per_page=10, pagination=pagination)

@app.route('/upload', methods=['GET','POST'])
def upload():
    if request.method == 'POST':
        con, cursor = get_database()
        image = request.files.get('photo')
        image.save(os.path.join('upload',image.filename))
        new = con.lobject(new_file=os.path.join('upload', image.filename))
        oid = new.oid
        cursor.execute("""INSERT INTO public.images(oid,username) VALUES(%s, %s)""", (oid, 'test'))
        new.close()
        con.commit()
        con.close()
    form = ExampleForm()
    return render_template('upload.html', form=form)


if __name__ == '__main__':
    app.run(host='0.0.0.0', debug=True)
  