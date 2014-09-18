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
import lang.gbs_builtins
import common.position
import common.i18n as i18n

from lang.gbs_def_helper import *

#from common.utils import *
from common.utils import (
    StaticException,
    set_new, set_add,
)

class GbsTypeInferenceException(StaticException):
    "Base class for type inferrer exceptions."

    def error_type(self):
        "Return the error type of these exceptions."
        return i18n.i18n('Type error')

class GbsTypeInference(object):
    "Infer types and decorate Gobstones programs with type annotations."

    def __init__(self):
        self.ribs = [set_new()]
        self.global_context = {}
        self.context = {}
        self.init_builtins()

    def init_builtins(self):
        "Initialize a global context with types for all the builtins."
        for b in lang.gbs_builtins.BUILTINS:
            bname, b = b.name(), b.underlying_construct()
            set_add(self.ribs[0], b.name())
            self.global_context[b.name()] = b.gbstype()

    def push_env(self):
        "Push an empty environment into the stack of environment ribs."
        self.ribs.append(set_new())

    def pop_env(self):
        "Pop the top environment from the stack of environment ribs."
        for name in self.ribs[-1]:
            del self.context[name]
        self.ribs.pop()

    def _add_var(self, token, new_type=None):
        """Add a variable to the context with the given type, checking
        that it is consistent with the types it might already have."""
        if new_type is None: # fresh
            new_type = lang.gbs_type.GbsTypeVar()
        varname = token.value
        if varname in self.ribs[-1]:
            old_type = self.context[varname]
            lang.gbs_type.unify(old_type, new_type)
        else:
            self.context[varname] = new_type
            set_add(self.ribs[-1], varname)
        return new_type

    def infer_program(self, tree):
        "Infer the type of a program."
        self.module_handler = tree.module_handler
        for mdl_name, mdl_tree in self.module_handler.parse_trees():
            mdl_infer = GbsTypeInference()
            try:
                mdl_infer.infer_program(mdl_tree)
            except SourceException as exception:
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
        "Add the types of all the imported routines to the global context."
        for imp in imports:
            mdl_name = imp.children[1].value
            rtns = imp.children[2].children
            for rtn in rtns:
                self.global_context[rtn.value] = self.module_handler.type_of(
                                                    mdl_name, rtn.value)

    def infer_defs(self, tree):
        "Infer the type of a list of definitions."
        for def_ in tree.children:
            self.initialize_def(def_)
        for def_ in tree.children:
            self.infer_def(def_)

    def initialize_def(self, tree):
        """Initialize the types of all the toplevel definitions in a
        file. Routines are initialized with fresh types.
        For instance, given "function f(x1, x2) {...}", the
        identifier "f" is initialized with type (s1 x s2) -> s3,
        where s1, s2 and s3 are fresh type variables."""
        tok = get_def_name(tree)
        params = lang.gbs_type.GbsTypeVar()
        
        type_decl = get_def_type_decl(tree)
        if type_decl is not None:
            t = lang.gbs_type.parse_type_declaration(type_decl)
        elif is_def_keyword(tree, 'procedure'):
            t = lang.gbs_type.GbsProcedureType(params)
        elif is_entrypoint_def(tree):
            t = lang.gbs_type.GbsEntryPointType()        
        else:
            t = lang.gbs_type.GbsFunctionType(params,
                                              lang.gbs_type.GbsTypeVar())
        self.global_context[tok.value] = t

    def infer_def(self, tree):
        "Infer the type of a definition (either a function or a procedure)."
        prfn, name, params, body, type_decl = unpack_definition(tree)
        self.push_env()
        for p in params.children:
            self._add_var(p)
        self.infer_commands(body)
        self._set_definition_type(tree, prfn, name, params, body)
        #self._debug(tree)
        self.pop_env()

    def _debug(self, tree):
        print()
        print('DEF', tree.children[0], tree.children[1].value)
        d2 = {}
        for k, v in self.global_context.items():
            if k not in lang.gbs_builtins.BUILTIN_NAMES:
                d2[k] = v
        print('   Global_ctx:', d2)
        print('   Local_ctx :', self.context)

    def _set_definition_type(self, tree, prfn, name, params, body):
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
            raise GbsTypeInferenceException(msg, area)

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
            raise GbsTypeInferenceException(msg, area)

    def infer_assign_var_name(self, tree):
        "Infer types for a variable assignment: var := <expr>"
        var = tree.children[1]
        exp = tree.children[2]
        try:
            self._add_var(var, self.infer_expression(exp))
        except lang.gbs_type.UnificationFailedException as e:
            area = common.position.ProgramAreaNear(tree)
            msg = i18n.i18n(
                      '"%s" has type: %s\n' +
                      'Right hand side has type: %s'
                  ) % (
                      var.value, e.type1.show(), e.type2.show()
                  )
            raise GbsTypeInferenceException(msg, area)

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
                raise GbsTypeInferenceException(msg, area)

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
                raise GbsTypeInferenceException(msg, area)

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
        rng_or_enum = tree.children[2]
        index_type = lang.gbs_type.GbsTypeVar()
        # index and range/enumeration components should have the same type
        self._add_var(index, index_type)
        for child in rng_or_enum.children[1:]:
            if not child is None:
                self._infer_expression_check_type(child, index_type)        
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
          'varName': self.infer_var_name,
          'funcCall': self.infer_func_call,
          'unaryMinus': self.infer_a_a_unary_op,
          'literal': self.infer_literal,
        }
        assert exptype in dispatch
        return dispatch[exptype](tree)

    def _infer_expression_check_type(self, tree, expected_type):
        """Infer types for an expression, and check that its
        inferred type coincides with the expected type."""
        real_type = self.infer_expression(tree)
        try:
            lang.gbs_type.unify(real_type, expected_type)
            return real_type
        except lang.gbs_type.UnificationFailedException as e:
            area = common.position.ProgramAreaNear(tree)
            msg = i18n.i18n(
                      'Expression should have type: %s\n' +
                      'But has type: %s'
                  ) % (
                      expected_type, real_type
                  )
            raise GbsTypeInferenceException(msg, area)

    def infer_bool_bool_bool_binary_op(self, tree):
        """Infer types for an application of a binary operator
        of type 'Bool * Bool -> Bool'."""
        t = lang.gbs_type.GbsBoolType()
        self._infer_expression_check_type(tree.children[2], t)
        self._infer_expression_check_type(tree.children[3], t)
        return t

    def infer_a_a_bool_binary_op(self, tree):
        """Infer types for an application of a binary operator
        of type 'forall a. a * a -> Bool'."""
        t = lang.gbs_type.GbsTypeVar()
        self._infer_expression_check_type(tree.children[2], t)
        self._infer_expression_check_type(tree.children[3], t)
        return lang.gbs_type.GbsBoolType()

    def infer_int_int_int_binary_op(self, tree):
        """Infer types for an application of a binary operator
        of type 'Int * Int -> Bool'."""
        t = lang.gbs_type.GbsIntType()
        self._infer_expression_check_type(tree.children[2], t)
        self._infer_expression_check_type(tree.children[3], t)
        return t

    def infer_bool_bool_unary_op(self, tree):
        """Infer types for an application of a unary operator
        of type 'Bool -> Bool'."""
        t = lang.gbs_type.GbsBoolType()
        self._infer_expression_check_type(tree.children[1], t)
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
            lang.gbs_type.unify(fun_type.paramtype(), expected.paramtype())
        except lang.gbs_type.UnificationFailedException as e:
            area = common.position.ProgramAreaNear(tree)
            msg = i18n.i18n(
                      'function "%s" is receiving: %s\n' +
                      'But should receive: %s'
                  ) % (
                      fun_name, expected.paramtype(), fun_type.paramtype()
                  )
            raise GbsTypeInferenceException(msg, area)

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
            raise GbsTypeInferenceException(msg, area)

        tree.type_annotation = expected.parameters()
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
        else:
            assert False

def typecheck(tree):
    "Infer types for a Gobstones program."
    GbsTypeInference().infer_program(tree)

