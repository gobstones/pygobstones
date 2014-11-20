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


"""This module provides functions that implement type inference
for Gobstones ASTs."""

import lang.gbs_type
from lang.gbs_type import print_type
import lang.gbs_builtins
import common.position
import common.i18n as i18n

from lang.gbs_def_helper import *

#from common.utils import *
from common.utils import (
    StaticException,
    set_new, set_add,
)

def _type_name(node):
    node_name = node.children[1].value
    if len(node.children) > 2:
        output_name = node_name + "("
        for inner_type in node.children[2].children: 
         output_name += _type_name(inner_type)
        return output_name + ")"
    else:
        return node_name

class GbsTypeInferenceException(StaticException):
    "Base class for type inferrer exceptions."

    def error_type(self):
        "Return the error type of these exceptions."
        return i18n.i18n('Type error')

class GbsTypeInference(object):
    "Infer types and decorate Gobstones programs with type annotations."

    def __init__(self, enable_errors):
        self.ribs = [set_new()]
        self.global_context = {}
        self.context = {}
        self.init_builtins()
        self.enable_errors = enable_errors

    def error(self, exception):
        if self.enable_errors:
            raise exception
        else:
            print exception.msg

    def init_builtins(self):
        "Initialize a global context with types for all the builtins."
        for b in lang.gbs_builtins.get_builtins():
            bname, b = b.name(), b.underlying_construct()
            set_add(self.ribs[0], b.name())
            self.global_context[b.name()] = b.gbstype()
        
        for type_name, gbs_type in lang.gbs_type.BasicTypes.items():            
            self.global_context[type_name] = gbs_type()

    def push_env(self):
        "Push an empty environment into the stack of environment ribs."
        self.ribs.append(set_new())

    def pop_env(self):
        "Pop the top environment from the stack of environment ribs."
        for name in self.ribs[-1]:
            del self.context[name]
        self.ribs.pop()

    def _add_var_with_offset(self, var, offsets, new_type=None):
        """Add a variable with it's offset to the context with the given
        type, checking that is consistent with the types it might already
        have."""
        pass

    def _add_var(self, token, new_type=None):
        """Add a variable to the context with the given type, checking
        that it is consistent with the types it might already have."""
        if new_type is None: # fresh
            new_type = lang.gbs_type.GbsTypeVar()
        varname = token.value
        if varname in self.ribs[-1]:
            old_type = self.context[varname]
            lang.gbs_type.unify(new_type, old_type)
        else:
            self.context[varname] = new_type
            set_add(self.ribs[-1], varname)
        return new_type

    def infer_program(self, tree):
        "Infer the type of a program."
        self.module_handler = tree.module_handler
        for mdl_name, mdl_tree in self.module_handler.parse_trees():
            mdl_infer = GbsTypeInference(self.enable_errors)
            try:
                mdl_infer.infer_program(mdl_tree)
            except StaticException as exception:
                self.module_handler.reraise(
                    GbsTypeInferenceException,
                    exception,
                    common.i18n.i18n(
                        'Error typechecking module %s'
                    ) % (
                        mdl_name,
                    ),
                    common.position.ProgramAreaNear(tree.children[1]))
            self.module_handler.set_type_context(
                mdl_name, mdl_infer.global_context)
        imports = tree.children[1].children
        self.infer_imports(imports)
        defs = tree.children[2]
        self.infer_defs(defs)

    def infer_imports(self, imports):
        """Add the types of all the imported routines and imported types
        to the global context."""
        for imp in imports:
            mdl_name = imp.children[1].value
            imported_defs = imp.children[2].children
            for imported_def in imported_defs:
                self.global_context[imported_def.value] = self.module_handler.type_of(mdl_name, 
                                                                                      imported_def.value)

    def infer_defs(self, tree):
        "Infer the type of a list of definitions."
        for def_ in type_defs(tree):
            self.initialize_def(def_)
        for def_ in type_defs(tree):
            self.infer_type_def(def_)
        for def_ in type_defs(tree):    
            self.infer_type_def2(def_)
            
        for def_ in routine_defs(tree):
            self.initialize_def(def_)
        for def_ in routine_defs(tree):
            self.infer_routine_def(def_)

    def initialize_def(self, tree):
        """Initialize the types of all the toplevel definitions 
        in a file."""
        if is_type_def(tree):
            self.initialize_type_def(tree)
        else:
            self.initialize_routine_def(tree)

    def initialize_routine_def(self, tree):
        """Routines are initialized with fresh types.
        For instance, given "function f(x1, x2) {...}", the
        identifier "f" is initialized with type (s1 x s2) -> s3,
        where s1, s2 and s3 are fresh type variables."""
        tok = get_def_name(tree)
        params = lang.gbs_type.GbsTypeVar()
        
        type_decl = get_def_type_decl(tree)
        if type_decl is not None:
            t = lang.gbs_type.parse_type_declaration(type_decl, self.global_context)
        elif is_def_keyword(tree, 'procedure'):
            t = lang.gbs_type.GbsProcedureType(params)
        elif is_entrypoint_def(tree):
            t = lang.gbs_type.GbsEntryPointType()        
        else:
            t = lang.gbs_type.GbsFunctionType(params,
                                              lang.gbs_type.GbsTypeVar())
        self.global_context[tok.value] = t

    def initialize_type_def(self, tree):
        """ Initializes User-Defined Type """        
        _, name, type_or_def = tree.children
        if type_or_def.children[0] == 'variant':
            t = lang.gbs_type.GbsVariantType(name.value)
        elif type_or_def.children[0] == 'record':
            t = lang.gbs_type.GbsRecordType(name.value)
        elif type_or_def.children[0] == 'type':
            t = lang.gbs_type.GbsTypeAlias(name.value)
        else:            
            assert False
        self.add_type(name.value, t)
    
    def add_type(self, name, type):
        self.global_context[name] = type
    
    def infer_routine_def(self, tree):
        """Infer the type of a definition (either a function or a procedure).
        Needed? Or already known on initialization?"""
        prfn, name, params, body, type_decl = unpack_definition(tree)
        self.push_env()
        for p in params.children:
            self._add_var(p)
        self.infer_commands(body)
        self._set_routine_definition_type(tree, prfn, name, params, body)
        #self._debug(tree)
        self.pop_env()

    def infer_record_type(self, body):
        fields = {}
        for field in body.children:
            _, fname, ftype = field.children
            fname = fname.children[1]
            ftype = self.infer_type(ftype)
            fields[fname.value] = ftype
            self.global_context[fname.value] = lang.gbs_builtins.TYPE_GETTER_FUNC
        return fields 

    def infer_type_def(self, tree):
        "Infer the type of a type definition (alias/variant/record)"
        _, name, type_or_def = tree.children
        self.push_env()
        if type_or_def.children[0] == 'record':
            fields = self.infer_record_type(type_or_def.children[1])
            self.global_context[name.value].fields = fields
        elif type_or_def.children[0] == 'variant':
            self.infer_variant_type(name.value, type_or_def.children[1])
        elif type_or_def.children[0] == 'type':
            type = self.infer_type(type_or_def)
            self.global_context[name.value].alias_of = type
        else:
            assert False
        self.pop_env()
        
    def infer_type_def2(self, tree):
        "Infer the type of variant cases"
        _, name, type_or_def = tree.children
        self.push_env()
        if type_or_def.children[0] == 'variant':
            self.infer_variant_type_cases(name.value, type_or_def.children[1])
        self.pop_env()
    
    def infer_variant_type(self, variant_name, body):
        variant = self.global_context[variant_name]
        for case in body.children:
            _, cname, cbody = case.children
            fields = {}
            if not cbody is None:
                fields = self.infer_record_type(cbody)
            variant.cases[cname.value] = lang.gbs_type.GbsRecordType(cname.value, fields)
            
    def infer_variant_type_cases(self, variant_name, body):
        variant = self.global_context[variant_name]
        for case in body.children:
            _, cname, cbody = case.children
            ct = variant.instantiate()
            ct.is_case = cname.value
            self.add_type(cname.value, ct) 
    
    def infer_type(self, node):
        "Infer types"
        """[TODO] Check """
        if node is None:
            return lang.gbs_type.GbsTypeVar()
        else:
            type = node.children[1]
            if len(node.children) > 2:
                inner_types = [self.infer_type(inner_type) for inner_type in node.children[2].children]
                return lang.gbs_type.ComposedTypes[type.value](*inner_types)
            else:
                type_parts = type.value.split("::")
                if len(type_parts) > 1:
                    type_name = type_parts[1]
                else:
                    type_name = type_parts[0]
                type_class = self.global_context[type_name]
                if len(type_parts) == 1 and isinstance(type_class, lang.gbs_type.GbsVariantType):
                    type.value = type_class.name + "::" + type.value
                return type_class
        
    def _debug(self, tree):
        print()
        print('DEF', tree.children[0], tree.children[1].value)
        d2 = {}
        for k, v in self.global_context.items():
            if k not in lang.gbs_builtins.BUILTIN_NAMES:
                d2[k] = v
        print('   Global_ctx:', d2)
        print('   Local_ctx :', self.context)

    def _set_routine_definition_type(self, tree, prfn, name, params, body):
        """Given a context with types for the parameters and local
        variables in a routine, build the type for this routine
        and unify it with its type in the global context.
        For instance if the function "f" has a parameter "x",
        and returns an expression, take the type "s" for "x"
        from the local context, the type "t" for the returned
        expression. Build the type "s -> t" for the function
        and unify that with any type information previously
        known for "f". This requires that the body of the routine
        has already been typechecked."""
        param_types = []
        for p in params.children:
            param_types.append(self.context[p.value])
        param_types = lang.gbs_type.GbsTupleType(param_types)
        if prfn == 'procedure':
            def_type = lang.gbs_type.GbsProcedureType(param_types)
        elif prfn == 'function':
            return_types = self._return_type(prfn, name, params, body)
            def_type = lang.gbs_type.GbsFunctionType(param_types, return_types)
        elif prfn == 'entrypoint' and (name.value == 'program' or name.value == 'interactive'):
            def_type = lang.gbs_type.GbsEntryPointType()
        else:
            assert False
        expected = self.global_context[name.value].instantiate()
        try:
            lang.gbs_type.unify(expected, def_type)
            if prfn == 'function': #[TODO] Check
                freevars = def_type.freevars()
                if len(freevars) > 0:
                    def_type = lang.gbs_type.GbsForallType(freevars, def_type)
                    self.global_context[name.value] = def_type
            tree.type_annot = def_type
        except lang.gbs_type.UnificationFailedException as e:
            area = common.position.ProgramAreaNear(tree)
            if prfn == 'procedure':
                msg = i18n.i18n(
                          'procedure "%s" should take: %s\n' +
                          'But takes: %s'
                      ) % (
                          name.value,
                          expected.paramtype(),
                          def_type.paramtype()
                      )
            else:
                msg = i18n.i18n(
                          'function "%s" should take: %s and return: %s\n' +
                          'But takes: %s and returns: %s'
                      ) % (
                          name.value,
                          expected.paramtype(), expected.restype(),
                          def_type.paramtype(), def_type.restype()
                      )
            self.error(GbsTypeInferenceException(msg, area))

    def _return_type(self, prfn, name, params, body):
        """Return the type annotation for the expression
        returned by the given routine. This requires that
        the given routine has already been typechecked."""
        if len(body.children) == 0:
            return None
        last_command = body.children[-1]
        if last_command.children[0] != 'return':
            return None
        return_type = body.children[-1].type_annot
        return return_type

    def infer_commands(self, tree):
        """Infer types for a sequence of commands, adding
        typing information to the local context if necessary."""
        for cmd in tree.children:
            self.infer_cmd(cmd)

    def infer_cmd(self, tree):
        """Infer types for a command, adding typing information
        to the local context if necessary."""
        command = tree.children[0]
        dispatch = {
            'Skip': self.infer_skip,
            'THROW_ERROR': self.infer_boom,
            'procCall': self.infer_proc_call,
            'assignVarName': self.infer_assign_var_name,
            'assignVarTuple1': self.infer_assign_var_tuple1,
            'if': self.infer_if,
            'case': self.infer_case,
            'while': self.infer_while,
            'repeat': self.infer_repeat,
            'repeatWith': self.infer_repeat_with,
            'foreach': self.infer_foreach,
            'block': self.infer_block,
            'return': self.infer_return,
        }
        assert command in dispatch
        dispatch[command](tree)

    def infer_skip(self, tree):
        "Infer types for a Skip command."
        pass

    def infer_boom(self, tree):
        "Infer types for a THROW_ERROR command."
        pass

    def infer_proc_call(self, tree):
        "Infer types for a procedure call."
        proc_name = tree.children[1].value
        proc_type = self.global_context[proc_name].instantiate()
        arg_type = self.infer_tuple(tree.children[2])
        expected = lang.gbs_type.GbsProcedureType(arg_type)
        try:
            lang.gbs_type.unify(proc_type, expected)
        except lang.gbs_type.UnificationFailedException as e:
            area = common.position.ProgramAreaNear(tree)
            msg = i18n.i18n(
                      'procedure "%s" is receiving: %s\n' +
                      'But should receive: %s'
                  ) % (
                      proc_name, expected.paramtype(), proc_type.paramtype()
                  )
            self.error(GbsTypeInferenceException(msg, area))
        tree.type_annotation = proc_type.parameters()

    def infer_assign_var_name(self, tree):
        "Infer types for a variable assignment: var := <expr>"
        var = tree.children[1].children[1]
        offsets = tree.children[2]
        exp = tree.children[3]
        try:
            self._add_var_with_offset(var, offsets, self.infer_expression(exp))
        except lang.gbs_type.UnificationFailedException as e:
            area = common.position.ProgramAreaNear(tree)
            msg = i18n.i18n(
                      '"%s" has type: %s\n' +
                      'Right hand side has type: %s'
                  ) % (
                      var.value, e.type2.show(), e.type1.show()
                  )
            self.error(GbsTypeInferenceException(msg, area))

    def infer_assign_var_tuple1(self, tree):
        "Infer types for a tuple assignment: (v1, ..., vN) := f(...)"
        tup = tree.children[1].children
        funcCall = tree.children[2]
        fun_name = funcCall.children[1].value
        ret_types = self._infer_func_call(funcCall, nretvals=len(tup))
        for var, ret_type in zip(tup, ret_types.subtypes()):
            try:
                self._add_var(var, ret_type)
            except lang.gbs_type.UnificationFailedException as e:
                area = common.position.ProgramAreaNear(var)
                msg = i18n.i18n(
                          '"%s" has type: %s\n' +
                          'Function "%s" returns: %s'
                      ) % (
                          var.value, e.type1.show(),
                          fun_name, ret_types.show()
                      )
                self.error(GbsTypeInferenceException(msg, area))

    def infer_if(self, tree):
        "Infer types for conditional statement."
        cond = tree.children[1]
        self._infer_expression_check_type(cond, lang.gbs_type.GbsBoolType())
        self.infer_block(tree.children[2]) # then
        if tree.children[3] is not None:
            self.infer_block(tree.children[3]) # else

    def infer_case(self, tree):
        "Infer types for a case statement."
        value = tree.children[1]
        value_type = lang.gbs_type.GbsTypeVar()
        self._infer_expression_check_type(value, value_type)
        for branch in tree.children[2].children:
            if branch.children[0] == 'branch':
                self._check_literals(branch.children[1], value_type)
                self.infer_block(branch.children[2])
            else: # defaultBranch
                self.infer_block(branch.children[1])

    def _check_literals(self, lits, expected_type):
        """Check the types for the list of literals in a
        case statement."""
        for lit in lits.children:
            lit_type = self.infer_tok_literal(lit)
            try:
                lang.gbs_type.unify(lit_type, expected_type)
            except lang.gbs_type.UnificationFailedException as e:
                area = common.position.ProgramAreaNear(lit)
                msg = i18n.i18n(
                          'Literal should have type: %s\n' +
                          'But has type: %s'
                      ) % (
                          expected_type, lit_type
                      )
                self.error(GbsTypeInferenceException(msg, area))

    def infer_while(self, tree):
        "Infer types for a while statement."
        cond = tree.children[1]
        self._infer_expression_check_type(cond, lang.gbs_type.GbsBoolType())
        self.infer_block(tree.children[2])

    def infer_repeat(self, tree):
        "Infer types for a repeat statement."
        times = tree.children[1]
        self._infer_expression_check_type(times, lang.gbs_type.GbsIntType())
        self.infer_block(tree.children[2])

    def infer_foreach(self, tree):
        "Infer types for a foreach statement."
        index = tree.children[1]
        list = tree.children[2]
        index_type = lang.gbs_type.GbsTypeVar()
        # index and both limits should have the same type
        self._add_var(index, index_type)
        self._infer_expression_check_type(list, lang.gbs_type.GbsListType(index_type))
        self.infer_block(tree.children[3])
        tree.index_type_annotation = index_type

    def infer_repeat_with(self, tree):
        "Infer types for a repeatWith statement."
        index = tree.children[1]
        rng = tree.children[2]
        index_type = lang.gbs_type.GbsTypeVar()
        exclude_type = lang.gbs_type.GbsListType(lang.gbs_type.GbsTypeVar())
        # index and both limits should have the same type
        self._add_var(index, index_type)
        self._infer_expression_check_type(rng.children[1], index_type, [exclude_type])
        self._infer_expression_check_type(rng.children[2], index_type, [exclude_type])
        self.infer_block(tree.children[3])
        tree.index_type_annotation = index_type

    def infer_block(self, tree):
        "Infer types for a block of commands."
        self.infer_commands(tree.children[1])

    def infer_return(self, tree):
        """Infer types for a return statement. Add a type annotation
        to the AST node, to be able to retrieve the type of the
        returned expression later."""
        tree.type_annot = self.infer_tuple(tree.children[1])

    def infer_tuple(self, tree):
        "Infer types for a tuple."
        types = []
        for exp in tree.children:
            types.append(self.infer_expression(exp))
        return lang.gbs_type.GbsTupleType(types)

    def infer_expression(self, tree):
        "Infer types for an expression."
        exptype = tree.children[0]
        dispatch = {
          'or': self.infer_bool_bool_bool_binary_op,
          'and': self.infer_bool_bool_bool_binary_op,
          'not': self.infer_bool_bool_unary_op,
          'relop': self.infer_a_a_bool_binary_op,
          'addsub': self.infer_int_int_int_binary_op,
          'mul': self.infer_int_int_int_binary_op,
          'divmod': self.infer_int_int_int_binary_op,
          'pow': self.infer_int_int_int_binary_op,
          'listop': self.infer_list_list_list_binary_op,
          'projection': self.infer_projection,
          'constructor': self.infer_constructor,
          'varName': self.infer_var_name,
          'funcCall': self.infer_func_call,
          'match': self.infer_match,
          'unaryMinus': self.infer_a_a_unary_op,
          'literal': self.infer_literal,
          'type': self.infer_type,
        }
        if exptype in dispatch:
            return dispatch[exptype](tree)
        else:
            msg = i18n.i18n('Unknown expression: %s') % (exptype,)
            area = common.position.ProgramAreaNear(tree)
            self.error(GbsTypeInferenceException(msg, area))

    def _check_excluded_types(self, tree, type, excluded_types):
        for excluded_type in excluded_types:
            try:
                lang.gbs_type.unify(type, excluded_type)
                area = common.position.ProgramAreaNear(tree)
                msg = i18n.i18n('Expression can\'t have type: %s') % (excluded_type,)
                self.error(GbsTypeInferenceException(msg, area))
            except lang.gbs_type.UnificationFailedException as exception:
                pass

    def _infer_expression_check_type(self, tree, expected_type, excluded_types=[]):
        """Infer types for an expression, and check that its
        inferred type coincides with the expected type."""
        
        real_type = self.infer_expression(tree)
        return self.check_type(tree, real_type, expected_type, excluded_types)

    def check_type(self, tree, real_type, expected_type, excluded_types=[]):
        try:
            lang.gbs_type.unify(real_type, expected_type)
            self._check_excluded_types(tree, real_type, excluded_types)
            return real_type
        except lang.gbs_type.UnificationFailedException as e:
            area = common.position.ProgramAreaNear(tree)
            msg = i18n.i18n(
                      'Expression should have type: %s\n' +
                      'But has type: %s'
                  ) % (
                      expected_type, real_type
                  )
            self.error(GbsTypeInferenceException(msg, area))
        
    def infer_bool_bool_bool_binary_op(self, tree):
        """Infer types for an application of a binary operator
        of type 'Bool * Bool -> Bool'."""
        t = lang.gbs_type.GbsBoolType()
        self._infer_expression_check_type(tree.children[2], t)
        self._infer_expression_check_type(tree.children[3], t)
        tree.type_annotation = [t,t]
        return t

    def infer_a_a_bool_binary_op(self, tree):
        """Infer types for an application of a binary operator
        of type 'forall a. a * a -> Bool'."""
        t = lang.gbs_type.GbsTypeVar()
        self._infer_expression_check_type(tree.children[2], t)
        self._infer_expression_check_type(tree.children[3], t)
        tree.type_annotation = [t,t]
        return lang.gbs_type.GbsBoolType()

    def infer_int_int_int_binary_op(self, tree):
        """Infer types for an application of a binary operator
        of type 'Int * Int -> Bool'."""
        t = lang.gbs_type.GbsIntType()
        self._infer_expression_check_type(tree.children[2], t)
        self._infer_expression_check_type(tree.children[3], t)
        tree.type_annotation = [t,t]
        return t
    
    def infer_a_a_list_binary_op(self, tree):
        """Infer types for an application of a binary operator
        of type 'a * a -> List(a)'."""
        t = lang.gbs_type.GbsTypeVar()
        self._infer_expression_check_type(tree.children[2], t)
        self._infer_expression_check_type(tree.children[3], t)
        return lang.gbs_type.GbsListType(t)
    
    def infer_list_list_list_binary_op(self, tree):
        """Infer types for an application of a binary operator
        of type 'List * List -> List'."""
        t = lang.gbs_type.GbsListType()
        self._infer_expression_check_type(tree.children[2], lang.gbs_type.GbsListType())
        self._infer_expression_check_type(tree.children[3], lang.gbs_type.GbsListType())
        tree.type_annotation = [t,t]
        return t
    
    def infer_constructor(self, tree):
        """ Infer record/variant constructor type """
        expected_type = self.infer_type(tree.children[2])
        
        def constructor_except(real_type, expected_type):
            area = common.position.ProgramAreaNear(tree)
            msg = i18n.i18n(
                      'constructor "%s" is receiving: %s\n' +
                      'But should receive: %s'
                  ) % (
                      expected_type.name, real_type.fields_repr(), expected_type.fields_repr()
                  )
            self.error(GbsTypeInferenceException(msg, area))
        
        fieldgens = collect_nodes_until_found(tree, is_field_gen)
            
        fields = {}
        for fieldgen in fieldgens:
            fname, fvalue = fieldgen.children[2].children
            fields[fname.children[1].value] = self.infer_expression(fvalue)
        
        type_name = tree.children[2].children[1]
        if type_name.value == "Arreglo":
            real_type = lang.gbs_type.GbsArrayType()
        else:
            real_type = lang.gbs_type.GbsRecordType(type_name.value, fields)
        
        return_type = expected_type 
        
        if isinstance(expected_type, lang.gbs_type.GbsVariantType):
            if type_name.value == expected_type.name:
                area = common.position.ProgramAreaNear(tree)
                msg = i18n.i18n('"%s" is not a valid variant case for "%s" type.') % (
                      type_name.value, expected_type.name
                  )
                self.error(GbsTypeInferenceException(msg, area))
            expected_type.is_case = type_name.value.split("::")[1] 
            expected_type = expected_type.get_case()
        
        if not isinstance(real_type, lang.gbs_type.GbsArrayType) and len(fields.keys()) != len(expected_type.fields.keys()):
            constructor_except(real_type, expected_type)
        
        try:
            self.check_type(tree, real_type, expected_type)
        except GbsTypeInferenceException as e:
            constructor_except(real_type, expected_type)
        
        return return_type
    
    def infer_projection(self, tree):
        """Infer types for an application of projection operator
        of type 'Record(s1:a1 * s2:a2 .. * sn:an) * si -> ai'"""
        field_name = tree.children[3].children[1]
        t1 = lang.gbs_type.GbsRecordTypeVar({field_name.value : lang.gbs_type.GbsTypeVar()})
        t2 = lang.gbs_type.GbsSymbolType()
        self._infer_expression_check_type(tree.children[2], t1)
        self._infer_expression_check_type(tree.children[3], t2)
        return t1.fields.get(field_name.value) 

    def infer_bool_bool_unary_op(self, tree):
        """Infer types for an application of a unary operator
        of type 'Bool -> Bool'."""
        t = lang.gbs_type.GbsBoolType()
        self._infer_expression_check_type(tree.children[1], t)
        tree.type_annotation = [t]
        return t

    def infer_a_a_unary_op(self, tree):
        """Infer types for an application of a unary operator
        of type 'forall a. a -> a'."""
        t = lang.gbs_type.GbsTypeVar()
        self._infer_expression_check_type(tree.children[1], t)
        tree.type_annotation = [t]
        return t

    def infer_var_name(self, tree):
        "Infer types for a variable use."
        return self._add_var(tree.children[1], None)

    def infer_func_call(self, tree):
        "Infer types for a function call."
        res_type = self._infer_func_call(tree, nretvals=1)
        return res_type.subtypes()[0] # singleton tuple

    def infer_match(self, tree):
        "Infer types for a match statement."
        value = tree.children[1]
        value_type = lang.gbs_type.GbsTypeVar()
        branch_body_type = lang.gbs_type.GbsTypeVar()
        self._infer_expression_check_type(value, value_type)
        for branch in tree.children[2].children:
            if branch.children[0] == 'branch':
                self._check_literals(branch.children[1], value_type)
                branch_body = branch.children[2]
            else: # defaultBranch
                branch_body = branch.children[1]
            self._infer_expression_check_type(branch_body, branch_body_type)
        return branch_body_type

    def _infer_func_call(self, tree, nretvals):
        "Infer types for a function call."
        fun_name = tree.children[1].value
        fun_type = self.global_context[fun_name].instantiate()
        arg_type = self.infer_tuple(tree.children[2])
        subtypes = [lang.gbs_type.GbsTypeVar() for i in range(nretvals)]
        res_type = lang.gbs_type.GbsTupleType(subtypes)
        expected = lang.gbs_type.GbsFunctionType(arg_type, res_type)

        # check parameters
        try:
            lang.gbs_type.unify(expected.paramtype(), fun_type.paramtype())
        except lang.gbs_type.UnificationFailedException as e:
            area = common.position.ProgramAreaNear(tree)
            msg = i18n.i18n(
                      'function "%s" is receiving: %s\n' +
                      'But should receive: %s'
                  ) % (
                      fun_name, print_type(expected.paramtype()), print_type(fun_type.paramtype())
                  )
            self.error(GbsTypeInferenceException(msg, area))

        # check return value
        try:
            lang.gbs_type.unify(fun_type._res, expected._res)
        except lang.gbs_type.UnificationFailedException as e:
            area = common.position.ProgramAreaNear(tree)
            msg = i18n.i18n(
                      'function "%s" is called as if it returned: %s\n' +
                      'But returns: %s'
                  ) % (
                      fun_name, expected._res, fun_type._res
                  )
            self.error(GbsTypeInferenceException(msg, area))

        tree.type_annotation = fun_type.parameters()
        return res_type

    def infer_literal(self, tree):
        "Infer types for a literal expression."
        return self.infer_tok_literal(tree.children[1])

    def infer_tok_literal(self, tok):
        "Infer types for a constant."
        if tok.type == 'num':
            return lang.gbs_type.GbsIntType()
        elif tok.type == 'upperid':
            return self.global_context[tok.value].instantiate()
        elif tok.type == 'symbol':
            return lang.gbs_type.GbsSymbolType()
        elif tok.type == 'string':
            return lang.gbs_type.GbsStringType()
        else:
            assert False

def typecheck(tree, enable_errors=False):
    "Infer types for a Gobstones program."
    GbsTypeInference(enable_errors).infer_program(tree)

