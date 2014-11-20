#!/usr/bin/python
import sys
sys.path.append('./')

import model
import sqlite3 as sqlite
import getpass

import role

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
        full_name text,
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
    create table role_assignments (
        id integer primary key,
        user_id integer,
        role_id integer
    );
''')

#c.execute('''
#    create table teachers (
#        id integer primary key,
#        course_id integer,
#        user_id integer
#    );
#''')
#
#c.execute('''
#    create table students (
#        id integer primary key,
#        course_id integer,
#        user_id integer
#    );
#''')

ph = model.PasswordHandler()

admin_pass = getpass.getpass('choose password for admin: ')
admin_salt = ph.generate_salt()
c.execute('insert into users (username, pass_salt, pass_hash, full_name, comment) values (?, ?, ?, ?, ?)', (
    u'admin',
    admin_salt.encode('utf-8'),
    ph.hash_password(salt=admin_salt, password=admin_pass).encode('utf-8'),
    u'admin_full_name',
    u'System administrator',
))
admin_user_id = c.lastrowid
for r in [role.course_admin, role.user_admin]:
    c.execute('insert into role_assignments (user_id, role_id) values (?, ?)', (
        admin_user_id,
        r,
    ))
conn.commit()

print 'NB. use sqlite3 command line tool, NOT sqlite'
print 'OK'
