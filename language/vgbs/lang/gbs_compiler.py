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
    val = lang.gbs_builtins.parse_constant(tok.value)
    assert val is not None
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

    def compile_program(self, tree, module_prefix=''):
        """Given an AST for a full program, compile it to virtual machine
code, returning an instance of lang.gbs_vm.GbsCompiledProgram.
The Main module should be given the empty module prefix ''.
Every other module should be given the module name as a prefix.
"""
        self.module_handler = tree.module_handler
        self.compile_imported_modules(tree)

        imports = tree.children[1].children
        defs = tree.children[2]

        self.code = lang.gbs_vm.GbsCompiledProgram(
                        tree, module_prefix=module_prefix)
        self.compile_imports(imports)
        self.compile_defs(defs)
        return self.code

    def compile_imported_modules(self, tree):
        "Recursively compile the imported modules."
        for mdl_name, mdl_tree in self.module_handler.parse_trees():
            compiler = GbsCompiler()
            try:
                code = compiler.compile_program(
                           mdl_tree, module_prefix=mdl_name
                       )
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
                mdl_code = self.module_handler.compiled_code_for(mdl_name)
                if rtn.value in mdl_code.routines:
                    self.code.external_routines[rtn.value] = (
                        mdl_code,
                        mdl_code.routines[rtn.value]
                    )
                else:
                    assert rtn.value in mdl_code.external_routines
                    val = mdl_code.external_routines[rtn.value]
                    self.code.external_routines[rtn.value] = val

    def compile_defs(self, tree):
        "Compile a list of definitions."
        self.temp_counter = 0
        for def_ in tree.children:
            self.compile_def(def_)
                    
    def temp_varname(self):
        "Make a temporary variable name."
        self.temp_counter += 1
        return '_tempvar%i' % (self.temp_counter)

    def compile_def(self, tree):
        "Compile a single definition."
        prfn = def_helper.get_def_keyword(tree)
        name = def_helper.get_def_name(tree).value
        self._current_def_name = name
        params = [param.value for param in def_helper.get_def_params(tree)]
        code = lang.gbs_vm.GbsCompiledCode(tree, prfn, name, params)
        code.add_enter()
        self.compile_commands(def_helper.get_def_body(tree), code)
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
            'foreach': self.compile_foreach,
            'block': self.compile_block,
            'return': self.compile_return,
        }
        assert command in dispatch
        dispatch[command](tree, code)

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
        for arg in args:
            self.compile_expression(arg, code)
        code.push(('call', procname, len(args)), near=tree)

    def compile_assign_var_name(self, tree, code):
        "Compile a variable assignment: var := <expr>"
        self.compile_expression(tree.children[2], code)
        code.push(('popTo', tree.children[1].value), near=tree)

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
        # value0 := value
        self.compile_expression(value, code)
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
            code.push(('call', i18n.i18n('_isEmpty'), 1), near=tree)
            code.push(('call', 'not', 1), near=tree)
            code.push(('jumpIfFalse', label), near=tree)
        def head(listVar, var):
            code.push(('pushFrom', listVar), near=tree)
            code.push(('call', i18n.i18n('_head'), 1), near=tree)
            code.push(('popTo', var), near=tree)
        def tail(listVar, var):
            code.push(('pushFrom', listVar), near=tree)
            code.push(('call', i18n.i18n('_tail'), 1), near=tree)
            code.push(('popTo', var), near=tree)
        
        
        foreach_type = tree.children[2].children[0]
        index = tree.children[1].value
        body = tree.children[3]
        xs0 = self.temp_varname()
        lbegin = GbsLabel()
        lend = GbsLabel()
        lend2 = GbsLabel()
        # xs0 := <List>
        if foreach_type == 'enum':
            self.compile_foreach_sequence(tree, code)
        elif foreach_type == 'range':
            self.compile_foreach_range(tree, code)
        else:
            assert False            
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

    def compile_foreach_sequence(self, tree, code):
        "Compile a foreach's sequence."          
        sequence = tree.children[2].children[1:] 
        code.push(('call', i18n.i18n('[]'), 0), near=tree)
        for element in sequence:
            self.compile_expression(element, code)
            code.push(('call', i18n.i18n('_snoc'), 2), near=tree)
    
    def compile_foreach_range(self, tree, code):
        "Compile a foreach's range."
        _, range_first, range_last, range_second = tree.children[2].children
        self.compile_expression(range_first, code)
        self.compile_expression(range_last, code)
        if not range_second is None: 
            self.compile_expression(range_second, code)
        else:
            self.compile_expression(range_first, code)
            code.push(('call', i18n.i18n('next'), 1), near=tree)
        code.push(('call', i18n.i18n('_range'), 3), near=tree)

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
          'varName': self.compile_var_name,
          'funcCall': self.compile_func_call,
          'unaryMinus': self.compile_unary_minus,
          'literal': self.compile_literal,
        }
        assert exptype in dispatch
        dispatch[exptype](tree, code)

    def compile_binary_op(self, tree, code):
        "Compile a binary operator expression."
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
        code.push(('pushFrom', tree.children[1].value), near=tree)

    def compile_func_call(self, tree, code):
        "Compile a function call."
        funcname = tree.children[1].value
        args = tree.children[2].children
        self._compile_func_call_poly(tree, funcname, args, code)

    def _compile_func_call_poly(self, tree, funcname, args, code):
        "Compile a potentially polymorphic function call."
        polys = lang.gbs_builtins.BUILTINS_POLYMORPHIC
        annotate = True
        annotate = annotate and funcname in polys
        annotate = annotate and hasattr(tree, 'type_annotation')
        annotate = annotate and isinstance(tree.type_annotation, list)
        for arg in args:
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

