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

"Gobstones compiler from source ASTs to virtual machine code."

import lang.gbs_vm
import lang.gbs_builtins
import lang.gbs_type
import lang.gbs_def_helper as def_helper
import common.i18n as i18n
import common.position
import common.utils

class GbsCompileException(common.utils.StaticException):
    "Base exception for Gobstones compiler errors."
    pass

def parse_literal(tok):
    """Given a token, parse its string value and return the denotated
    Gobstones value.
    """
    if tok.type == 'symbol':
        val = tok.value
    else:
        val = lang.gbs_builtins.parse_constant(tok.value)
        #assert val is not None
        if val is None:
            val = tok.value
    return val

class GbsLabel(object):
    "Represents a unique label in the program."
    def __repr__(self):
        return 'L_%s' % (id(self),)

class GbsCompiler(object):
    "Compiler of Gobstones programs."

    def __init__(self):
        self.code = None
        self.temp_counter = None
        self.module_handler = None
        self._current_def_name = None
        self.constructor_of_type = {"Arreglo":"Arreglo"}

    def compile_program(self, tree, module_prefix='', explicit_board=None):
        """Given an AST for a full program, compile it to virtual machine
code, returning an instance of lang.gbs_vm.GbsCompiledProgram.
The Main module should be given the empty module prefix ''.
Every other module should be given the module name as a prefix.
"""
        if explicit_board is None:
            entrypoint_tree = def_helper.find_def(tree.children[2], def_helper.is_entrypoint_def)
            self.explicit_board = len(entrypoint_tree.children[2].children) != 0
        else:
            self.explicit_board = explicit_board
        self.module_handler = tree.module_handler
        self.compile_imported_modules(tree)

        imports = tree.children[1].children
        defs = tree.children[2]

        self.code = lang.gbs_vm.GbsCompiledProgram(
                        tree, module_prefix=module_prefix)
        self.compile_imports(imports)
        self.user_defined_routine_names = list(self.code.external_routines.keys())
        self.user_defined_routine_names += def_helper.get_routine_names(defs)
        
        self.compile_defs(defs)
        return self.code

    def compile_imported_modules(self, tree):
        "Recursively compile the imported modules."
        for mdl_name, mdl_tree in self.module_handler.parse_trees():
            compiler = GbsCompiler()
            try:
                code = compiler.compile_program(
                           mdl_tree, module_prefix=mdl_name, explicit_board=self.explicit_board
                       )
                self.constructor_of_type.update(compiler.constructor_of_type)
            except common.utils.SourceException as exception:
                self.module_handler.reraise(
                    GbsCompileException,
                    exception,
                    i18n.i18n(
                        'Error compiling module %s'
                    ) % (
                        mdl_name,
                    ),
                    common.position.ProgramAreaNear(tree.children[1]))
            self.module_handler.set_compiled_code(mdl_name, code)

    def compile_imports(self, imports):
        """Add the imported procedures and functions to the local
namespace of routines.
"""
        for imp in imports:
            mdl_name = imp.children[1].value
            rtns = imp.children[2].children
            for rtn in rtns:
                if (not isinstance(rtn, lang.gbs_constructs.UserType) and
                    not isinstance(rtn, lang.gbs_constructs.BuiltinFieldGetter)):
                    mdl_code = self.module_handler.compiled_code_for(mdl_name)
                    if rtn.name() in mdl_code.routines:
                        self.code.external_routines[rtn.name()] = (
                            mdl_code,
                            mdl_code.routines[rtn.name()]
                        )
                    else:
                        assert rtn.name() in mdl_code.external_routines
                        val = mdl_code.external_routines[rtn.name()]
                        self.code.external_routines[rtn.name()] = val

    def compile_defs(self, tree):
        "Compile a list of definitions."
        self.temp_counter = 0
        for def_ in tree.children:
            if def_helper.is_type_def(def_):
                self.gather_type_data(def_)
            else:
                self.compile_routine_def(def_)
                    
    def gather_type_data(self, def_):
        _, type_name, type_or_def = def_.children
        if type_or_def.children[0] == 'record':
            self.constructor_of_type[type_name.value] = type_name.value
        else:
            body = type_or_def.children[1]
            for case in body.children:
                _, cname, _ = case.children
                self.constructor_of_type[cname.value] = type_name.value
                    
    def temp_varname(self):
        "Make a temporary variable name."
        self.temp_counter += 1
        return '_tempvar%i' % (self.temp_counter)

    def compile_routine_def(self, tree):
        "Compile a single definition."
        prfn = def_helper.get_def_keyword(tree)
        name = def_helper.get_def_name(tree).value
        self._current_def_name = name
        params = [param.value for param in def_helper.get_def_params(tree)]
        
        immutable_params = []
        if prfn == 'function':
            immutable_params = params
        elif prfn == 'procedure' and len(params) > 1:
            immutable_params = params[1:]
            
        code = lang.gbs_vm.GbsCompiledCode(tree, prfn, name, params, self.explicit_board)
        code.add_enter()
        for p in immutable_params:
                code.push(('setImmutable', p), near=tree)            
        self.compile_commands(def_helper.get_def_body(tree), code)
        if prfn == 'procedure' and self.explicit_board:            
            code.push(('pushFrom', params[0]), near=tree)                
        code.add_leave_return()
        code.build_label_table()
        self.code.routines[name] = code

    #### The following methods take a program fragment in form of an AST
    #### and a "code" argument, which should be an instance of
    #### lang.gbs_vm.GbsCompiledCode.
    ####
    #### The compilation process appends to the compiled code the virtual
    #### machine code corresponding to the given program fragment.

    #### Commands

    def compile_commands(self, tree, code):
        "Compile a sequence of commands."
        for cmd in tree.children:
            self.compile_cmd(cmd, code)

    def compile_cmd(self, tree, code):
        "Compile a single command."
        command = tree.children[0]
        dispatch = {
            'Skip': self.compile_skip,
            'THROW_ERROR': self.compile_boom,
            'procCall': self.compile_proc_call,
            'assignVarName': self.compile_assign_var_name,
            'assignVarTuple1': self.compile_assign_var_tuple1,
            'if': self.compile_if,
            'case': self.compile_case,
            'while': self.compile_while,
            'repeat': self.compile_repeat,
            'repeatWith': self.compile_repeat_with,
            'foreach': self.compile_foreach,
            'block': self.compile_block,
            'return': self.compile_return,
        }
        assert command in dispatch
        dispatch[command](tree, code)

    def compile_type(self, tree, code):
        """Compile a type expression. Just fill a hole in construct() function.
        In a future, it could be usefull for runtime type checks. [CHECK]"""
        tok = tree.children[1]
        type = self.constructor_of_type[tok.value] + "::" + tok.value
        code.push(('pushConst', type), near=tree)

    def compile_skip(self, tree, code):
        "Compile a Skip command."
        pass

    def compile_boom(self, tree, code):
        "Compile a THROW_ERROR command."
        code.push(('THROW_ERROR', tree.children[1].value), near=tree)

    def compile_proc_call(self, tree, code):
        "Compile a procedure call."
        procname = tree.children[1].value
        args = tree.children[2].children     
        
        if self.explicit_board:           
            inout_var = args[0]
        
        type_annotation = None
        if hasattr(tree, 'type_annotation'):
            type_annotation = tree.type_annotation
            
        for i, arg in zip(range(len(args)), args):
            self.compile_expression(arg, code)
        code.push(('call', procname, len(args)), near=tree)
        
        if self.explicit_board:
            code.push(('popTo', inout_var.children[1].value), near=tree)


    def compile_projectable_var_check(self, tree, code, var):
        "Compile a projectable variable check. Varname is pushed to stack."
        code.push(('pushConst', var), near=tree)
        code.push(('call', '_checkProjectableVar', 1), near=tree)
        
    def compile_assign_var_name(self, tree, code):
        "Compile an assignment: <lvalue> := <expr>"            
        
        offsets = tree.children[2].children    
        if len(offsets) > 0:
            #calculate assignment reference       
            var = tree.children[1].children[1].value
            self.compile_projectable_var_check(tree, code, var)
            code.push(('pushFrom', var), near=tree)                                
            for offset in offsets:
                if offset.children[0] == 'index':
                    self.compile_expression(offset.children[1], code)
                else:
                    code.push(('pushConst', parse_literal(offset.children[1].children[1])), near=tree)
                code.push(('call', '_getRef', 2), near=tree)        
            
            #compile expression
            self.compile_expression(tree.children[3], code)
            #Set ref
            code.push(('call', '_SetRefValue', 2), near=tree)
        else:
            #compile expression
            self.compile_expression(tree.children[3], code)
            #assign varname
            full_varname = '.'.join([tok.value for tok in tree.children[1].children[1:]])        
            code.push(('popTo', full_varname), near=tree)
    
    def compile_assign_var_tuple1(self, tree, code):
        "Compile a tuple assignment: (v1, ..., vN) := f(...)"
        self.compile_expression(tree.children[2], code)
        varnames = [var.value for var in tree.children[1].children]
        for var in common.utils.seq_reversed(varnames):
            code.push(('popTo', var), near=tree)

    def compile_if(self, tree, code):
        "Compile a conditional statement."
        lelse = GbsLabel()
        self.compile_expression(tree.children[1], code) # cond
        code.push((('jumpIfFalse'), lelse), near=tree)
        self.compile_block(tree.children[2], code) # then
        if tree.children[3] is None:
            code.push(('label', lelse), near=tree)
        else:
            lend = GbsLabel()
            code.push(('jump', lend), near=tree)
            code.push(('label', lelse), near=tree)
            self.compile_block(tree.children[3], code) # else
            code.push(('label', lend), near=tree)

    def compile_case(self, tree, code):
        "Compile a case statement."
        #   case (Value) of
        #     Lits1 -> {Body1}
        #     LitsN -> {BodyN}
        #     _     -> {BodyElse}
        #
        # Compiles to code corresponding to:
        #
        #   value0 := Value
        #   if   (value0 in Lits1) {Body1}
        #   elif (value0 in Lits2) {Body2}
        #   ...
        #   elif (value0 in LitsN) {BodyN}
        #   else               {BodyElse}
        value = tree.children[1]
        value0 = self.temp_varname()
        
        self.compile_expression(value, code)
        # value0 := value
        code.push(('popTo', value0), near=tree)
        
        lend = GbsLabel()
        next_label = None
        for branch in tree.children[2].children:
            if next_label is not None:
                code.push(('label', next_label), near=tree)
            if branch.children[0] == 'branch':
                lits = [parse_literal(lit) for lit in branch.children[1].children]
                next_label = GbsLabel()
                # if value0 in LitsI
                code.push(('pushFrom', value0), near=tree)
                code.push(('jumpIfNotIn', lits, next_label), near=tree)
                # BodyI
                self.compile_block(branch.children[2], code)
                code.push(('jump', lend), near=tree)
            else: # defaultBranch
                # BodyElse
                self.compile_block(branch.children[1], code)
        code.push(('label', lend), near=tree)
    
    def compile_match(self, tree, code):
        "Compile a match statement."
        #   match (<Expr-V>) of
        #     <Case-1> -> <Expr-1>
        #     <Case-2> -> <Expr-2>
        #     ...
        #     <Case-N> -> <Expr-N>
        #     _        -> <Expr-Else>
        #
        # Compiles to code corresponding to:
        #
        #   case := _extract_case(<Expr-V>)
        #   if   (case == <Case-1>) <Expr-1>
        #   elif (case == <Case-2>) <Expr-2>
        #   ...
        #   elif (case == <Case-N>) <Expr-N>
        #   else <Expr-Else>
        value = tree.children[1]
        value0 = self.temp_varname()
        
        self.compile_expression(value, code)
        # This is a runtime function to extract type name
        code.push(('call', '_extract_case', 1), near=tree)
        # value0 := value
        code.push(('popTo', value0), near=tree)
        
        lend = GbsLabel()
        next_label = None
        default_branch = False
        for branch in tree.children[2].children:
            if not next_label is None:
                code.push(('label', next_label), near=tree)
            if branch.children[0] == 'branch':
                case_i = parse_literal(branch.children[1])
                next_label = GbsLabel()
                # if value0 in LitsI
                code.push(('pushFrom', value0), near=tree)
                code.push(('pushConst', case_i), near=tree)
                code.push(('call', '==', 2), near=tree)
                code.push(('jumpIfFalse', next_label), near=tree)
                # BodyI
                self.compile_expression(branch.children[2], code)
                code.push(('jump', lend), near=tree)
            else: # defaultBranch
                # BodyElse
                default_branch = True
                self.compile_expression(branch.children[1], code)
        if not default_branch:
            code.push(('label', next_label), near=tree)
            code.push(('THROW_ERROR', '"' + i18n.i18n('Expression has no matching branch.') + '"'), near=tree)
        code.push(('label', lend), near=tree)

    def compile_while(self, tree, code):
        "Compile a while statement."
        lbegin = GbsLabel()
        lend = GbsLabel()
        code.push(('label', lbegin), near=tree)
        self.compile_expression(tree.children[1], code) # cond
        code.push(('jumpIfFalse', lend), near=tree)
        self.compile_block(tree.children[2], code) # body
        code.push(('jump', lbegin), near=tree)
        code.push(('label', lend), near=tree)

    def compile_repeat(self, tree, code):
        "Compile a repeat statement."
        #
        #   repeat (<Expr>) <Block>
        #
        # Compiles to code corresponding to
        # the following fragment:
        #
        #   counter := <Expr>
        #   while (true) {
        #     if (not (counter > 0)) { break }
        #     <Block>
        #     counter := counter - 1
        #   }
        #
        
        times = tree.children[1]
        body = tree.children[2]
        counter = self.temp_varname()
        lbegin = GbsLabel()
        lend = GbsLabel()
        # counter := <Expr>
        self.compile_expression(times, code)
        code.push(('popTo', counter), near=tree)
        # while (true) {
        code.push(('label', lbegin), near=tree)
        #   if (not (counter > 0) { break }
        code.push(('pushFrom', counter), near=tree)
        code.push(('pushConst', 0), near=tree)
        code.push(('call', '>', 2), near=tree)
        code.push(('jumpIfFalse', lend), near=tree)
        #   <Block>
        self.compile_block(body, code)
        #   counter := counter - 1
        code.push(('pushFrom', counter), near=tree)
        code.push(('pushConst', 1), near=tree)
        code.push(('call', '-', 2), near=tree)
        code.push(('popTo', counter), near=tree)            
        # end while
        code.push(('jump', lbegin), near=tree)
        code.push(('label', lend), near=tree)
        code.push(('delVar', counter), near=tree)

    def compile_foreach(self, tree, code):
        "Compile a foreach statement."
        #
        #   foreach <Index> in <List> <Block>
        #
        # Compiles to code corresponding to
        # the following fragment:
        #
        #   xs0 := <List>
        #   while (true) {
        #     if (isEmpty(xs0)) break;
        #     <Index> := head(xs0)
        #     setImmutable(<Index>)
        #     <Block>
        #     unsetImmutable(<Index>)
        #     xs0 := tail(xs)
        #   }
        #
        def jumpIfIsEmpty(var, label):
            code.push(('pushFrom', var), near=tree)
            code.push(('call', i18n.i18n('isEmpty'), 1), near=tree)
            code.push(('call', 'not', 1), near=tree)
            code.push(('jumpIfFalse', label), near=tree)
        def head(listVar, var):
            code.push(('pushFrom', listVar), near=tree)
            code.push(('call', i18n.i18n('head'), 1), near=tree)
            code.push(('popTo', var), near=tree)
        def tail(listVar, var):
            code.push(('pushFrom', listVar), near=tree)
            code.push(('call', i18n.i18n('tail'), 1), near=tree)
            code.push(('popTo', var), near=tree)
            
        index = tree.children[1].value
        list_ = tree.children[2]
        body = tree.children[3]
        xs0 = self.temp_varname()
        lbegin = GbsLabel()
        lend = GbsLabel()
        lend2 = GbsLabel()
        # xs0 := <List>
        self.compile_expression(list_, code)
        code.push(('popTo', xs0), near=tree)        
        # while (true) {
        code.push(('label', lbegin), near=tree)
        #   if (isEmpty(xs0)) break;
        jumpIfIsEmpty(xs0, lend)
        #   <Index> := head(xs0)
        head(xs0, index)
        #   setImmutable(<Index>)
        code.push(('setImmutable', index), near=tree)
        #   <Block>
        self.compile_block(body, code)
        #   setImmutable(<Index>)
        code.push(('unsetImmutable', index), near=tree)
        #   xs0 := tail(xs0)
        tail(xs0, xs0)
        # }
        code.push(('jump', lbegin), near=tree)
        code.push(('label', lend2), near=tree)
        code.push(('delVar', index), near=tree)
        code.push(('label', lend), near=tree)
        
    def compile_repeat_with(self, tree, code):
        "Compile a repeatWith statement."
        #
        #   repeatWith i in Lower..Upper {BODY}
        #
        # Compiles to code corresponding to
        # the following fragment:
        #
        #   i := Lower
        #   upper0 := Upper
        #   if (i <= upper0) {
        #     while (true) {
        #        {BODY}
        #        if (i == upper0) break;
        #        i := next(i)
        #     }
        #   }
        #
        def call_next():
            """Add a VM instruction for calling the builtin 'next' function,
which operates on any iterable value.
"""
            name = i18n.i18n('next')
            if hasattr(tree, 'index_type_annotation'):
                name = lang.gbs_builtins.polyname(
                    name,
                    [repr(tree.index_type_annotation)])
            code.push(('call', name, 1), near=tree)

        # upper0 is preserved in the stack
        i = tree.children[1].value
        limit_lower = tree.children[2].children[1]
        limit_upper = tree.children[2].children[2]
        body = tree.children[3]
        upper0 = self.temp_varname()
        lbegin = GbsLabel()
        lend = GbsLabel()
        # i := Lower
        self.compile_expression(limit_lower, code)
        code.push(('popTo', i), near=tree)
        code.push(('setImmutable', i), near=tree)
        # upper0 := Upper
        self.compile_expression(limit_upper, code)
        code.push(('popTo', upper0), near=tree)
        # if i <= upper0
        code.push(('pushFrom', i), near=tree)
        code.push(('pushFrom', upper0), near=tree)
        code.push(('call', '<=', 2), near=tree)
        code.push(('jumpIfFalse', lend), near=tree)
        # while true
        code.push(('label', lbegin), near=tree)
        # body
        self.compile_block(body, code)
        # if (i == upper0) break
        code.push(('pushFrom', i), near=tree)
        code.push(('pushFrom', upper0), near=tree)
        code.push(('call', '/=', 2), near=tree)
        code.push(('jumpIfFalse', lend), near=tree)
        # i := next(i)
        code.push(('pushFrom', i), near=tree)
        call_next()
        code.push(('unsetImmutable', i), near=tree)
        code.push(('popTo', i), near=tree)
        code.push(('setImmutable', i), near=tree)
        # end while
        code.push(('jump', lbegin), near=tree)
        code.push(('label', lend), near=tree)
        code.push(('delVar', i), near=tree)

    def compile_block(self, tree, code):
        "Compile a block statement."
        self.compile_commands(tree.children[1], code)

    def compile_return(self, tree, code):
        "Compile a return statement."
        vals = tree.children[1].children 
        for val in vals:
            self.compile_expression(val, code)
        if self._current_def_name == 'program':
            vrs = []
            expr_count = 1
            for v in tree.children[1].children:
                if v.children[0] == 'varName':
                    vrs.append(v.children[1].value)
                else:
                    vrs.append("#%s" % (expr_count,)) 
                expr_count += 1
                    
            if hasattr(tree, 'type_annot'):
                # Decorate the return variables with their types.
                types = [
                    repr(subtype)
                    for subtype in tree.type_annot.subtypes()
                ]
                vrs = [
                    lang.gbs_builtins.polyname(vname, [vtype])
                    for vname, vtype in zip(vrs, types)
                ]
            code.push(('returnVars', len(vals), vrs), near=tree)
        else:
            code.push(('return', len(vals)), near=tree)
    
    #### Expressions

    def compile_expression(self, tree, code):
        "Compile an expression."
        exptype = tree.children[0]
        dispatch = {
          'or': self.compile_or,
          'and': self.compile_and,
          'not': self.compile_not,
          'relop': self.compile_binary_op,
          'addsub': self.compile_binary_op,
          'mul': self.compile_binary_op,
          'divmod': self.compile_binary_op,
          'pow': self.compile_binary_op,
          'listop': self.compile_binary_op,
          'projection': self.compile_binary_op,
          'constructor': self.compile_func_call,
          'varName': self.compile_var_name,
          'funcCall': self.compile_func_call,
          'match': self.compile_match,
          'unaryMinus': self.compile_unary_minus,
          'literal': self.compile_literal,
          'type': self.compile_type,
        }
        if exptype in dispatch:
            dispatch[exptype](tree, code)
        else:
            msg = i18n.i18n('Unknown expression: %s') % (exptype,)
            area = common.position.ProgramAreaNear(tree)
            raise GbsCompileException(msg, area)

    def get_type_annotation(self, tree):
        if hasattr(tree, 'type_annotation'):
            return tree.type_annotation
        else:
            return None

    def compile_binary_op(self, tree, code):
        "Compile a binary operator expression."
        type_annotation = self.get_type_annotation(tree)
        self.compile_expression(tree.children[2], code)
        self.compile_expression(tree.children[3], code)
        code.push(('call', tree.children[1].value, 2), near=tree)

    def compile_not(self, tree, code):
        "Compile a boolean not expression."
        self.compile_expression(tree.children[1], code)
        code.push(('call', 'not', 1), near=tree)

    def compile_or(self, tree, code):
        "Compile a short-circuiting disjunction."
        lcontinue = GbsLabel()
        lend = GbsLabel()
        type_annotation = self.get_type_annotation(tree)
        
        self.compile_expression(tree.children[2], code)
            
        code.push(('jumpIfFalse', lcontinue), near=tree)
        code.push(('pushConst', lang.gbs_builtins.parse_constant('True')),
                  near=tree)
        code.push(('jump', lend), near=tree)
        code.push(('label', lcontinue), near=tree)
        self.compile_expression(tree.children[3], code)
        code.push(('label', lend), near=tree)

    def compile_and(self, tree, code):
        "Compile a short-circuiting conjunction."
        lcontinue = GbsLabel()
        lend = GbsLabel()
        type_annotation = self.get_type_annotation(tree)
        self.compile_expression(tree.children[2], code)
        code.push(('jumpIfFalse', lcontinue), near=tree)
        self.compile_expression(tree.children[3], code)
        code.push(('jump', lend), near=tree)
        code.push(('label', lcontinue), near=tree)
        code.push(('pushConst', lang.gbs_builtins.parse_constant('False')),
                  near=tree)
        code.push(('label', lend), near=tree)

    def compile_unary_minus(self, tree, code):
        "Compile a unary minus expression."
        funcname = 'unary-'
        args = tree.children[1:]
        self._compile_func_call_poly(tree, funcname, args, code)

    def compile_var_name(self, tree, code):
        "Compile a variable name expression."        
        offsets = tree.children[2].children
        var = tree.children[1].value
        code.push(('pushFrom', var), near=tree)      
        if len(offsets) > 0:
            self.compile_projectable_var_check(tree, code, var)
            #calculate assignment reference                   
            for offset in offsets:                
                self.compile_expression(offset.children[1], code)            
                code.push(('call', '_getRef', 2), near=tree)
            code.push(('call', '_getRefValue', 1), near=tree)        

    def compile_func_call(self, tree, code):
        "Compile a function call."
        funcname = tree.children[1].value
        args = tree.children[2].children
        if lang.gbs_builtins.is_defined(funcname) or funcname in self.user_defined_routine_names:
            self._compile_func_call_poly(tree, funcname, args, code)
        else:
            self._compile_field_getter(tree, funcname, args, code)

    def _compile_field_getter(self, tree, field_name, args, code):
        self.compile_expression(args[0], code)
        field = tree.children[1]
        field.type = 'symbol'        
        code.push(('pushConst', parse_literal(field)), near=tree)
        code.push(('call', '_get_field', 2), near=tree)

    def _compile_func_call_poly(self, tree, funcname, args, code):
        "Compile a potentially polymorphic function call."
        polys = lang.gbs_builtins.BUILTINS_POLYMORPHIC
        annotate = True
        annotate = annotate and funcname in polys
        annotate = annotate and hasattr(tree, 'type_annotation')
        annotate = annotate and isinstance(tree.type_annotation, list)
        
        type_annotation = None
        if hasattr(tree, 'type_annotation'):
            type_annotation = tree.type_annotation
        
        for i, arg in zip(range(len(args)),args):
            self.compile_expression(arg, code)
                
        if annotate:
            funcname = lang.gbs_builtins.polyname(
                funcname,
                [repr(ann) for ann in tree.type_annotation])
        code.push(('call', funcname, len(args)), near=tree)

    def compile_literal(self, tree, code):
        "Compile a constant expression."
        tok = tree.children[1]
        code.push(('pushConst', parse_literal(tok)), near=tree)

def compile_program(tree):
    "Compile a full Gobstones program."
    compiler = GbsCompiler()
    return compiler.compile_program(tree)

