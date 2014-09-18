#!/usr/bin/python
import os
import sys
import web
import re
import sqlite3 as sqlite

import base
import local
import role
import model
import error_messages

web.config.debug = False

if web.config.debug:
    print('Warning: debug mode can make session data to disappear for no reason.')
    print('We should always set debug to False.')
    print('See http://webpy.org/docs/0.3/sessions')
    sys.exit(1)

def capitalize(string):
    return string[0].upper() + string[1:].lower()

def camel_case(string):
    return ''.join(map(capitalize, string.split('_')))

urls = ['/', 'Home']
for record_name in ['login', 'course', 'user']:
    for request in ['admin', 'add_service', 'add', 'remove']:
        if (record_name, request) == ('login', 'admin'): continue

        url = '/%s/%s' % (record_name, request)
        cls = camel_case('%s_%s' % (record_name, request))
        urls.extend([url, cls])

        options = {}
        if record_name == 'login' and request in ['add_service']:
            options['parent_class'] = base.NoLoginContent

        globals()[cls] = getattr(getattr(model, record_name), 'class_%s' % (request,))(**options)

        ## Example:
        #LoginAddService = model.login.class_add_service(parent_class=base.NoLoginContent)
        #LoginAdd = model.login.class_add()
        #LoginRemove = model.login.class_remove()

urls = tuple(urls)
local.app = web.application(urls, globals())
local.db = web.database(dbn='sqlite', db='_changui.db')
local.store = web.session.DBStore(local.db, 'sessions')
local.session = web.session.Session(local.app, local.store, initializer={'count': 0})

header_menu = [
    ('Cursos', 'CourseAdmin', '/course/admin'),
    ('Usuarios', 'UserAdmin', '/user/admin'),
]

def menu_to_display():
    menu2 = []
    for title, resource, url in header_menu:
        if base.have_permissions_for(globals()[resource]):
            menu2.append((title, url))
    return menu2

local.render = web.template.render('templates', base='layout', globals={
            'menu': menu_to_display,
            'session': local.session,
            'role': role,
            'errmsg': lambda x: error_messages.messages.get(x, ''),
        })

def notfound():
    return web.notfound(local.render.notfound())

local.app.notfound = notfound

class Home(base.Content):
    def request(self):
        return local.render.home()

if __name__ == '__main__':
    if not os.path.exists('_changui.db'):
        print
        print 'File _changui.db does not exist.'
        print 'Run ./dev/create_db.py and retry.'
        print
        sys.exit(1)
    local.app.run()

