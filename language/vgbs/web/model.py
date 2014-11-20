# coding:utf-8:
import web

import forms
import role
import local

## Login

import hashlib
import random

class PasswordHandler(object):

    def digest(self, string):
        return hashlib.sha256(string).hexdigest()

    def generate_salt(self):
        return self.digest(str(random.getrandbits(256)))

    def hash_password(self, salt, password):
        pepper = 'cc8c9d0fa1ea48b36d4d683eafc6b4976081de75f613a93432f35a907c8525da'
        return self.digest(pepper + '\0' + password + '\0' + salt)

def add_login(data):
    login_user = data['user']
    login_pass = data['pass']
    it = local.db.select('users', where='username=$login_user', vars=locals())
    ph = PasswordHandler()

    try:
        record = it[0]
    except IndexError:
        raise web.seeother('/login/add_service?errmsg=invalid_user_pass')

    if ph.hash_password(salt=record['pass_salt'], password=login_pass) != record['pass_hash']:
        raise web.seeother('/login/add_service?errmsg=invalid_user_pass')

    local.session.username = login_user
    local.session.user_id = record.id
    local.session.logged_in = True
    raise web.seeother('/')

def remove_login(data):
    local.session.username = None
    local.session.user_id = None
    local.session.logged_in = False
    raise web.seeother('/')

login = forms.Record('login',
    fields=[
        forms.Field(
            name='user',
            primary=True,
            description='Usuario (e-mail)',
            #format='^[a-zA-Z0-9]$',
        ),
        forms.PasswordField(
            name='pass',
            description='Contraseña',
        ),
    ],
    add_title='Ingresar',
    add_action=add_login,
    remove_action=remove_login,
)

## Course

course = forms.Record('course',
    table='courses',
    role=role.course_admin,
    fields=[
        forms.Field(
            name='name',
            primary=True,
            description='Nombre del curso',
        ),
        forms.Field(
            name='comment',
            description='Descripción del curso',
        ),
    ],
    add_title='Dar de alta curso',
    admin_title='Administrar cursos',
)

## User

def add_user(data):
    if data['password'] != data['password2']:
        raise web.seeother('/user/add_service?errmsg=pass2_no_match&error_user_password=1&error_user_password2=1')
    if len(data['password']) < 8:
        raise web.seeother('/user/add_service?errmsg=pass_too_short&error_user_password=1&error_user_password2=1')

    ph = PasswordHandler()
    user_pass = data['password']
    user_salt = ph.generate_salt()
    info = {}
    info['username'] = data['username']
    info['pass_salt'] = user_salt.encode('utf-8')
    info['pass_hash'] = ph.hash_password(salt=user_salt, password=user_pass).encode('utf-8')
    info['full_name'] = data['full_name']
    info['comment'] = data['comment']
    local.db.insert('users', **info)
    raise web.seeother('/user/admin')

user = forms.Record('user',
    table='users',
    role=role.user_admin,
    fields=[
        forms.Field(
            name='username',
            primary=True,
            description='Usuario',
        ),
        forms.PasswordField(
            name='password',
            description='Contraseña',
        ),
        forms.PasswordField(
            name='password2',
            description='Reingresar contraseña',
        ),
        forms.Field(
            name='full_name',
            description='Nombre completo',
        ),
        forms.Field(
            name='comment',
            description='Comentarios',
        ),
    ],
    add_title='Crear usuario',
    admin_title='Administrar usuarios',
    add_action=add_user,
)

