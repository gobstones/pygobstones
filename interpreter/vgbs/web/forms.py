import web

import base
import local

def orNone(a, b):
    if a is None:
        return b
    return a

class Field(object):

    def __init__(self, name, description, primary=False, validator=None):
        self.name = name
        self.primary = primary
        self.description = description
        if validator == None:
            validator = lambda *args: (True, '')
        self.validator = validator
        self.record = None # yet

    def full_name(self):
        return self.record.record_name + '_' + self.name

    def validate(self, value):
        return self.validator(value)

    def html_input(self, default_values): 
        return "<input type='text' id='%s' name='%s' value='%s'>" % (
                    self.full_name(),
                    self.full_name(),
                    default_values.get(self.full_name(), '')
        )

class PasswordField(Field):
    def __init__(self, *args, **kwargs):
        Field.__init__(self, *args, **kwargs)

    def validate(self, value):
        #if len(value) < 8:
        #    return False, 'pass_too_short'
        return True, ''

    def html_input(self, default_values): 
        return "<input type='password' id='%s' name='%s'>" % (
                    self.full_name(),
                    self.full_name(),
        )

class Record(object):

    def __init__(self, record_name,
                        table=None, fields=[],
                        role=None,
                        add_title=None,
                        admin_title=None,
                        add_action=None,
                        remove_action=None):
        self.record_name = record_name
        self.table = table
        self.fields = fields
        self.add_action = add_action
        self.remove_action = remove_action

        self.primary_key = None
        self._check_primary_key()

        for field in self.fields:
            field.record = self

        self.role = role

        self.add_title = orNone(add_title, 'Dar de alta %s' % (self.record_name,))
        self.admin_title = orNone(admin_title, 'Administrar %s' % (self.record_name,))

    def all_elements(self):
        if self.table is None:
            return []
        return local.db.select(self.table)

    def _check_primary_key(self):
        nprimary = 0
        for field in self.fields:
            if field.primary:
                nprimary += 1
                self.primary_key = field
        if nprimary != 1:
            raise Exception('Warning: %s should have exactly one primary key' % (
                                self.record_name)
            )

    def class_admin(self, parent_class=base.Content):
        metaself = self
        class C(parent_class):
            role_required = self.role
            def request(self):
                "Main administration page."
                return local.render.admin_list(
                    record=metaself,
                )
        return C

    def class_add_service(self, parent_class=base.Content):
        metaself = self
        class C(parent_class):
            role_required = self.role
            def request(self):
                "Render the form for creating instances of this record."
                cookies = web.cookies()
                input = web.input()

                # get the default value for each field
                # from the cookies
                default_values = {}
                for field in metaself.fields:
                    default = cookies.get('last_' + field.full_name(), None)
                    if default is None:
                        default = ''
                    default_values[field.full_name()] = default

                if input.get('errfield', False):
                    focus_on = input.errfield
                else:
                    focus_on = metaself.fields[0].full_name()

                return local.render.add_form(
                    input=web.input(),
                    action='/%s/add' % (metaself.record_name,),
                    description=metaself.add_title,
                    fields=metaself.fields,
                    default_values=default_values,
                    focus=focus_on
                )
        return C

    def class_add(self, parent_class=base.Action):
        metaself = self
        class C(parent_class):
            role_required = self.role
            def request(self):
                "Add an instance of this record."
                data = web.input()

                # Check that the values for each field are valid
                bad_fields = []
                errmsg = False
                any_error = False
                dictionary = {}
                for field in metaself.fields:
                    value = data.get(field.full_name())
                    dictionary[field.name] = value
                    web.setcookie('last_' + field.full_name(), value)

                    ok, message = field.validate(value)
                    if not ok:
                        any_error = True
                        bad_fields.append('error_' + field.full_name())
                        if not errmsg:
                            errmsg = message

                if any_error:
                    raise web.seeother('/%s/add_service?errmsg=%s%s' % (
                        metaself.record_name,
                        errmsg,
                        ''.join(['&%s=1' % (f,) for f in bad_fields])
                    ))

                if metaself.table is not None:
                    # Check that there are no repeated keys
                    primary_value = dictionary[metaself.primary_key.name]
                    it = local.db.query('select count(*) as total from ' + metaself.table + \
                                        ' where ' + metaself.primary_key.name + '=$primary_value',
                                        vars=locals())
                    if it[0].total > 0:
                        raise web.seeother('/%s/add_service?errmsg=already_exists&error_%s=1' % (
                            metaself.record_name,
                            metaself.primary_key.full_name()
                        ))

                if metaself.table is not None and metaself.add_action is None:
                    local.db.insert(metaself.table, **dictionary)

                if metaself.add_action is not None:
                    metaself.add_action(dictionary)
                else:
                    raise web.seeother('/%s/admin' % (metaself.record_name,))

        return C

    def class_remove(self, parent_class=base.Action):
        metaself = self
        class C(parent_class):
            role_required = self.role
            def request(self):
                dictionary = {}
                if metaself.remove_action is not None:
                    metaself.remove_action(dictionary)

        return C
