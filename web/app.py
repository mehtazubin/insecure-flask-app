from base64 import b64encode
from flask import Flask, render_template, request, Blueprint, redirect, url_for, flash, session
from flask_bootstrap import Bootstrap
from flask_nav import Nav
from flask_nav.elements import *
from flask_paginate import Pagination, get_page_args
from flask_material import Material
from flask_wtf import FlaskForm
from flask_wtf.file import FileField
from flask_images import Images
from wtforms import TextField, HiddenField, ValidationError, RadioField,\
    BooleanField, SubmitField, PasswordField, FormField, validators
import psycopg2, os
import hashlib


nav = Nav()
app = Flask(__name__, static_url_path='/web/static')
app.secret_key = 'howareyoudoingthisisasecretkeyformyapp'
Material(app)
Images(app)
nav.init_app(app)
app.config['IMAGES_URL'] = ''


#return a connection and cursor for db
def get_database():
    conn = psycopg2.connect("dbname='flask' user='flask' host='db' password='flaskdb'")
    return conn, conn.cursor()
#validator to make sure username doesn't exist
def val_username():
    def _val_username(form, field):
        con, cursor = get_database()
        cursor.execute("""SELECT * FROM public.users WHERE username=%s""", (field.data,)) #checks is username present in db
        if cursor.fetchone():
            con.close()
            raise ValidationError("Username is already taken")
    return _val_username

def val_image(message=u'Images only!', extensions=None):
    if not extensions:
        extensions = ('jpg', 'jpeg', 'png', 'gif')
    def _val_image(form, field):
        if not field.data or field.data.filename.split('.')[-1].lower() not in extensions:
            raise ValidationError(message)
    return _val_image

#Login Form Class with custom validation to check for username/password match:
class LoginForm(FlaskForm): 
    username = TextField('Username', [validators.required()])
    password = PasswordField('Password', [validators.required()])
    submit = SubmitField(label="Log In")
    def validate(self):
        rv = FlaskForm.validate(self)
        if not rv:
            return False
        con, cursor = get_database()
        cursor.execute('SELECT password FROM public.users WHERE username=%s', (self.username.data,))
        check = cursor.fetchone()
        con.close()
        if check == None or (check != None and check[0] != hashlib.sha512(self.password.data.encode()).hexdigest()):
            self.password.errors.append("Incorrect Login")
            return False
        return True

#Register Form Class with custom validation to check for duplicate username:
class RegisterForm(FlaskForm): 
    username = TextField('Username', [val_username(), validators.required()])
    password = PasswordField('Password', [validators.required()])
    submit = SubmitField(label="Create Account")

    def validate(self):
        rv = FlaskForm.validate(self)
        if not rv:
            return False
        return True
#Photo Upload Form
class PhotoForm(FlaskForm):
    photo = FileField('Sample upload', [val_image(), validators.required()])
    caption = TextField('Caption')
    submit_button = SubmitField('Submit Form')
    def validate(self):
        rv = FlaskForm.validate(self)
        if not rv:
            return False
        return True

#Form for editing photo captions
class EditForm(FlaskForm):
    caption = TextField('Caption')
    submit = SubmitField(label='Save')

#Object for working with images
class Image():
    def __init__(self, path, caption, oid=''):
        self.path = path
        self.caption = caption
        self.oid = oid

#Navigation Bar template for logged in user
@nav.navigation()
def user():
    return Navbar(
        '',
        View('Logout', 'logout'),
        View('My Images', 'myimages'),
        View('Upload', 'upload'),
        View('Home', 'home')
    )

#Navigation Bar template for Visitor
@nav.navigation()
def visitor():
    return Navbar(
        '',
        View('Login', 'login'),
        View('Home', 'home')
    )

#Route for logging someone in. Users custom validation and added cookie if login was successful
@app.route('/login', methods=['GET', 'POST'])
def login():
    form = LoginForm()
    if request.method == 'POST' and form.validate_on_submit():
        username = request.values.get('username')
        response = redirect(url_for('home'))
        session['username'] = username #sets username cookie
        return response
    return render_template('login.html', form=form)

#Removes cookie effectively logging a user out
@app.route('/logout', methods=['GET'])
def logout():
    response = redirect(url_for('home'))
    session.pop('username', None)
    return response

#Path to allow a user to register for an account, provided that the username doesn't already exist
@app.route('/register', methods=['GET', 'POST'])
def register():
    form = RegisterForm()
    if request.method == 'POST' and form.validate_on_submit():
        con, cursor = get_database()
        password = hashlib.sha512(request.values.get('password').encode()).hexdigest()
        cursor.execute("""INSERT INTO public.users VALUES(%s, %s)""", (request.values.get('username')
            , password)) #inserts new username and password into the db
        con.commit()
        con.close()
        return redirect(url_for('login'))
    return render_template('register.html', form=form)

#Only available to users, allows them to upload new images using the PhotoForm
@app.route('/upload', methods=['GET','POST'])
def upload():
    form = PhotoForm()
    if request.method == 'POST' and 'username' in session and form.validate_on_submit():
        username = session['username']
        caption = request.values.get('caption')
        con, cursor = get_database()
        image = request.files.get('photo')
        image.save(os.path.join('upload',image.filename))
        new = con.lobject(new_file=os.path.join('upload', image.filename)) #creates a large object in database
        oid = new.oid
        cursor.execute("""INSERT INTO public.images(oid,username,caption) VALUES(%s, %s, %s)""", (oid, username, caption)) #inserts oid for large object in image table
        new.close()
        con.commit()
        con.close()
    return render_template('upload.html', form=form)

#Allows users to edit their captions for an image
@app.route('/edit', methods=['GET', 'POST'])
def edit():
    oid = request.values.get('oid')
    if request.method == 'POST' and 'username' in session:
        new_caption = request.values.get('caption')
        con, cursor = get_database()
        cursor.execute("""UPDATE public.images SET caption=%s WHERE oid=%s""", (new_caption, oid)) #updates image table with new caption
        con.commit()
        con.close()
        return redirect(url_for('myimages'))
    form = EditForm()
    con, cursor = get_database()
    cursor.execute("""SELECT * FROM public.images WHERE oid=%s""", (oid,)) #fetches image info (caption, userna,e)
    result = cursor.fetchone()
    l = con.lobject(int(oid)) #fetches image from db
    path = os.path.join('/web/static/images', str(result[0]))
    l.export(path) #stores image in local storage
    con.close()
    return render_template('edit.html', form=form, image=Image(path, result[2], str(result[0]))) #passes image info and editform to the edit.html view template

#Allows a user to delete their image from the database
@app.route('/delete', methods=['GET'])
def delete():
    oid = request.values.get('oid')
    if oid and 'username' in session:
        con, cursor = get_database()
        cursor.execute("""DELETE FROM public.images WHERE oid=%s""", (oid,)) #deleted image oid from db, markes image ready for deletion
        con.commit()
        con.close()
    return redirect(url_for('myimages'))

#Visitors View for all immages sorted chronologically
@app.route('/')
def home(page=1):
    page, per_page, offset = get_page_args(page_parameter='page',
                                           per_page_parameter='per_page') #pagination info retrieval
    con, cursor = get_database()
    cursor.execute("""SELECT oid,caption FROM public.images ORDER BY timestamp DESC limit %s offset %s""", 
        (per_page, offset)) #fetches all images ordered by time limited by 10 per page and offset by page number
    fetched = cursor.fetchall()
    cursor.execute("""SELECT COUNT(*) FROM public.images""")
    result = cursor.fetchone()
    images = []
    for i in range(0,len(fetched),2): #loops through all retrieved rows
        l = con.lobject(fetched[i][0])
        path1 = os.path.join('/web/static/images', str(fetched[i][0]))
        caption1 = fetched[i][1]
        l.export(path1) #stores image in local storage
        l.close()
        if i + 1 < len(fetched):
            l = con.lobject(fetched[i + 1][0])
            path2 = os.path.join('/web/static/images', str(fetched[i + 1][0]))
            caption2 = fetched[i + 1][1]
            l.export(path2)
            l.close()
            images.append((Image(path1, caption1), Image(path2, caption2))) #creates tuple of 2 Image Class objects (look above for reference) to display 2 images per row
        else:
            images.append((Image(path1, caption1),)) #if total number of images is odd, then the last tuple only has one Image Class object
    con.close()
    username = None
    if 'username' in session:
        username = session['username'] #to see if its a logged in user or a visitor
    pagination = Pagination(page=page, per_page=10, total=int(result[0]), search=False, record_name='images')
    return render_template('home.html', images=images, per_page=10, pagination=pagination, username=username)

#Users View to look at all of their images
#Most of the code is the same as the home function save for the query which also adds the username constraint for fetched items
@app.route('/myimages')
def myimages(page=1):
    username = session['username']
    page, per_page, offset = get_page_args(page_parameter='page',
                                           per_page_parameter='per_page')
    con, cursor = get_database()
    cursor.execute("""SELECT oid,caption FROM public.images WHERE username=%s ORDER BY timestamp DESC limit %s offset %s""", (username, per_page, offset)) #same query as visitor images page but also constrained by username
    fetched = cursor.fetchall()
    cursor.execute("""SELECT COUNT(*) FROM public.images WHERE username=%s""", (username,))
    result = cursor.fetchone()
    images = []
    for i in range(0,len(fetched),2):
        l = con.lobject(fetched[i][0])
        path1 = os.path.join('/web/static/images', str(fetched[i][0]))
        caption1 = fetched[i][1]
        l.export(path1)
        l.close()
        if i + 1 < len(fetched):
            l = con.lobject(fetched[i + 1][0])
            path2 = os.path.join('/web/static/images', str(fetched[i + 1][0]))
            caption2 = fetched[i + 1][1]
            l.export(path2)
            l.close()
            images.append((Image(path1, caption1, str(fetched[i][0])), Image(path2, caption2, str(fetched[i + 1][0]))))
        else:
            images.append((Image(path1, caption1, str(fetched[i][0])),))
    con.close()
    pagination = Pagination(page=page, per_page=10, total=int(result[0]), search=False, record_name='images')
    return render_template('images.html', images=images, per_page=10, pagination=pagination, username=username)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8080, debug=True)
  