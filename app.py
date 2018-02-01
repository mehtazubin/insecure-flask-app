from flask import Flask, render_template, request
from flask_material import Material
from flask_wtf import FlaskForm
from flask_wtf.file import FileField
from wtforms import TextField, HiddenField, ValidationError, RadioField,\
    BooleanField, SubmitField, PasswordField, FormField, validators
from wtforms.validators import Required

APP = Flask(__name__)
Material(APP)
APP.config['SECRET_KEY'] = 'USE-YOUR-OWN-SECRET-KEY-DAMNIT'
APP.config['RECAPTCHA_PUBLIC_KEY'] = 'TEST'

# straight from the wtforms docs:
class TelephoneForm(FlaskForm):
    username = TextField('Username', [validators.required()])
    password = PasswordField('Password', [validators.required()])
    submit = SubmitField(label="Log In")

class ExampleForm(FlaskForm):
    field1 = TextField('First Field', description='This is field one.')
    field2 = TextField('Second Field', description='This is field two.',
                       validators=[Required()])
    hidden_field = HiddenField('You cannot see this', description='Nope')
    radio_field = RadioField('This is a radio field', choices=[
        ('head_radio', 'Head radio'),
        ('radio_76fm', "Radio '76 FM"),
        ('lips_106', 'Lips 106'),
        ('wctr', 'WCTR'),
    ])
    checkbox_field = BooleanField('This is a checkbox',
                                  description='Checkboxes can be tricky.')

    # subforms
    mobile_phone = FormField(TelephoneForm)

    # you can change the label as well
    office_phone = FormField(TelephoneForm, label='Your office phone')

    ff = FileField('Sample upload')

    submit_button = SubmitField('Submit Form')


    def validate_hidden_field(form, field):
        raise ValidationError('Always wrong')

@APP.route('/', methods=['GET', 'POST'])  
def hello_world():
    form = TelephoneForm()
    if request.method == 'POST':
        APP.logger.info(request.values)
    return render_template('login.html', form=form)

if __name__ == '__main__':
    APP.run(debug=True)
  