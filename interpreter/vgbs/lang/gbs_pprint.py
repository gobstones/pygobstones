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


#### Not-quite-pretty printing

def llen(s):
  return len(s.split('\n')[-1])

class GbsPrettyPrinter(object):
  "Pretty printer for Gobstones programs."
  def __init__(self, width=70, indentation_width=4):
    self.width = width
    self.indentation_width = indentation_width

  def join_fit_map(self, indent, sep, args, func):  
    wsep = ''
    ind = ''
    lines = []

    # deal with indentation exceeding right margin
    indent_ex = False
    if indent > self.width:
      indent_ex = True
      lines.append('')
    while indent > self.width - 4 * self.indentation_width:
      indent -= self.indentation_width
    if indent_ex:
      ind = indent * ' '

    s = '' 
    for a in args:
      if indent + len(s) + len(wsep) < self.width:
        s1 = s + wsep + func(a, indent + len(s) + len(wsep))
      else:
        s1 = None
      if s1 is not None and llen(s1) < self.width:
        s = s1
      else:
        s += wsep
        lines.append(ind + s)
        s = func(a, indent)
        ind = indent * ' '
      wsep = sep
    if s != '':
      lines.append(ind + s)
    return '\n'.join(lines)

  def join_fit(self, indent, sep, args):
    return self.join_fit_map(indent, sep, args, lambda a, l: a)

  def pprint_program(self, tree, print_imports=True):
    imports = tree.children[1].children
    defs = tree.children[2]
    s = ''
    if print_imports and len(imports) > 0:
      s += self.pprint_imports(imports)
      s += '\n'
    s += self.pprint_defs(defs)
    return s

  def pprint_imports(self, imports):
    res = []
    for imp in imports:
      res.append(self.pprint_import(imp))
    return '\n'.join(res)

  def pprint_import(self, tree):
    mdl_name = tree.children[1].value
    rtns = tree.children[2].children
    s = 'from %s import (' % (mdl_name,)
    s += self.join_fit_map(llen(s), ', ', rtns, self.pprint_rtn_name)
    s += ')\n'
    return s

  def pprint_rtn_name(self, tree, start_col):
    return tree.value

  def pprint_defs(self, tree):
    return '\n\n'.join([self.pprint_def(x) for x in tree.children])

  def pprint_def(self, tree):
    prfn, name, params, body, type_decl = tree.children
    head = '%s %s' % (prfn, name.value)
    head += '('
    head += self.join_fit(len(head), ', ', [p.value for p in params.children])
    head += ')'
    s = '%s ' % (head,)
    if type_decl is not None:
      s += ':: '
      s += self.pprint_type(type_decl, llen(s))
      s += ' '
    s += '\n{\n'
    self.level = 1
    s += self.pprint_commands(body)
    s += '}'
    return s

  def pprint_commands(self, tree):
    if tree.children == []:
      trail = ''
    else:
      trail = '\n'
    return '\n'.join([self.pprint_cmd(x) for x in tree.children]) + trail

  def indent(self):
    return ' ' * self.level * self.indentation_width

  def pprint_cmd(self, tree):
    command = tree.children[0]
    dispatch = {
      'Skip': self.pprint_Skip,
      'THROW_ERROR': self.pprint_THROW_ERROR,
      'procCall': self.pprint_procCall,
      'assignVarName': self.pprint_assignVarName,
      'assignVarTuple1': self.pprint_assignVarTuple1,
      'if': self.pprint_if,
      'case': self.pprint_case,
      'while': self.pprint_while,
      'repeat': self.pprint_repeat,
      'foreach': self.pprint_foreach,
      'block': self.pprint_block,
      'return': self.pprint_return,
    }
    return dispatch[command](tree)

  def pprint_Skip(self, tree):
    return self.indent() + 'Skip'

  def pprint_THROW_ERROR(self, tree):
    return self.indent() + 'THROW_ERROR(' + tree.children[1].value + ')'

  def pprint_procCall(self, tree):
    s = self.indent() + tree.children[1].value + '('
    vals = tree.children[2].children
    s += self.join_fit_map(llen(s), ', ', vals, self.pprint_expression)
    s += ')'
    return s

  def pprint_assignVarName(self, tree):
    s = self.indent() + tree.children[1].value + ' := '
    s += self.pprint_expression(tree.children[2], llen(s))
    return s

  def pprint_assignVarTuple1(self, tree):
    varnames = [v.value for v in tree.children[1].children]
    s = self.indent() + '('
    s += self.join_fit(llen(s), ', ', varnames)
    s += ') := '
    s += self.pprint_funcCall(tree.children[2], llen(s))
    return s

  def pprint_if(self, tree):
    s = self.indent() + 'if ('
    s += self.pprint_expression(tree.children[1], llen(s))
    s += ') '
    s += self.pprint_block_noindent(tree.children[2])
    if tree.children[3] is not None:
      s += ' else '
      s += self.pprint_block_noindent(tree.children[3])
    return s

  def pprint_case(self, tree):
    ss = []
    s = self.indent() + 'case ('
    s += self.pprint_expression(tree.children[1], llen(s))
    s += ') of'
    ss.append(s)
    self.level += 1
    for branch in tree.children[2].children:
      if branch.children[0] == 'branch':
        lits = [l.value for l in branch.children[1].children]
        s = self.indent()
        s += self.join_fit(len(s), ', ', lits)
        s += ' -> '
        s += self.pprint_block_noindent(branch.children[2])
      else: # defaultBranch
        s = self.indent() + '_ -> '
        s += self.pprint_block_noindent(branch.children[1])
      ss.append(s)
    self.level -= 1
    return '\n'.join(ss)

  def pprint_while(self, tree):
    s = self.indent() + 'while ('
    s += self.pprint_expression(tree.children[1], llen(s))
    s += ') '
    s += self.pprint_block_noindent(tree.children[2])
    return s
  
  def pprint_repeat(self, tree):
    s = self.indent() + 'repeat '
    s += self.pprint_expression(tree.children[1], llen(s))
    s += ' '
    s += self.pprint_block_noindent(tree.children[2])
    return s
  def pprint_foreach(self, tree):
    s = self.indent() + 'foreach '
    s += tree.children[1].value
    s += ' in '
    from_ = tree.children[2].children[1]
    to_ = tree.children[2].children[2]
    s += self.pprint_expression(from_, llen(s))
    s += '..'
    s += self.pprint_expression(to_, llen(s))
    s += ' '
    s += self.pprint_block_noindent(tree.children[3])
    return s

  def pprint_block(self, tree):
    return self.indent() + self.pprint_block_noindent(tree)

  def pprint_block_noindent(self, tree):
    s = '{\n'
    self.level += 1
    s += self.pprint_commands(tree.children[1])
    self.level -= 1
    s += self.indent() + '}'
    return s

  def pprint_return(self, tree):
    s = self.indent() + 'return ('
    vals = tree.children[1].children
    s += self.join_fit_map(llen(s), ', ', vals, self.pprint_expression)
    s += ')'
    return s

  def pprint_expression(self, tree, start_col):
    exptype = tree.children[0]
    dispatch = {
     'or': self.pprint_binary_op,
     'and': self.pprint_binary_op,
     'not': self.pprint_unary_op,
     'relop': self.pprint_binary_op,
     'addsub': self.pprint_binary_op,
     'mul': self.pprint_binary_op,
     'divmod': self.pprint_binary_op,
     'pow': self.pprint_binary_op,
     'varName': self.pprint_varName,
     'funcCall': self.pprint_funcCall,
     'unaryMinus': self.pprint_unary_op,
     'literal': self.pprint_literal,
    }
    return dispatch[exptype](tree, start_col)

  # return precedence and associativity
  def prec_assoc(self, tree):
    d = {
     'or': (10, 'L'),
     'and': (20, 'L'),
     'not': (30, 'L'),
     'relop': (40, 'L'),
     'addsub': (50, 'L'),
     'mul': (60, 'L'),
     'divmod': (70, 'L'),
     'pow': (80, 'R'),
     'varName': (100, 'L'),
     'funcCall': (100, 'L'),
     'unaryMinus': (100, 'L'),
     'literal': (100, 'L'),
    }
    return d[tree.children[0]]

  def pprint_varName(self, tree, start_col):
    return tree.children[1].value

  def pprint_funcCall(self, tree, start_col):
    vals = tree.children[2].children
    s = tree.children[1].value + '('
    s += self.join_fit_map(start_col + llen(s), ', ', vals, self.pprint_expression)
    s += ')'
    return s

  def pprint_unary_op(self, tree, start_col):
    unary_ops = {
      'not': 'not ',
      'unaryMinus': '-',
    }
    pr, assoc = self.prec_assoc(tree)
    pr1, assoc1 = self.prec_assoc(tree.children[1])
    parens1 = pr > pr1
    s = unary_ops[tree.children[0]]
    if parens1: s += '('
    s += self.pprint_expression(tree.children[1], start_col + len(s))
    if parens1: s += ')'
    return s

  def pprint_binary_op(self, tree, start_col):
    pr, assoc = self.prec_assoc(tree)
    pr1, assoc1 = self.prec_assoc(tree.children[2])
    pr2, assoc2 = self.prec_assoc(tree.children[3])
    parens1 = (pr > pr1 or (pr == pr1 and assoc == 'R'))
    parens2 = (pr > pr2 or (pr == pr2 and assoc == 'L'))
    s = ''
    if parens1: s += '('
    s += self.pprint_expression(tree.children[2], start_col + len(s))
    if parens1: s += ')'
    s += ' ' + tree.children[1].value + ' '
    if parens2: s += '('
    s += self.pprint_expression(tree.children[3], start_col + llen(s))
    if parens2: s += ')'
    return s

  def pprint_literal(self, tree, start_col):
    return tree.children[1].value

  ### types

  def pprint_type(self, tree, start_col):
    s = '('
    sc1 = start_col + llen(s)
    params = tree.children[1].children
    s += self.join_fit_map(sc1, ', ', params, self.pprint_type_atom)
    s += ')'
    if tree.children[0] == 'funcType':
      s += ' -> '
      if len(s) != llen(s):
        s += '\n' + start_col * ' ' + '('
        sc2 = start_col + 1
      else:
        s += '('
        sc2 = start_col + llen(s)
      res = tree.children[2].children
      s += self.join_fit_map(sc2, ', ', res, self.pprint_type_atom)
      s += ')'
    return s

  def pprint_type_atom(self, tok, start_col):
    return tok.value 

def pretty_print(tree, print_imports=True):
  return GbsPrettyPrinter().pprint_program(tree, print_imports=print_imports)

