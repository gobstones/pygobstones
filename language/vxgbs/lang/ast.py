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

"""Abstract syntax tree representation.
Includes the implementation of the semantic actions in the parser.
"""
from itertools import groupby
import common.i18n as i18n
import common.position
import common.utils
import lang.bnf_parser
import lang.gbs_builtins
import copy

def fix_string_literal(node):
    if node.children[1].type == 'string':
        node.children[1].value = node.children[1].value.strip('"')
    return node

def _tree_insert_left(operator_type, opr1, arg1, right):
    """Convert trees of the form:

   arg1 opr1 (arg2 opr2 arg3)
             |--- right ----|

into trees of the form:

   (arg1 opr1 arg2) opr2 arg3
   |---- left ----|

whenever "right" is of the form (arg2 opr2 arg3)
with the operator type of right is `operator_type`.
"""
    if isinstance(right, ASTNode) and right.children[0] == operator_type:
        # Swap to left
        opr2 = right.children[1]
        arg2 = right.children[2]
        arg3 = right.children[3]
        left = _tree_insert_left(operator_type, opr1, arg1, arg2)
        return ASTNode(
            [operator_type, opr2, left, arg3],
            arg1.pos_begin,
            right.pos_end)
    else:
        # Do not swap
        return ASTNode(
            [operator_type, opr1, arg1, right],
            arg1.pos_begin,
            right.pos_end)

def _is_range_expr(node):
    return len(node.children) in [3,4] and node.children[-2] == 'range_to'

def _make_range_generator(expr_range):
    pos_b = expr_range.pos_begin
    pos_e = expr_range.pos_end
    
    if len(expr_range.children) == 4:
        first, second, _, last = expr_range.children
    elif len(expr_range.children) == 3:
        first, _, last = expr_range.children
        second = ASTNode(['literal',
                          lang.bnf_parser.Token('symbol', 'NoSecondElementForRange', pos_b, pos_e)], 
                          pos_b, pos_e)
    else:
        assert False
        
    return ASTNode(['funcCall',
                   lang.bnf_parser.Token('lowerid', '_range', pos_b, pos_e),
                   ASTNode([first, last, second], pos_b, pos_e)
                  ], pos_b, pos_e)

def _make_list_expression(expr_list):
    """Convert a list of expressions [e1, ..., eN] into an
    expression representing a Gobstones list, of the form:
        cons(e1, ... cons(eN, nil) ... )
    """
    pos_b = expr_list.pos_begin
    pos_e = expr_list.pos_end
    lst = expr_list.children
    ret = ASTNode(['funcCall',
                   lang.bnf_parser.Token('lowerid', '[]', pos_b, pos_e),
                   ASTNode([], pos_b, pos_e)
                  ], pos_b, pos_e)
    for exp in common.utils.seq_reversed(lst):
        pos_b = exp.pos_begin
        pos_e = exp.pos_end
        exp_list = ASTNode(['funcCall',
                           lang.bnf_parser.Token('lowerid', '[x]', pos_b, pos_e),
                           ASTNode([exp], pos_b, pos_e)
                           ], pos_b, pos_e)
        ret = ASTNode(['listop',
                       lang.bnf_parser.Token('lowerid', '++', pos_b, pos_e),
                       exp_list, 
                       ret], pos_b, pos_e)
    return ret

def _concat_internal_list_generators(expr_list):
    return expr_list

def _infixl(subtrees, action):
    "Expands an action corresponding to an INFIXL declaration."
    # arg1 opr1 (arg2 opr2 arg3)  --->  (arg1 opr1 arg2) opr2 arg3
    #           |---- right ---|        |---- left ----|
    operator_type = action[1]
    arg1 = subtrees[1]
    opr1_args = subtrees[2]
    if opr1_args is None:
        return arg1
    opr1 = opr1_args.children[1]
    right = opr1_args.children[2]
    return _tree_insert_left(operator_type, opr1, arg1, right)

def _infixr(subtrees, action):
    "Expands an action corresponding to an INFIXR declaration."
    # arg1 opr arg2
    operator_type = action[1]
    arg1 = subtrees[1]
    opr_arg2 = subtrees[2]
    if opr_arg2 is None:
        return arg1
    opr = opr_arg2.children[1]
    arg2 = opr_arg2.children[2]
    return ASTNode([operator_type, opr, arg1, arg2],
                   arg1.pos_begin,
                   arg2.pos_end)

class ASTNode(common.position.ProgramElement):
    "Represents an internal node of an abstract syntax tree."

    def __init__(self, children, pos_begin, pos_end):
        common.position.ProgramElement.__init__(self)
        
        # A node is represented by a list
        # - its first element is a label
        # - the remaining elements are the actual children
        self.children = children
        self.pos_begin = pos_begin
        self.pos_end = pos_end

        # Used by the static analysis tool
        self.live_in = None
        self.live_out = None
        self.live_gen = None
        self.annotations = {}

    def __repr__(self):
        return 'AST(' + repr(self.children) + ')'

    def clone(self):
        """ Return a shallow copy of this ASTNode """
        return copy.copy(self)

    def first_child(self):
        """ Return the first child, skipping None children that
        may arise from optional elements in the grammar.
        """
        for child in self.children[1:]:
            if child is None:
                continue
            return child
        return None

    def description(self):
        """ Return a string describing the AST node, with text
        suitable for referring to the node in error reporting or other
        human interface.
        """
        if self.children == []:
            return ''
        head = self.children[0]
        if isinstance(head, str):
            if head in i18n.AST_type_descriptions:
                return i18n.AST_type_descriptions[head]
            else:
                return head
        else:
            return head.description()

    def has_children(self):
        "Return True (every internal AST node has children)."
        return True

    def show_liveness_info(self):
        """Return a string, showing liveness annotations made at
this node by the static analysis tool.
"""
        live_in = ''
        if self.live_in is not None:
            live_in = ''.join([
                '{live_in: ',
                str(' '.join(common.utils.seq_sorted(self.live_in.keys()))),
                '}'
            ])
        live_out = ''
        if self.live_out is not None:
            live_out = ''.join([
                '{live_out: ',
                str(' '.join(common.utils.seq_sorted(self.live_out.keys()))),
                '}'
            ])
        return live_in, live_out

    def show_ast(self, indent=0, show_liveness=False):
        """Return a string, result of pretty printing the full
AST starting at this node, with the given indentation.

If show_liveness is True, also show the annotations made
at nodes by the static analysis tool.
"""
        def pretty_print(elem, i=indent + 1):
            "Pretty print an AST node or other elements."
            tabulation = '    ' * i
            if elem is None:
                return tabulation + 'None'
            elif isinstance(elem, str):
                return tabulation + elem
            else:
                # Is an AST
                return elem.show_ast(i, show_liveness=show_liveness)

        def pretty_print_list(elem_list):
            "Pretty print a list of AST nodes or other elements."
            lst = [pretty_print(elem) for elem in elem_list if elem != '']
            return '\n'.join(lst)

        tabulation = '    ' * indent
        if show_liveness:
            live_in, live_out = self.show_liveness_info()
        else:
            live_in, live_out = '', ''
        if len(self.children) == 0:
            return ''.join([
                tabulation,
                'AST(',
                pretty_print_list([live_in, live_out]),
                ')'
            ])
        elif isinstance(self.children[0], str):
            return ''.join([
                tabulation,
                'AST(',
                self.children[0],
                '\n',
                pretty_print_list([live_in] + self.children[1:] + [live_out]),
                ')'
            ])
        else:
            return ''.join([
                '    ' * indent,
                'AST(\n',
                pretty_print_list([live_in] + self.children + [live_out]),
                ')'
            ])


class ASTBuilder(object):
    "Class to build an abstract syntax tree from a source string."

    def __init__(self, starting_position=None):
        self.starting_position = starting_position

    def _expand_action_part(self, subtrees, action_part, uniq=False):
        "Expands a part of an action to synthetize an AST."
        if action_part == '[]':
            return ASTNode(
                [],
                self._pos_begin(subtrees),
                self._pos_end(subtrees))
        elif action_part == 'None':
            return None
        elif action_part[0] == '[' and action_part[-1] == ']':
            lst = [self._expand_action_part(subtrees, action_part[1:-1])]
            return ASTNode(
                lst,
                self._pos_begin(subtrees),
                self._pos_end(subtrees))
        elif action_part[0] == '$':
            pos_b = self._pos_begin(subtrees)
            pos_e = self._pos_end(subtrees)
            subs = subtrees[int(action_part[1:])]
            if uniq and subs is not None:
                subs.pos_begin = pos_b
                subs.pos_end = pos_e
            return subs
        else:
            return action_part

    def _pos_begin(self, subtrees):
        """Returns the position where the first nonempty element of
`subtrees` occurs.
"""
        for subtree in subtrees:
            if subtree is None or isinstance(subtree, str):
                continue
            return subtree.pos_begin
        return self.starting_position

    def _pos_end(self, subtrees):
        """Returns the position where the last nonempty element of
`subtrees` occurs.
"""
        for subtree in common.utils.seq_reversed(subtrees):
            if subtree is None or isinstance(subtree, str):
                continue
            return subtree.pos_end
        return self.starting_position

    def _expand_action(self, subtrees, action):
        "Expands an action to synthetize an AST."
        if action is None:
            if len(subtrees) == 2:
                return subtrees[1]
            else:
                return subtrees
        elif len(action) == 1:
            return self._expand_action_part(subtrees, action[0], uniq=True)
        else:
            dispatch = {
                '++': self._expand_action_concatenate,
                'INFIXL': _infixl,
                'INFIXR': _infixr,
                'NEGATE': self._expand_action_negate,
                'MKFIELD': self._expand_action_mkfield,
                'SYMBOL': self._expand_action_symbol,
                'RISSYMBOL': self._expand_action_right_is_symbol,
                'LIST': self._expand_action_list,
                'varName/funcCall': self._expand_action_varname_funccall,
                'procedure': self._expand_action_procedure_def,
                'entrypoint': self._expand_action_entrypoint_def,
                'procCall/assignVarName': self._expand_action_proccall_assignvarname,
                'literal/construct': self._expand_action_literal_or_construct,
                'CONSTRUCTFIELDS': self._expand_action_constructfields,
            }
            expand = dispatch.get(action[0], self._expand_action_default)
            return expand(subtrees, action)

    def _expand_action_constructfields(self, subtrees, action):
        """Expands the constructor arguments"""
        pos_b = self._pos_begin(subtrees)
        pos_e = self._pos_end(subtrees)
        
        # Fields assocs and a given record expression
        if subtrees[2].children[0] == 'funcCall':
            return ASTNode(['recordSuchAs',
                            subtrees[1],
                            subtrees[2]],
                           pos_b, pos_e)
        # Normal field assocs
        else:
            symbol_tok = subtrees[1].children[1]
            symbol_tok.type = 'symbol'
            firstf = ASTNode(['funcCall',
                              lang.bnf_parser.Token('lowerid', '_mk_field', pos_b, pos_e),
                              ASTNode([ASTNode(['literal',
                                                symbol_tok], 
                                                pos_b, pos_e), 
                                       subtrees[2].children[1]], 
                                      pos_b, 
                                      pos_e)],
                             pos_b,
                             pos_e,)
            return ASTNode([firstf] + subtrees[3].children,
                           pos_b,
                           pos_e)
    
    
    def _expand_action_concatenate(self, subtrees, action):
        """Expands a ++ action: concatenate synthetized results."""
        value = []
        expansion = [
                self._expand_action_part(subtrees, a)
                for a in action[1:]
        ]
        for elem in expansion:
            value.extend(elem.children)
        return ASTNode(
                value,
                self._pos_begin(subtrees),
                self._pos_end(subtrees))

    def _expand_action_negate(self, subtrees, action):
        """Expands a NEGATE action: negate synthetized result."""
        value = self._expand_action_part(subtrees, action[1])
        return value.negate()

    def _expand_action_list(self, subtrees, action):
        """Expands a LIST action, creating a list expression,
        of the form: cons(x1, ... cons(xN, nil) ...), or reducing
        list generators like ".." from [x1..x2] to x1..x2; or
        [x1,x2..x3] to x1,x2..x3        
        """
        
        expanded = self._expand_action_part(subtrees, action[1])
        if _is_range_expr(expanded):
            return _make_range_generator(expanded)
        else:
            return _make_list_expression(expanded)

    def _expand_action_right_is_symbol(self, subtrees, action):
        """ Expand a RISSYMBOL action to build a symbol from right expression """
        def expand_right_as_symbol(node):        
            if node.children[1].value != '.':            
                node = self._expand_action_symbol(node.children, action)
            else:
                node.children[2] = expand_right_as_symbol(node.children[2])
            return node
        
        if not subtrees[2] is None:
             subtrees[2].children[2] = expand_right_as_symbol(subtrees[2].children[2])
        
        expanded = _infixl(subtrees, ['INFIXL'] + action[1:])
        return expanded

    def _expand_action_mkfield(self, subtrees, action):
        """ Expand a funcCall action to build a funcCall ASTNode """
        pos_b = self._pos_begin(subtrees)
        pos_e = self._pos_end(subtrees)
        params = [self._expand_action_part(subtrees, action[i]) for i in range(len(action))[1:]]
        return ASTNode(['funcCall',
                   lang.bnf_parser.Token('lowerid', '_mk_field', pos_b, pos_e),
                   ASTNode(params, pos_b, pos_e)
                  ], pos_b, pos_e)

    def _expand_action_symbol(self, subtrees, _):
        """ Expand a SYMBOL action to build a literal #str node """
        tok = subtrees[1]
        tok.type = "symbol"
        return ASTNode(['literal',
                        tok],
                        self._pos_begin(subtrees),
                        self._pos_end(subtrees))

    def _expand_action_literal_or_construct(self, subtrees, action):
        """Expands a literal/construct, transforming "literal/construct"
        action into either a "literal", "recConstruct" or "ArrayConstruct" node."""
        if subtrees[1].type == 'upperid' and not lang.gbs_builtins.is_builtin_constant(subtrees[1].value):
            return self._make_construct_expression(subtrees)
        else:
            return fix_string_literal(ASTNode(
                ['literal', subtrees[1]],
                self._pos_begin(subtrees),
                self._pos_end(subtrees)))
            

    def _make_construct_expression(self, expr_construct):
        pos_b = self._pos_begin(expr_construct)
        pos_e = self._pos_end(expr_construct)
        constructor_type = ASTNode(['type', expr_construct[1]], pos_b, pos_e)
        
        from_value = None
        if len(expr_construct[2].children) > 0 and expr_construct[2].children[0] == 'recordSuchAs':
            fields = _make_list_expression(ASTNode([expr_construct[2].children[2]], pos_b, pos_e))
            from_value = expr_construct[2].children[1] 
        else:
            fields = _make_list_expression(expr_construct[2])
            
        if constructor_type.children[1].value == 'Arreglo':
            return ASTNode(['funcCall',
                            lang.bnf_parser.Token('lowerid', '_mkArray', pos_b, pos_e),
                            ASTNode([constructor_type,
                                     fields], pos_b, pos_e),                                                        
                            ], pos_b, pos_e)
        else:
            if not (len(expr_construct[2].children) > 0 and expr_construct[2].children[0] == 'recordSuchAs'):
                return ASTNode(['constructor',
                            lang.bnf_parser.Token('lowerid', '_construct', pos_b, pos_e),
                            ASTNode([constructor_type,
                                     fields],
                                    pos_b, 
                                    pos_e),
                            ], pos_b, pos_e)
            else:
                return ASTNode(['constructor',
                            lang.bnf_parser.Token('lowerid', '_construct_from', pos_b, pos_e),
                            ASTNode([constructor_type,
                                     fields,
                                     from_value],
                                    pos_b, 
                                    pos_e),
                            ], pos_b, pos_e)
                
            
    
    def _expand_action_proccall_assignvarname(self, subtrees, _):
        """Expands a procCall/assignVarName, transforming "procCall/assignVarName"
        action into either a "procCall" or a "assignVarName" node."""
        content = subtrees[1].children
        if len(content) > 2 and len(content[2].children) > 0 and content[2].children[0] == 'procCall':
            proccall = content[2]
            params = proccall.children[2]
            var = content[1]
            if len(var.children) < 3:
                var.children = var.children + [ASTNode([], self._pos_begin(subtrees), self._pos_end(subtrees))]            
            params.children.insert(0, var)         
            content[2].annotations['explicit_board'] = True   
            return content[2]
        else:            
            return ASTNode(
                content,
                self._pos_begin(subtrees),
                self._pos_end(subtrees))
        
    def _expand_action_procedure_def(self, subtrees, _):
        """Expands a procedure definition inserting inout parameter to 
        params list."""
        procname = subtrees[3]
        params = subtrees[4]
        proctype = subtrees[5]
        body = subtrees[6]
        procVar = subtrees[2]
        
        result = ASTNode(
            ['procedure', procname, params, body, proctype],
            self._pos_begin(subtrees),
            self._pos_end(subtrees))
        result.annotations["varProc"] = procVar
        
        if not procVar is None:
            params.children.insert(0, procVar.children[1])            
                
        return result 
        
    def _expand_action_entrypoint_def(self, subtrees, _):
        """Expands a procedure definition inserting inout parameter to 
        params list."""
        
        if isinstance(subtrees[1], lang.bnf_parser.Token) and subtrees[1].value == 'interactive':        
            epvar = subtrees[2]
            epname = subtrees[1]
            body = subtrees[5]
        else:
            epvar = subtrees[1]
            epname = subtrees[2]
            body = subtrees[4]
        params = ASTNode([],self._pos_begin(subtrees), self._pos_end(subtrees))
        eptype = None
        if not epvar is None and len(epvar.children) != 0:
            params.children.insert(0, epvar.children[1])
        result = ASTNode(
            ['entrypoint', epname, params, body, eptype],
            self._pos_begin(subtrees),
            self._pos_end(subtrees))
        result.annotations["varProc"] = epvar
        return result
    
    def _expand_action_varname_funccall(self, subtrees, _):
        """Expands a varName/funcCall, transforming "varName/funcCall"
        action into either a "varName" or a "funcCall" node."""
        if subtrees[2] is None:
            if hasattr(subtrees[1], "children"):
                children = subtrees[1].children
            else:
                children = []
            return ASTNode(
                ['varName'] + children,
                self._pos_begin(subtrees),
                self._pos_end(subtrees))
        else:
            return ASTNode(
                ['funcCall', subtrees[1].children[0], subtrees[2]],
                self._pos_begin(subtrees),
                self._pos_end(subtrees))

    def _expand_action_default(self, subtrees, action):
        """Expands a default action: create a node labeled with the
first children.
"""
        children = [
                self._expand_action_part(subtrees, a)
                for a in action
        ]
        return ASTNode(
                children,
                self._pos_begin(subtrees),
                self._pos_end(subtrees))

    def build_ast_from(self, parsing_stream):
        "Synthetizes an AST from a parsing stream."
        prods = []
        trees = []
        for event, symbol, expansion in parsing_stream:
            is_consume = event == 'CONSUME' 
            is_empty_produce = event == 'PRODUCE' and expansion.rule == ('',)
            if is_consume or is_empty_produce:
                if is_consume:
                    value = expansion
                    self.starting_position = expansion.pos_end
                else:
                    value = None
                while prods != []:
                    cur_prod = prods[-1]
                    cur_prod[1].pop(0)
                    cur_tree = trees[-1]
                    cur_tree.append(value)
                    if cur_prod[1] == []:
                        prods.pop()
                        action = cur_prod[0]
                        subtrees = trees.pop()
                        value = self._expand_action(subtrees, action)
                    else:
                        break
                if prods == []:
                    return value
            else:
                assert event == 'PRODUCE' and expansion.rule != ('',)
                prods.append((expansion.action, list(expansion.rule)))
                trees.append([symbol])
        assert False

