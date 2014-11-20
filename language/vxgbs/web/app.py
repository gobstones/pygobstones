#!/usr/bin/python
import os
import sys
import random
import hashlib
import web
import sqlite3 as sqlite

class PasswordHandler(object):

    def digest(self, string):
        return hashlib.sha256(string).hexdigest()

    def generate_salt(self):
        return self.digest(str(random.getrandbits(256)))

    def hash_password(self, salt, password):
        pepper = 'cc8c9d0fa1ea48b36d4d683eafc6b4976081de75f613a93432f35a907c8525da'
        return self.digest(pepper + '\0' + password + '\0' + salt)

web.config.debug = False

if web.config.debug:
    print('Warning: debug mode can make session data to disappear for no reason.')
    print('We should always set debug to False.')
    print('See http://webpy.org/docs/0.3/sessions')
    sys.exit(1)

urls = (

    # content that requires NOT to be logged in
    '/login_service', 'LoginService',

    # content that requires login
    '/', 'Home',
    '/problems', 'Problems',

    # actions
    '/login', 'Login',
    '/logout', 'Logout',
)
app = web.application(urls, globals())
db = web.database(dbn='sqlite', db='_changui.db')
store = web.session.DBStore(db, 'sessions')
session = web.session.Session(app, store, initializer={'count': 0})
render = web.template.render('templates', base='layout')

class NoLoginContent(object):
    "Content that requires not to be logged in."
    def GET(self, *args, **kwargs):
        print 'va1', session.get('logged_in', False)
        if session.get('logged_in', False):
            raise web.seeother('/')
        else:
            return self.request(*args, **kwargs)

    def POST(self, *args, **kwargs):
        print 'va2', session.get('logged_in', False)
        return self.GET(*args, **kwargs)

class Content(object):
    "Content that requires login."
    def GET(self, *args, **kwargs):
        print 'va3', session.get('logged_in', False)
        if session.get('logged_in', False):
            return self.request(*args, **kwargs)
        else:
            raise web.seeother('/login_service')

    def POST(self, *args, **kwargs):
        print 'va4', session.get('logged_in', False)
        return self.GET(*args, **kwargs)

class Action(object):
    "Actions."

    def GET(self, *args, **kwargs):
        return self.request(*args, **kwargs)

    def POST(self, *args, **kwargs):
        return self.request(*args, **kwargs)

####

class LoginService(NoLoginContent):
    def request(self):
        default_login_user = web.cookies().get('last_login_user')
        if default_login_user is None:
            default_login_user = ''
        return render.login_form(web.input(), default_login_user)

####

class Home(Content):
    def request(self):
        print 'at home!'
        return render.home()

####

class Login(Action):
    def request(self):
        data = web.input()
        login_user = data.get('login_user', '')
        login_pass = data.get('login_pass', '')
        web.setcookie('last_login_user', login_user)
        it = db.select('users', where='username=$login_user', vars=locals())
        ph = PasswordHandler()

        try:
            record = it[0]
        except IndexError:
            raise web.seeother('/login_service?errmsg=true')

        if ph.hash_password(salt=record['pass_salt'], password=login_pass) != record['pass_hash']:
            raise web.seeother('/login_service?errmsg=true')

        session.logged_in = True
        print 'after login:', session.get('logged_in', False)
        raise web.seeother('/')

class Logout(Action):
    def request(self):
        session.logged_in = False
        raise web.seeother('/')

if __name__ == '__main__':
    if not os.path.exists('_changui.db'):
        print
        print 'File _changui.db does not exist.'
        print 'Run ./dev/create_db.py and retry.'
        print
        sys.exit(1)
    app.run()

