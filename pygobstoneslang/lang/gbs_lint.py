#
# Copyright (C) 2011, 2012 Pablo Barenbaum <foones@gmail.com>
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program. If not, see <http://www.gnu.org/licenses/>.
#

import pygobstoneslang.common.position as position
import pygobstoneslang.common.utils as utils
import gbs_builtins
import gbs_constructs
import gbs_type
import gbs_modules
import bnf_parser
from gbs_def_helper import *
import pygobstoneslang.common.i18n as i18n
from pygobstoneslang.common.utils import *

#### Basic semantic checking of Gobstones programs.

## Normalization of identifiers (normalize_id)
#
# Determines which identifiers are identified as the same one
# (mapping identifiers to namespaces).
#
# The kind of a program construct is:
#
#   'callable' for procedures and functions
#   'atomic'   for constants, variables, parameters and indices
#
# The default normalization scheme is:
#
#    return kind, name
#
# Which makes two namespaces.
# For instance, with this scheme:
#    - a function and a variable can have the same name
#      (because they have different kinds)
#    - a variable and an index cannot have the same name
#      (since they are both atomic constructs)
#
# Alternative normalization schemes could be:
#
#    return name
#       # unique namespace: function and variables cannot share names
#
#    return name.lower()
#       # functions and procedures cannot have the same
#       # name (modulo case)
#

def lax_normalize_id(kind, name):
    return kind, name

def strict_normalize_id(kind, name):
    return name.lower()

NORMALIZE_ID = {
    'lax': lax_normalize_id,
    'strict': strict_normalize_id,
}

##
class GbsLintWarning(SourceWarning):
    pass

class GbsLintException(StaticException):
    def error_type(self):
        return i18n.i18n('Semantic error')


def is_variable(toktype):
    return toktype == "variable"

class InvocationGraph(object):

    def __init__(self):
        self.graph = {}
        self.inverse_graph = {}

    def add(self, invoker, invoked):
        self.add_graph(invoker, invoked)
        self.add_inverse(invoker, invoked)

    def add_graph(self, invoker, invoked):
        if not invoker in self.graph.keys():
            self.graph[invoker] = {}
        self.graph[invoker] = invoked

    def add_inverse(self, invoker, invoked):
        if not invoked in self.inverse_graph.keys():
            self.inverse_graph[invoked] = {}
        self.inverse_graph[invoked][invoker] = True

    def invocation_chain_includes(self, invoker, invoked):
        for chain in self.get_invocation_chains(invoker):
            if invoked in chain:
                return True
        return False

    def callers_for(self, name):
        if name in self.inverse_graph.keys():
            return self.inverse_graph[name].keys()
        else:
            return []

    def get_invocation_chains(self, invoker):
        chains = []
        for parent_invoker in self.callers_for(invoker):
            chains += [[invoker] + chain for chain in self.get_invocation_chains(parent_invoker)]
        if len(chains) == 0:
            chains = [[invoker]]
        return chains

    def recursive_invocation(self, invoker, invoked):
        return invoker == invoked or self.invocation_chain_includes(invoker, invoked)

    def get_invocation_chains_with_ancestor(self, invocable, ancestor):
        result = []
        for chain in self.get_invocation_chains(invocable):
            if ancestor in chain:
                result += [chain]
        return result

class SymbolTableManager(object):
    """ Manages a routine symbol table and a variable/index/param
        symbol table in order to generate two different namespaces """
    def __init__(self, normalize_id=lax_normalize_id):
        self.tables = {
            "type_proc" : SymbolTable(normalize_id),
            "rtn"       : SymbolTable(normalize_id),
            "name"      : SymbolTable(normalize_id)
        }
        self.environment_names = []

    def table_for_construct(self, construct):
        if hasattr(construct, "type") and construct.type() in ['procedure', 'type']:
            return self.tables["type_proc"]
        elif hasattr(construct, "type") and construct.type() in ['function', 'entrypoint']:
            return self.tables["rtn"]
        else:
            return self.tables["name"]

    def table_for_type(self, type):
        if type in ['procedure', 'type']:
            return self.tables["type_proc"]
        elif type in ['function', 'entrypoint']:
            return self.tables["rtn"]
        else:
            return self.tables["name"]

    def add(self, construct, area=None, exclusive=True):
        self.table_for_construct(construct).add(construct, area, exclusive)

    def push_env(self, environment_name=None):
        for name, table in self.tables.items():
            table.push_env()
        self.environment_names.append(environment_name)

    def environment_name(self):
        return self.environment_names[-1]

    def pop_env(self):
        for name, table in self.tables.items():
            table.pop_env()
        self.environment_names.pop()

    def is_immutable(self, var):
        return self.tables["name"].is_immutable(var)

    def set_immutable(self, var):
        self.tables["name"].set_immutable(var)

    def unset_immutable(self, var):
        self.tables["name"].unset_immutable(var)

    def get_routine(self, as_kind, name, else_=None):
        return self.tables["rtn"].get(as_kind, name, else_)

    def get_name(self, as_kind, name, else_=None):
        return self.tables["name"].get(as_kind, name, else_)

    def get(self, as_kind, name, else_=None):
        val = self.get_routine(as_kind, name, else_)
        if val is None:
            val = self.get_name(as_kind, name, else_)
            if val is None:
                val = self.tables["type_proc"].get(as_kind, name, else_)
        return val

    def is_defined_as(self, tree, name, as_kind, as_type):
        return self.table_for_type(as_type).is_defined_as(tree, name, as_kind, as_type)

    def check_defined_as(self, tree, name, as_kind, as_type):
        return self.table_for_type(as_type).check_defined_as(tree, name, as_kind, as_type)

    def _error_not_defined(self, tree, name, as_type):
        self.tables["name"]._error_not_defined(tree, name, as_type)

    def all_defined_routine_or_type_names(self):
        all_defined = []
        for name, table in self.tables.items():
            all_defined += table.all_defined_routine_or_type_names()
        return all_defined

    def get_of_possible_types(self, name, as_kind, possible_types):
        rtnval = self.tables["rtn"].get(as_kind, name, None)
        if not rtnval is None and rtnval.type() in possible_types:
            return rtnval
        else:
            return self.tables["name"].get(as_kind, name, None)

    def check_not_defined_or_defined_as(self, tree, name, as_kind, possible_types):
        return self.table_for_construct(self.get_of_possible_types(name, as_kind, possible_types)).check_not_defined_or_defined_as(tree, name, as_kind, possible_types)

    def remove(self, name, kind, type):
        self.table_for_type(type).remove(name, kind)


class SymbolTable(object):
    """Represents a table that maps symbol names to program constructs.
It is case sensitive, but stores the names in normalized form to report
an error if it finds similar symbol names."""
    def __init__(self, normalize_id=lax_normalize_id):
        self.table = {}
        self.ribs = [[]]
        self.immutable = {}
        self.normalize_id = normalize_id

    def add(self, construct, area=None, exclusive=True):
        "Add a construct. Raise an error if it is already defined and exclusive."

        aname, construct = construct.name(), construct.underlying_construct()
        atype = construct.type()
        if area is None:
            area = construct.area()
        lname = self.normalize_id(construct.kind(), aname)
        if lname in self.table and exclusive:
            area = construct.area()
            oname = self.table[lname].name()
            otype = self.table[lname].type()
            if aname == oname:
                l1 = i18n.i18n('Cannot define ' + atype + ' "%s"') % (aname,)
                l2 = i18n.i18n(otype + ' "%s" already defined %s') % (
                                oname, self.table[lname].where())
                raise GbsLintException('\n'.join([l1, l2]), area)
            else:
                msg = i18n.i18n('"%s" is too similar to ' + otype + ' "%s", defined %s') % (
                                aname, oname, self.table[lname].where())
                raise GbsLintException(msg, area)
        elif not lname in self.table:
            self.table[lname] = construct
            self.ribs[-1].append(lname)

    def remove(self, name, kind):
        lname = self.normalize_id(kind, name)
        del self.table[lname]
        self.ribs[-1] = filter(lambda x: x != lname, self.ribs[-1])

    def push_env(self):
        self.ribs.append([])

    def pop_env(self):
        for lname in self.ribs[-1]:
            del self.table[lname]
        self.ribs.pop()

    def set_immutable(self, var):
        self.immutable[var] = 1

    def unset_immutable(self, var):
        del self.immutable[var]

    def is_immutable(self, var):
        return var in self.immutable

    def get(self, kind, name, else_):
        lname = self.normalize_id(kind, name)
        return self.table.get(lname, else_)

    def is_defined_as(self, tree, name, as_kind, as_type):
        "Returns whether name is already defined with the given construct type or not."
        val = self.get(as_kind, name, None)
        if val is None:
            return False
        else:
            return val.type() == as_type and val.name() == name

    def check_defined_as(self, tree, name, as_kind, as_type):
        "Check that a name is already defined with the given construct type."
        val = self.get(as_kind, name, None)
        if val is None:
            self._error_not_defined(tree, name, as_type)
        elif val.type() != as_type or val.name() != name:
            self._error_conflictive_definition(tree, name, as_type, val)
        return val

    def _error_not_defined(self, tree, name, as_type):
        area = position.ProgramAreaNear(tree)
        msg = i18n.i18n(as_type + ' "%s" is not defined') % (name,)
        raise GbsLintException(msg, area)

    def check_not_defined_or_defined_as(self, tree, name, as_kind, possible_types):
        """Check that a name is not defined or, if it is already defined,
           that it has the given construct type."""
        val = self.get(as_kind, name, None)
        if val is None:
            return None
        elif val.type() not in possible_types or val.name() != name:
            self._error_conflictive_definition(tree, name, possible_types[0], val)
        return val

    def _error_conflictive_definition(self, tree, name, as_type, val):
        if val.name() == name:
            area = position.ProgramAreaNear(tree)
            l1 = i18n.i18n('"%s" is not a ' + as_type) % (name,)
            l2 = i18n.i18n(val.type() + ' "%s" defined %s') % (name, val.where())
            raise GbsLintException('\n'.join([l1, l2]), area)
        else:
            area = position.ProgramAreaNear(tree)
            msg = i18n.i18n('"%s" is too similar to ' + val.type() + ' "%s", defined %s') % (
                            name, val.name(), val.where())
            raise GbsLintException(msg, area)

    def all_defined_routine_or_type_names(self):
        rtns = []
        for construct in self.table.values():
            if (isinstance(construct, gbs_constructs.UserConstruct) or
               isinstance(construct, gbs_constructs.BuiltinFieldGetter)):
                rtns.append(construct)
        return rtns



class GbsSemanticChecker(object):

    """Checks semantic correction of Gobstones programs and
    subprograms, given an abstract syntax tree."""

    def __init__(self, strictness='lax', warn=std_warn, explicit_board=None, allow_recursion=True):
        self.warn = warn
        self.strictness = strictness
        self.symbol_table = SymbolTableManager(normalize_id=NORMALIZE_ID[strictness])
        self.type_getters = {}
        self.explicit_board = explicit_board
        self.allow_recursion = allow_recursion
        self.invocation_graph = InvocationGraph()
        self.types = []

    def setup(self, tree):
        if self.explicit_board is None:
            entrypoint_tree = find_def(tree.children[2], is_entrypoint_def)
            self.explicit_board = len(entrypoint_tree.children[2].children) != 0

        gbs_builtins.explicit_builtins = self.explicit_board
        for b in gbs_builtins.get_builtins():
            self.symbol_table.add(b)
        for name, type in gbs_type.BasicTypes.items():
            self.symbol_table.add(gbs_constructs.BuiltinType(name, type))
        self.types += gbs_type.build_types(tree)

    def check_program(self, tree, loaded_modules=[], is_main_program=True):
        self.setup(tree)

        self.loaded_modules = loaded_modules
        self.is_main_program = is_main_program

        self.module_handler = tree.module_handler = gbs_modules.GbsModuleHandler(tree.source_filename, tree.toplevel_filename)
        self.imported_rtns = {}
        imports = tree.children[1].children
        for imp in imports:
            self.check_import(imp)
        defs = tree.children[2]
        self.check_defs(defs)

    """[TODO] Better name """
    def all_defined_routine_or_type_names(self):
        return list(filter(lambda construct: construct.name() not in self.imported_rtns.keys(), self.symbol_table.all_defined_routine_or_type_names()))

    def field_getters_for_type(self, type_name):
        constructs = []
        for field_getter in self.type_getters[type_name]:
            constructs.append(self.symbol_table.get('callable', field_getter))
        return constructs

    def check_import(self, tree):
        mdl_name = tree.children[1].value
        if not self.module_handler.module_exists(mdl_name):
            pos = position.ProgramAreaNear(tree.children[1])
            raise GbsLintException(i18n.i18n('Module %s cannot be found') % (mdl_name,), pos)

        try:
            mdl_tree = self.module_handler.parse_tree(mdl_name)
        except utils.SourceException as exception:
            self.module_handler.reraise(GbsLintException, exception,
                                                      i18n.i18n('Error parsing module %s') % (mdl_name,),
                                                      position.ProgramAreaNear(tree.children[1]))

        if mdl_name in self.loaded_modules:
            pos = position.ProgramAreaNear(tree.children[1])
            raise GbsLintException(i18n.i18n('Recursive modules'), pos)

        mdl_lint = GbsSemanticChecker(strictness=self.strictness, warn=self.warn, explicit_board=self.explicit_board)
        try:
            mdl_lint.check_program(mdl_tree, self.loaded_modules + [mdl_name], is_main_program=False)
        except utils.SourceException as exception:
            self.module_handler.reraise(GbsLintException, exception,
                                                      i18n.i18n('Error linting module %s') % (mdl_name,),
                                                      position.ProgramAreaNear(tree.children[1]))

        import_tokens = tree.children[2].children
        imports = map(lambda imp: imp.value, import_tokens)

        constructs = tree.children[2].children = mdl_lint.all_defined_routine_or_type_names()

        if not (len(imports) == 1 and imports[0] == '*'):
            newcons = []
            imported = []
            for construct in constructs:
                if construct.name() in imports:
                    newcons.append(construct)
                    imported.append(construct.name())
                    if isinstance(construct, gbs_constructs.UserType):
                        newcons.extend(mdl_lint.field_getters_for_type(construct.name()))
            constructs = newcons
            invalid_imports = set(imports).difference(set(imported))
            if len(invalid_imports) > 0:
                import_index = imports.index(invalid_imports[0])
                mdl_lint.symbol_table._error_not_defined(import_tokens[import_index],
                                                         imports[import_index],
                                                         'type or callable')

        for construct in constructs:
            if isinstance(construct, gbs_constructs.BuiltinFieldGetter):
                if not construct.name() in self.imported_rtns:
                    self.symbol_table.add(construct, area=None)
                    self.imported_rtns[construct.name()] = True
            else:
                if construct.name() in self.imported_rtns:
                    pos = position.ProgramAreaNear(construct.identifier())
                    raise GbsLintException(i18n.i18n('%s %%s was already imported' % (construct.type(),)) % (construct.name(),), pos)
                else:
                    self.symbol_table.add(construct, area=position.ProgramAreaNear(construct.identifier()))
                    self.imported_rtns[construct.name()] = True
                    if construct.type() == "type":
                        self.types += filter(lambda x: x.name == construct.name(), mdl_lint.types)

    def check_defs(self, tree):
        if len(tree.children) == 0:
            if self.is_main_program:
                pos = position.ProgramAreaNear(tree)
                raise GbsLintException(i18n.i18n('Empty program'), pos)
        else:
            self._check_EntryPoint(tree)

            for def_ in tree.children:
                self.check_definition1(def_)

            for def_ in tree.children:
               self.check_definition2(def_)

    def _check_EntryPoint(self, tree):
        if not self._check_ProgramEntryPoint(tree) and self.is_main_program:
            pos = position.ProgramAreaNear(tree.children[-1])
            raise GbsLintException(i18n.i18n('There should be an entry point (Main procedure or program block).'), pos)

    def _check_ProgramEntryPoint(self, tree):
        entrypoint_tree = find_def(tree, is_entrypoint_def)
        return entrypoint_tree != None

    def _is_upperid(self, name, tok):
        return tok.type == 'upperid' and tok.value == name

    def _body_has_return(self, body):
        return len(body.children) > 0 and body.children[-1].children[0] == 'return'

    def _return_is_empty(self, return_clause):
        tup = return_clause.children[1].children
        return len(tup) == 0

    def _returns_varTuple(self, return_clause):
        tup = return_clause.children[1].children
        return self._is_varTuple(tup)

    def _is_varTuple(self, tup):
        for x in tup:
            if not self._is_varName(x):
                return False
        return True

    def _is_varName(self, gexp):
        if not gexp.has_children():
            return False
        return gexp.children[0] == 'varName'

    def _add_var(self, varName, tree):
        var = self.symbol_table.check_not_defined_or_defined_as(tree, varName, 'atomic', ['variable', 'index', 'parameter'])
        if var is None:
            self.symbol_table.add(gbs_constructs.UserVariable(varName, tree))
        elif var.type() == 'index':
            msg = i18n.i18n('Cannot modify "%s": index of a foreach/repeatWith/repeat is immutable') % (varName,)
            area = position.ProgramAreaNear(tree)
            raise GbsLintException(msg, area)
        elif var.type() == 'parameter':
            msg = i18n.i18n('Cannot modify "%s": parameter is immutable') % (varName,)
            area = position.ProgramAreaNear(tree)
            raise GbsLintException(msg, area)

    def _add_index(self, varName, tree):
        var = self.symbol_table.check_not_defined_or_defined_as(tree, varName, 'atomic', ['index', 'variable', 'parameter'])
        if var is None:
            self.symbol_table.add(gbs_constructs.UserIndex(varName, tree))
        elif var.type() == 'variable':
            msg = i18n.i18n('Index of a foreach/repeatWith/repeat cannot be a variable: "%s"') % (varName,)
            area = position.ProgramAreaNear(tree)
            raise GbsLintException(msg, area)
        elif var.type() == 'parameter':
            msg = i18n.i18n('Index of a foreach/repeatWith/repeat cannot be a parameter: "%s"') % (varName,)
            area = position.ProgramAreaNear(tree)
            raise GbsLintException(msg, area)

    def _add_readvar(self, varName, tree):
        var = self.symbol_table.check_not_defined_or_defined_as(tree, varName, 'atomic', ['variable', 'parameter', 'index'])
        if var is None:
            self.symbol_table.add(gbs_constructs.UserVariable(varName, tree))

    def _check_nested_indexes(self, varName, tree):
        if self.symbol_table.is_immutable(varName):
            msg = i18n.i18n('Nested foreach/repeatWith/repeat\'s cannot have the same index: "%s"') % (varName,)
            area = position.ProgramAreaNear(tree)
            raise GbsLintException(msg, area)

    def check_definition1(self, tree):
        if is_type_def(tree):
            self.check_type_definition1(tree)
        else:
            self.check_routine_definition1(tree)

    def add_type(self, name, tree):
        self.type_getters[name] = []
        self.symbol_table.check_not_defined_or_defined_as(tree, name, 'atomic', 'type')
        self.symbol_table.add(gbs_constructs.UserType(name, tree))

    def check_type_definition1(self, tree):
        " Visit a type definition and add it to the symbol table."
        _, type_name, type_or_def = tree.children
        self.add_type(type_name.value, tree)
        if type_or_def.children[0] in ['variant']:
            body = type_or_def.children[1]
            for case in body.children:
                fieldcase, cname, cbody = case.children
                if fieldcase != 'case':
                    area = position.ProgramAreaNear(tree)
                    msg = i18n.i18n('Variant body should only contain case declarations.')
                    raise GbsLintException(msg, area)
                self.add_type(cname.value, case)

    def check_routine_definition1(self, tree):
        "Visit a routine definition and add it to the symbol table."
        prfn, name, params, body, typeDecl = tree.children
        name = name.value
        # check parameters and returns
        if prfn == 'procedure':
            self.check_procedure_definition(tree)
        elif is_program_def(tree):
            self.check_entrypoint_definition(tree)
        elif is_interactive_def(tree):
            pass
        else:
            assert prfn == 'function'
            self.check_function_definition(tree)
        # add to the symbol table
        if prfn == 'procedure':
            self.symbol_table.add(gbs_constructs.UserProcedure(name, tree))
        elif prfn == 'function':
            self.symbol_table.add(gbs_constructs.UserFunction(name, tree))
        elif is_program_def(tree):
            self.symbol_table.add(gbs_constructs.UserProgramEntryPoint(name, tree))
        elif is_interactive_def(tree):
            self.symbol_table.add(gbs_constructs.UserInteractiveEntryPoint(name, tree))

    def check_entrypoint_definition(self, tree):
        prfn, name, params, body, typeDecl = tree.children
        if self._body_has_return(body):
            return_clause = body.children[-1]

    def check_procedure_definition(self, tree):
        prfn, name, params, body, typeDecl = tree.children
        if self.explicit_board and tree.annotations["varProc"] is None:
            name = name.value
            area = position.ProgramAreaNear(tree)
            msg = i18n.i18n('procedure "%s" should have a procedure variable') % (name,)
            raise GbsLintException(msg, area)

        if not self.explicit_board and not tree.annotations["varProc"] is None:
            name = name.value
            area = position.ProgramAreaNear(tree)
            msg = i18n.i18n('procedure "%s" should not have a procedure variable') % (name,)
            raise GbsLintException(msg, area)

        if self._body_has_return(body):
            name = name.value
            area = position.ProgramAreaNear(body.children[-1])
            msg = i18n.i18n('procedure "%s" should not have a return') % (name,)
            raise GbsLintException(msg, area)

    def check_function_definition(self, tree):
        prfn, name, params, body, typeDecl = tree.children
        if body.children == []:
            name = name.value
            area = position.ProgramAreaNear(tree)
            msg = i18n.i18n('function body of "%s" cannot be empty') % (name,)
            raise GbsLintException(msg, area)
        elif not self._body_has_return(body):
            name = name.value
            area = position.ProgramAreaNear(body.children[-1])
            msg = i18n.i18n('function "%s" should have a return') % (name,)
            raise GbsLintException(msg, area)
        return_clause = body.children[-1]
        if self._return_is_empty(return_clause):
            name = name.value
            area = position.ProgramAreaNear(body.children[-1])
            raise GbsLintException(i18n.i18n('return from function "%s" must return something') % (name,), area)

    def check_definition2(self, tree):
        if is_type_def(tree):
            self.check_type_definition2(tree)
        else:
            self.check_routine_definition2(tree)

    def check_type_definition2(self, tree):
        "[TODO] Check body of type definition"
        _, type_name, type_or_def = tree.children
        if type_or_def.children[0] == 'record':
            self.check_record_body(type_name, type_or_def.children[1])
        elif type_or_def.children[0] == 'variant':
            """[TODO] Check"""
            self.check_variant_body(type_or_def.children[1])
        elif type_or_def.children[0] == 'type':
            pass
        else:
            assert False

    def check_variant_body(self, body):
        for case in body.children:
            if not case.children[2] is None:
                self.check_record_body(case.children[1], case.children[2])

    def check_record_body(self, type_name, body):
        for field in body.children:
            self.check_type(field.children[2])
            self.add_field_getter_function(type_name, field)

    def add_field_getter_function(self, type_name, field):
        field_name = field.children[1].children[1].value
        self.type_getters[type_name.value].append(field_name)
        func_construct = gbs_constructs.BuiltinFieldGetter(field_name,
                                                                gbs_builtins.TYPE_GETTER_FUNC)
        self.symbol_table.add(func_construct, None, False)

    def check_routine_definition2(self, tree):
        "Check the parameters and body of a routine definition."
        prfn, name, params, body, typeDecl = tree.children
        name = name.value
        self.check_definition_body(prfn, name, params, body)

    def check_definition_body(self, prfn, name, params, tree):
        self.symbol_table.push_env(name)
        # add parameter names to symbol table
        parnames = set_new()
        if len(params.children) > 0:
            inout_var = params.children[0]
            set_add(parnames, inout_var.value)
            if prfn == 'function' or not self.explicit_board:
                self.symbol_table.add(gbs_constructs.UserParameter(inout_var.value, inout_var))
            else:
                self.symbol_table.add(gbs_constructs.UserVariable(inout_var.value, inout_var))
        if len(params.children) > 1:
            for var in params.children[1:]:
                if var.value in parnames:
                    msg = i18n.i18n(prfn + ' "%s" has a repeated parameter: "%s"') % (name, var.value)
                    raise GbsLintException(msg, position.ProgramAreaNear(var))
                set_add(parnames, var.value)
                self.symbol_table.add(gbs_constructs.UserParameter(var.value, var))
        for cmd in tree.children:
            self.check_command(cmd)
        self.symbol_table.pop_env()

    # commands

    def check_invocation(self, invoker_name, invoked_name, area):
        if not self.allow_recursion and self.invocation_graph.recursive_invocation(invoker_name, invoked_name):
            chain = [invoked_name] + self.invocation_graph.get_invocation_chains_with_ancestor(invoker_name, invoked_name)[0]
            chain.reverse()
            raise GbsLintException(i18n.i18n("Recursion is not allowed") + ". " + i18n.i18n("Invocation chain") + ": " + "->".join(chain), area)
        self.invocation_graph.add(invoker_name, invoked_name)

    def check_command(self, tree):
        command = tree.children[0]
        dispatch = {
            'Skip': self.check_Skip,
            'THROW_ERROR': self.check_THROW_ERROR,
            'procCall': self.check_procCall,
            'assignVarName': self.check_assignVarName,
            'assignVarTuple1': self.check_assignVarTuple1,
            'if': self.check_if,
            'case': self.check_case,
            'while': self.check_while,
            'repeat': self.check_repeat,
            'foreach': self.check_foreach,
            'block': self.check_block,
            'return': self.check_return,
        }
        if command in dispatch:
            dispatch[command](tree)
        else:
            msg = i18n.i18n('Unknown command: %s') % (command,)
            area = position.ProgramAreaNear(tree)
            raise GbsLintException(msg, area)

    def check_Skip(self, tree): pass
    def check_THROW_ERROR(self, tree): pass

    def _check_callable(self, callable_type, tree):
        name = tree.children[1]
        self.check_invocation(self.symbol_table.environment_name(), name.value, position.ProgramAreaNear(tree))
        def_ = self.symbol_table.check_defined_as(tree, name.value, 'callable', callable_type)
        self.check_arity(def_, tree)
        self.check_tuple(tree.children[2])
        return def_

    def _check_funcCall(self, tree, ret_arity):
        name = tree.children[1]
        def_ = self._check_callable('function', tree)
        self.check_return_arity(def_, tree, ret_arity)

    def check_procCall(self, tree):
        if self.explicit_board != tree.annotations.get('explicit_board', False):
            raise GbsLintException(i18n.i18n('Can not use passing by reference when using the implicit board.'),
                                   position.ProgramAreaNear(tree))
        self._check_callable('procedure', tree)

    def check_assignVarName(self, tree):
        varName = tree.children[1].children[1].value
        self._add_var(varName, tree)
        self.check_expression(tree.children[3])

    def check_type(self, tree):
        if not tree is None:
            type = tree.children[1]
            self.symbol_table.check_defined_as(type, type.value, 'atomic', 'type')

    def check_assignVarTuple1(self, tree):
        varTuple = tree.children[1].children
        nombres = {}
        for v in varTuple:
            if v.value in nombres:
                area = position.ProgramAreaNear(v)
                msg = i18n.i18n('Repeated variable in assignment: "%s"') % (v.value,)
                raise GbsLintException(msg, area)
            nombres[v.value] = True
            self._add_var(v.value, v)
        self._check_funcCall(tree.children[2], len(varTuple))

    def check_if(self, tree):
        self.check_expression(tree.children[1])
        self.check_block(tree.children[2])
        if tree.children[3] is not None: # check else
            self.check_block(tree.children[3])

    def check_block(self, tree):
        for cmd in tree.children[1].children:
            self.check_command(cmd)

    def check_while(self, tree):
        self.check_expression(tree.children[1])
        self.check_block(tree.children[2])
        self.check_nesting_constrains(tree.children[2])

    def check_case(self, tree):
        self.check_expression(tree.children[1])
        seen = {}
        for branch in tree.children[2].children:
            if branch.children[0] == 'branch':
                for literal in branch.children[1].children:
                    if literal.value in seen:
                        area = position.ProgramAreaNear(literal)
                        raise GbsLintException(i18n.i18n('Literals in a switch should be disjoint'), area)
                    seen[literal.value] = 1
                    self.check_constant_or_typename(literal)
                self.check_block(branch.children[2])
            else: # defaultBranch
                self.check_block(branch.children[1])

    def check_match(self, tree):
        self.check_expression(tree.children[1])
        seen = {}
        for branch in tree.children[2].children:
            if branch.children[0] == 'branch':
                branch_case = branch.children[1]
                if branch_case.value in seen:
                    area = position.ProgramAreaNear(branch_case)
                    raise GbsLintException(i18n.i18n('Constructors in a match should be disjoint'), area)
                seen[branch_case.value] = 1
                self.check_constant_or_typename(branch_case)
                self.check_expression(branch.children[2])
            else: # defaultBranch
                self.check_expression(branch.children[1])

    def check_repeat(self, tree):
        self.check_expression(tree.children[1]) # times
        self.check_block(tree.children[2]) # body
        self.check_nesting_constrains(tree.children[2])

    def check_foreach(self, tree):
        varname = tree.children[1].value
        self._add_index(varname, tree.children[1])
        self._check_nested_indexes(varname, tree.children[1])
        self.symbol_table.set_immutable(varname)
        self.check_expression(tree.children[2]) # list
        self.check_block(tree.children[3]) # body
        self.check_nesting_constrains(tree.children[3])
        self.symbol_table.unset_immutable(varname)
        self.symbol_table.remove(varname, "atomic", "index")

    def check_nesting_constrains(self, block):
        child = recursive_find_node(block, lambda node: node in ["foreach", "while", "repeat"])
        if not child is None:
            raise GbsLintException(i18n.i18n("Repetition nesting is not allowed"), position.ProgramAreaNear(block))


    def check_return(self, tree):
        self.check_tuple(tree.children[1])

    # expressions

    def check_tuple(self, tree):
        for expr in tree.children:
            self.check_expression(expr)

    def check_expression(self, tree):
        exptype = tree.children[0]
        dispatch = {
          'or': self.check_binary_op,
          'and': self.check_binary_op,
          'not': self.check_unary_op,
          'relop': self.check_binary_op,
          'addsub': self.check_binary_op,
          'mul': self.check_binary_op,
          'divmod': self.check_binary_op,
          'pow': self.check_binary_op,
          'listop': self.check_binary_op,
          'varName': self.check_varName,
          'projection' : self.check_binary_op,
          'constructor': self.check_constructor,
          'funcCall': self.check_funcCall,
          'unaryMinus': self.check_unary_op,
          'match': self.check_match,
          'literal': self.check_literal,
          'atom': self.check_atom,
          'type': self.check_type,
        }
        if exptype in dispatch:
            dispatch[exptype](tree)
        else:
            msg = i18n.i18n('Unknown expression: %s') % (exptype,)
            area = position.ProgramAreaNear(tree)
            raise GbsLintException(msg, area)

    def check_unary_op(self, tree):
        self.check_expression(tree.children[1])

    def check_binary_op(self, tree):
        self.check_expression(tree.children[2])
        self.check_expression(tree.children[3])

    def check_constructor(self, tree):
        for child_tree in tree.children[2].children:
            self.check_expression(child_tree)

        def is_field_gen(node):
            if not len(node.children) > 0:
                return False
            if not (isinstance(node.children[0], str) and node.children[0] == 'funcCall'):
                return False
            return (isinstance(node.children[1], bnf_parser.Token)
                    and node.children[1].value == '_mk_field')

        def fstop_search(node):
            if len(node.children) > 0 and node.children[0] == 'constructor':
                self.check_constructor(node)
                return True
            else:
                return False

        fieldgens = collect_nodes_with_stop(tree, tree, is_field_gen, fstop_search)
        field_names = []
        for fieldgen in fieldgens:
            fname, fvalue = fieldgen.children[2].children
            fname = fname.children[1].value
            if not fname in field_names:
                field_names.append(fname)
            else:
                area = position.ProgramAreaNear(tree)
                msg = i18n.i18n('Repeated assignment for field "%s".') % (fname,)
                raise GbsLintException(msg, area)

    def check_varName(self, tree):
        self._add_readvar(tree.children[1].value, tree.children[1])

    def check_funcCall(self, tree):
        self._check_funcCall(tree, 1)

    def check_literal(self, tree):
        self.check_constant_or_typename(tree.children[1])

    def check_atom(self, tree):
        tree.children = tree.children[1].children
        self.check_expression(tree)

    def check_constant_or_typename(self, literal):
        assert literal.type in ['upperid', 'num', 'symbol', 'string']
        if literal.type == 'upperid':
            try:
                self.symbol_table.check_defined_as(literal,literal.value, 'atomic', 'type')
            except GbsLintException as e:
                self.symbol_table.check_defined_as(literal, literal.value, 'atomic', 'constant')

    # auxiliary definitions

    def check_arity(self, def_comp, use_tree):
        if self.strictness == 'lax': return
        prfn = def_comp.type()
        name = def_comp.name()
        params = def_comp.params()
        args = use_tree.children[2].children
        if len(params) != len(args):
            if len(params) < len(args):
                many_few = 'many'
            else:
                many_few = 'few'
            area = position.ProgramAreaNear(use_tree)
            msg = i18n.i18n('Too ' + many_few + ' arguments for ' +
                                            prfn + ' "%s".\n' +
                                            'Expected %i (%s), received %i') % (
                            name,
                            len(params), ', '.join(params), len(args))
            raise GbsLintException(msg, area)

    def check_return_arity(self, def_comp, tree, ret_arity):
        prfn = def_comp.type()
        name = def_comp.name()
        nretvals = def_comp.num_retvals()
        if nretvals != ret_arity:
            area = position.ProgramAreaNear(tree)
            if nretvals == 1:
                                l1 = i18n.i18n('Function "%s" returns one value') % (name,)
            else:
                                l1 = i18n.i18n('Function "%s" returns %i values') % (name, nretvals)
            if ret_arity == 1:
                l2 = i18n.i18n('One value is expected')
            else:
                l2 = i18n.i18n('%i values are expected') % (ret_arity,)
            raise GbsLintException('\n'.join([l1, l2]), area)

# strictness in ['lax', 'strict']
def lint(tree, strictness='lax', allow_recursion=True):
    checker = GbsSemanticChecker(strictness=strictness, allow_recursion=allow_recursion)
    checker.check_program(tree)
    gbs_type.set_user_defined_types(checker.types)
