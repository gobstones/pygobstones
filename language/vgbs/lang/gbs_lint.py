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

import common.position
import lang.gbs_builtins
import lang.gbs_constructs
import lang.gbs_modules
from lang.gbs_def_helper import *
import common.i18n as i18n
from common.utils import *

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

class GbsLintException(StaticException):
    def error_type(self):
        return i18n.i18n('Semantic error')

class SymbolTable(object):
    """Represents a table that maps symbol names to program constructs.
It is case sensitive, but stores the names in normalized form to report
an error if it finds similar symbol names."""
    def __init__(self, normalize_id=lax_normalize_id):
        self.table = {}
        self.ribs = [[]]
        self.immutable = {}
        self.normalize_id = normalize_id

    def add(self, construct, area=None):
        "Add a construct. Raise an error if it is already defined."

        aname, construct = construct.name(), construct.underlying_construct()
        atype = construct.type()
        if area is None:
            area = construct.area()
        lname = self.normalize_id(construct.kind(), aname)
        if lname in self.table:
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
        self.table[lname] = construct
        self.ribs[-1].append(lname)

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

    def check_defined_as(self, tree, name, as_kind, as_type):
        "Check that a name is already defined with the given construct type."
        val = self.get(as_kind, name, None)
        if val is None:
            area = common.position.ProgramAreaNear(tree)
            msg = i18n.i18n(as_type + ' "%s" is not defined') % (name,)
            raise GbsLintException(msg, area)
        elif val.type() != as_type or val.name() != name:
            self._error_conflictive_definition(tree, name, as_type, val)
        return val

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
            area = common.position.ProgramAreaNear(tree)
            l1 = i18n.i18n('"%s" is not a ' + as_type) % (name,)
            l2 = i18n.i18n(val.type() + ' "%s" defined %s') % (name, val.where())
            raise GbsLintException('\n'.join([l1, l2]), area)
        else:
            area = common.position.ProgramAreaNear(tree)
            msg = i18n.i18n('"%s" is too similar to ' + val.type() + ' "%s", defined %s') % (
                            name, val.name(), val.where())
            raise GbsLintException(msg, area)

    def all_defined_routine_names(self):
        rtns = []
        for construct in self.table.values():
            if isinstance(construct, lang.gbs_constructs.UserConstruct):
                rtns.append(construct.identifier())
        return rtns

class GbsSemanticChecker(object):
    """Checks semantic correction of Gobstones programs and
subprograms, given an abstract syntax tree."""
    def __init__(self, strictness='lax', warn=std_warn):
        self.warn = warn
        self.strictness = strictness
        self.symbol_table = SymbolTable(normalize_id=NORMALIZE_ID[strictness])
        for b in lang.gbs_builtins.BUILTINS:
            self.symbol_table.add(b)

    def check_program(self, tree, loaded_modules=[], is_main_program=True):
        self.loaded_modules = loaded_modules
        self.is_main_program = is_main_program

        self.module_handler = tree.module_handler = lang.gbs_modules.GbsModuleHandler(tree.source_filename, tree.toplevel_filename)
        self.imported_rtns = {}
        imports = tree.children[1].children
        for imp in imports:
            self.check_import(imp)
        defs = tree.children[2]
        self.check_defs(defs)

    def check_import(self, tree):
        mdl_name = tree.children[1].value
        if not self.module_handler.module_exists(mdl_name):
            pos = common.position.ProgramAreaNear(tree.children[1])
            raise GbsLintException(i18n.i18n('Module %s cannot be found') % (mdl_name,), pos)

        try:
            mdl_tree = self.module_handler.parse_tree(mdl_name)
        except common.utils.SourceException as exception:
            self.module_handler.reraise(GbsLintException, exception,
                                                      common.i18n.i18n('Error parsing module %s') % (mdl_name,),
                                                      common.position.ProgramAreaNear(tree.children[1]))

        if mdl_name in self.loaded_modules:
            pos = common.position.ProgramAreaNear(tree.children[1])
            raise GbsLintException(i18n.i18n('Recursive modules'), pos)

        mdl_lint = GbsSemanticChecker(strictness=self.strictness, warn=self.warn)
        try:
            mdl_lint.check_program(mdl_tree, self.loaded_modules + [mdl_name], is_main_program=False)
        except common.utils.SourceException as exception:
            self.module_handler.reraise(GbsLintException, exception,
                                                      common.i18n.i18n('Error linting module %s') % (mdl_name,),
                                                      common.position.ProgramAreaNear(tree.children[1]))

        rtns = tree.children[2].children

        if len(rtns) == 1 and rtns[0].value == '<all>':
            rtns = tree.children[2].children = mdl_lint.symbol_table.all_defined_routine_names()

        for rtn in rtns:
            if rtn.type == 'lowerid':
                callable_type = 'function'
            else:
                callable_type = 'procedure'

            if rtn.value == 'Main':
                pos = common.position.ProgramAreaNear(rtn)
                raise GbsLintException(i18n.i18n('Cannot import Main procedure'), pos)

            mdl_lint.symbol_table.check_defined_as(rtn, rtn.value, 'callable', callable_type)
            construct = mdl_lint.symbol_table.get('callable', rtn.value, None)

            if rtn.value in self.imported_rtns:
                pos = common.position.ProgramAreaNear(rtn)
                raise GbsLintException(i18n.i18n('%s %%s was already imported' % (callable_type,)) % (rtn.value,), pos)
            self.imported_rtns[rtn.value] = True

            self.symbol_table.add(construct, area=common.position.ProgramAreaNear(rtn))

    def check_defs(self, tree):
        if len(tree.children) == 0:
            if self.is_main_program:
                pos = common.position.ProgramAreaNear(tree)
                raise GbsLintException(i18n.i18n('Empty program'), pos)
        else:
            self._check_EntryPoint(tree)        
            
            for def_ in tree.children:
                self.check_definition1(def_)           

            for def_ in tree.children:
               self.check_definition2(def_)      

    def _check_EntryPoint(self, tree):
        if not self._check_ProgramEntryPoint(tree) and self.is_main_program:
            pos = common.position.ProgramAreaNear(tree.children[-1])
            raise GbsLintException(i18n.i18n('There should be a "program" block.'), pos)            
    
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
            self.symbol_table.add(lang.gbs_constructs.UserVariable(varName, tree))
        elif var.type() == 'index':
            msg = i18n.i18n('Cannot modify "%s": index of a foreach is immutable') % (varName,)
            area = common.position.ProgramAreaNear(tree)
            raise GbsLintException(msg, area)
        elif var.type() == 'parameter':
            msg = i18n.i18n('Cannot modify "%s": parameter is immutable') % (varName,)
            area = common.position.ProgramAreaNear(tree)
            raise GbsLintException(msg, area)

    def _add_index(self, varName, tree):
        var = self.symbol_table.check_not_defined_or_defined_as(tree, varName, 'atomic', ['index', 'variable', 'parameter'])
        if var is None:
            self.symbol_table.add(lang.gbs_constructs.UserIndex(varName, tree))
        elif var.type() == 'variable':
            msg = i18n.i18n('Index of a foreach cannot be a variable: "%s"') % (varName,)
            area = common.position.ProgramAreaNear(tree)
            raise GbsLintException(msg, area)
        elif var.type() == 'parameter':
            msg = i18n.i18n('Index of a foreach cannot be a parameter: "%s"') % (varName,)
            area = common.position.ProgramAreaNear(tree)
            raise GbsLintException(msg, area)

    def _add_readvar(self, varName, tree):
        var = self.symbol_table.check_not_defined_or_defined_as(tree, varName, 'atomic', ['variable', 'parameter', 'index'])
        if var is None:
            self.symbol_table.add(lang.gbs_constructs.UserVariable(varName, tree))

    def _check_nested_indexes(self, varName, tree):
        if self.symbol_table.is_immutable(varName):
            msg = i18n.i18n('Nested foreach\'s cannot have the same index: "%s"') % (varName,)
            area = common.position.ProgramAreaNear(tree)
            raise GbsLintException(msg, area)

    def check_definition1(self, tree):
        "Visit a definition and add it to the symbol table."
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
            assert prfn == 'function' and name != 'Main'
            self.check_function_definition(tree)
        # add to the symbol table
        if prfn == 'procedure':
            self.symbol_table.add(lang.gbs_constructs.UserProcedure(name, tree))
        elif prfn == 'function':
            self.symbol_table.add(lang.gbs_constructs.UserFunction(name, tree))
        elif is_program_def(tree):
            self.symbol_table.add(lang.gbs_constructs.UserProgramEntryPoint(name, tree))
        elif is_interactive_def(tree):
            self.symbol_table.add(lang.gbs_constructs.UserInteractiveEntryPoint(name, tree))

    def check_entrypoint_definition(self, tree):
        prfn, name, params, body, typeDecl = tree.children
        if self._body_has_return(body):
            return_clause = body.children[-1]
            
    def check_procedure_definition(self, tree):
        prfn, name, params, body, typeDecl = tree.children
        if self._body_has_return(body):
            name = name.value
            area = common.position.ProgramAreaNear(body.children[-1])
            msg = i18n.i18n('procedure "%s" should not have a return') % (name,)
            raise GbsLintException(msg, area)

    def check_function_definition(self, tree):
        prfn, name, params, body, typeDecl = tree.children
        if body.children == []:
            name = name.value
            area = common.position.ProgramAreaNear(tree)
            msg = i18n.i18n('function body of "%s" cannot be empty') % (name,)
            raise GbsLintException(msg, area)
        elif not self._body_has_return(body):
            name = name.value
            area = common.position.ProgramAreaNear(body.children[-1])
            msg = i18n.i18n('function "%s" should have a return') % (name,)
            raise GbsLintException(msg, area)
        return_clause = body.children[-1]
        if self._return_is_empty(return_clause):
            name = name.value
            area = common.position.ProgramAreaNear(body.children[-1])
            raise GbsLintException(i18n.i18n('return from function "%s" must return something') % (name,), area)

    def check_definition2(self, tree):
        "Check the parameters and body of a definition."
        prfn, name, params, body, typeDecl = tree.children
        name = name.value
        self.check_definition_body(prfn, name, params, body)
    
    def check_definition_body(self, prfn, name, params, tree):
        self.symbol_table.push_env()
        # add parameter names to symbol table
        parnames = set_new()
        for var in params.children:
            if var.value in parnames:
                msg = i18n.i18n(prfn + ' "%s" has a repeated parameter: "%s"') % (name, var.value)
                raise GbsLintException(msg, common.position.ProgramAreaNear(var))
            set_add(parnames, var.value)
            self.symbol_table.add(lang.gbs_constructs.UserParameter(var.value, var))
        for cmd in tree.children:
            self.check_command(cmd)
        self.symbol_table.pop_env()
        
    # commands

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
            area = common.position.ProgramAreaNear(tree)
            raise GbsLintException(msg, area)

    def check_Skip(self, tree): pass
    def check_THROW_ERROR(self, tree): pass

    def _check_callable(self, callable_type, tree):
        name = tree.children[1]
        def_ = self.symbol_table.check_defined_as(tree, name.value, 'callable', callable_type)
        self.check_arity(def_, tree)
        self.check_tuple(tree.children[2])
        return def_

    def _check_funcCall(self, tree, ret_arity):
        name = tree.children[1]
        def_ = self._check_callable('function', tree)
        self.check_return_arity(def_, tree, ret_arity)

    def check_procCall(self, tree):
        self._check_callable('procedure', tree)

    def check_assignVarName(self, tree):
        varName = tree.children[1].value
        self._add_var(varName, tree)
        self.check_expression(tree.children[2])

    def check_assignVarTuple1(self, tree):
        varTuple = tree.children[1].children
        nombres = {}
        for v in varTuple:
            if v.value in nombres:
                area = common.position.ProgramAreaNear(v)
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

    def check_case(self, tree):
        self.check_expression(tree.children[1])
        seen = {} 
        for branch in tree.children[2].children:
            if branch.children[0] == 'branch':
                for literal in branch.children[1].children:
                    if literal.value in seen:
                        area = common.position.ProgramAreaNear(literal)
                        raise GbsLintException(i18n.i18n('Literals in a switch should be disjoint'), area)
                    seen[literal.value] = 1
                    self.check_constant(literal)
                self.check_block(branch.children[2])
            else: # defaultBranch
                self.check_block(branch.children[1])

    def check_repeat(self, tree):
        self.check_expression(tree.children[1]) # times
        self.check_block(tree.children[2]) # body

    def check_foreach(self, tree):
        varname = tree.children[1].value
        self._add_index(varname, tree.children[1])
        self._check_nested_indexes(varname, tree.children[1])
        self.symbol_table.set_immutable(varname)
        for child in tree.children[2].children[1:]:
            if not child is None:
                self.check_expression(child)        
        self.check_block(tree.children[3]) # body
        self.symbol_table.unset_immutable(varname)

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
          'varName': self.check_varName,
          'funcCall': self.check_funcCall,
          'unaryMinus': self.check_unary_op,
          'literal': self.check_literal,
          'atom': self.check_atom,
        }
        if exptype in dispatch:
            dispatch[exptype](tree)
        else:
            msg = i18n.i18n('Unknown expression: %s') % (exptype,)
            area = common.position.ProgramAreaNear(tree)
            raise GbsLintException(msg, area)

    def check_unary_op(self, tree):
        self.check_expression(tree.children[1])

    def check_binary_op(self, tree):
        self.check_expression(tree.children[2])
        self.check_expression(tree.children[3])

    def check_varName(self, tree):
        self._add_readvar(tree.children[1].value, tree.children[1])

    def check_funcCall(self, tree):
        self._check_funcCall(tree, 1)

    def check_literal(self, tree):
        self.check_constant(tree.children[1])

    def check_atom(self, tree):
        tree.children = tree.children[1].children
        self.check_expression(tree)

    def check_constant(self, literal):
        assert literal.type in ['upperid', 'num']
        if literal.type == 'upperid':
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
            area = common.position.ProgramAreaNear(use_tree)
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
            area = common.position.ProgramAreaNear(tree)
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
def lint(tree, strictness='lax'):
    GbsSemanticChecker(strictness=strictness).check_program(tree)

