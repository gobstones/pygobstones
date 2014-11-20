#!/usr/bin/python
import sys
sys.path.append('./')

import app
import sqlite3 as sqlite
import getpass

conn = sqlite.connect('_changui.db')
c = conn.cursor()

c.execute('''
    create table sessions (
        session_id char(128) UNIQUE NOT NULL,
        atime timestamp NOT NULL default current_timestamp,
        data text
    );
''')

c.execute('''
    create table users (
        id integer primary key,
        username text unique,
        pass_salt text,
        pass_hash text,
        first_name text,
        last_name text,
        comment text
    );
''')

c.execute('''
    create table courses (
        id integer primary key,
        name text unique,
        date_from text,
        date_to text,
        comment text
    );
''')

c.execute('''
    create table sys_admins (
        id integer primary key,
        user_id integer unique
    );
''')

c.execute('''
    create table teachers (
        id integer primary key,
        course_id integer,
        user_id integer
    );
''')

c.execute('''
    create table students (
        id integer primary key,
        course_id integer,
        user_id integer
    );
''')

ph = app.PasswordHandler()

admin_pass = getpass.getpass('choose password for admin: ')
admin_salt = ph.generate_salt()
c.execute('insert into users (username, pass_salt, pass_hash, first_name, last_name, comment) values (?, ?, ?, ?, ?, ?)', (
    u'admin',
    admin_salt.encode('utf-8'),
    ph.hash_password(salt=admin_salt, password=admin_pass).encode('utf-8'),
    u'admin_name',
    u'admin_pass',
    u'System administrator',
))
conn.commit()

print 'NB. use sqlite3 command line tool, NOT sqlite'
print 'OK'
