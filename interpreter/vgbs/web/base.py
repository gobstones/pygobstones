"Base classes for services."

import web

import local

def have_role(role_id):
    "Return True iff the currently logged user has the given role."
    user_id = local.session.user_id
    it = local.db.select('role_assignments',
              where='user_id=$user_id AND role_id=$role_id',
              vars=locals()
    )
    try:
        record = it[0]
        return True
    except IndexError:
        return False

def have_permissions_for(class_):
    if not local.session.get('logged_in', False):
        return False
    return have_role(class_.role_required)

class NoLoginContent(object):
    "Content that requires not to be logged in."

    def GET(self, *args, **kwargs):
        if local.session.get('logged_in', False):
            raise web.seeother('/')
        else:
            return self.request(*args, **kwargs)

    def POST(self, *args, **kwargs):
        return self.GET(*args, **kwargs)

class CheckRole(object):
    "Mixin to check that a user has a role."

    def check_role(self):
        role_required = getattr(self.__class__, 'role_required', None)
        if role_required is not None:
            if not have_permissions_for(self.__class__):
                raise notfound()

class Content(CheckRole):
    "Content that requires login."

    def GET(self, *args, **kwargs):
        self.check_role()
        if local.session.get('logged_in', False):
            return self.request(*args, **kwargs)
        else:
            raise web.seeother('/login/add_service')

    def POST(self, *args, **kwargs):
        return self.GET(*args, **kwargs)

class Action(CheckRole):
    "Action."

    def GET(self, *args, **kwargs):
        self.check_role()
        return self.request(*args, **kwargs)

    def POST(self, *args, **kwargs):
        self.check_role()
        return self.request(*args, **kwargs)

