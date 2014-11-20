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
import common.i18n as i18n
from common.utils import *

import lang.gbs_def_helper as def_helper

#### Live variable analysis.

class GbsLivenessException(StaticException):
  def error_type(self):
    return i18n.i18n('Liveness analysis')

class GbsUninitializedVarException(GbsLivenessException): pass
class GbsUnusedVarException(GbsLivenessException): pass

class GbsLivenessAnalyzer(object):
  """Analyzes live variables in Gobstones programs for reporting
uses of variables that have no associated definition and, conversely,
definitions with no associated use."""
  def annotate_program(self, tree):
    #imports = tree.children[1].children
    defs = tree.children[2]
    self.annotate_defs(defs)

  def annotate_defs(self, tree):
    "Annotate each command with live_in and live_out sets."
    for def_ in tree.children:
      self.annotate_def(def_)

  def annotate_def(self, tree):
    block = def_helper.get_def_body(tree)
    block.live_out = tokset_new()
    # iterate until a fixed point is met
    self.change = True
    while self.change:
      self.change = False
      self.annotate_body(block)

  def _live_in(self, tree, s):
    """Extend the live_in set of the tree with s, recording if this
modifies the current state of the analysis."""
    if tree.live_in is None:
      tree.live_in = {}
    if tokset_extend_change(tree.live_in, s):
      self.change = True

  def _live_out(self, tree, s):
    """Extend the live_out set of the tree with s, recording if this
modifies the current state of the analysis."""
    if tree.live_out is None:
      tree.live_out = {}
    if tokset_extend_change(tree.live_out, s):
      self.change = True

  def _live_out_loop(self, tree, minus=None):
    if tree.live_in is not None:
      s = tree.live_in
      if minus is not None:
        s = tokset_difference(s, minus)
      self._live_out(tree, s)

  def annotate_body(self, tree):
    s = tree.live_out
    for cmd in seq_reversed(tree.children):
      self.annotate_cmd(cmd, s)
      s = cmd.live_in
    self._live_in(tree, s)

  def annotate_cmd(self, tree, next_block_in):
    command = tree.children[0]
    dispatch = {
      'Skip': self.annotate_Skip,
      'THROW_ERROR': self.annotate_THROW_ERROR,
      'procCall': self.annotate_procCall,
      'assignVarName': self.annotate_assignVarName,
      'assignVarTuple1': self.annotate_assignVarTuple1,
      'if': self.annotate_if,
      'case': self.annotate_case,
      'while': self.annotate_while,
      'repeat': self.annotate_repeat,
      'foreach': self.annotate_foreach,
      'block': self.annotate_block,
      'return': self.annotate_return,
    }
    assert command in dispatch
    self._live_out(tree, next_block_in)
    dispatch[command](tree)

  # idea for annotate_<command> methods:
  # PRE: tree.live_out is already the live_out set
  # POST: tree.live_in is the live_in set

  def annotate_Skip(self, tree):
    self._live_in(tree, tree.live_out)

  def annotate_THROW_ERROR(self, tree):
    self._live_in(tree, tree.live_out)

  def annotate_procCall(self, tree):
    # in = gen U out
    gen = self.gen_tuple(tree.children[2])
    self._live_in(tree, tokset_union(gen, tree.live_out))

  def annotate_assignVarName(self, tree):
    # in = gen U (out \ kill)
    kill = tokset_new([tree.children[1].value])
    gen = self.gen_expression(tree.children[2])
    self._live_in(tree, tokset_union(gen, tokset_difference(tree.live_out, kill)))

  def annotate_assignVarTuple1(self, tree):
    # in = gen U (out \ kill)
    kill = tokset_new([v.value for v in tree.children[1].children])
    gen = self.gen_expression(tree.children[2])
    self._live_in(tree, tokset_union(gen, tokset_difference(tree.live_out, kill)))

  def annotate_if(self, tree):
    cond_ = tree.children[1]
    then_ = tree.children[2]
    else_ = tree.children[3]
    # in(if cond_ then_ else_) = gen(cond_) U in(then_) U in(else_)
    res = tokset_new()
    tokset_extend(res, self.gen_expression(cond_))
    self.annotate_cmd(then_, tree.live_out)
    tokset_extend(res, then_.live_in)
    if else_ is not None:
      self.annotate_cmd(else_, tree.live_out)
      tokset_extend(res, else_.live_in)
    else:
      tokset_extend(res, tree.live_out)
    self._live_in(tree, res)

  def annotate_case(self, tree):
    # in(case val of branches) = gen(val) U in(branch1) U ... U in(branchN)
    val = tree.children[1]
    res = tokset_new()
    tokset_extend(res, self.gen_expression(val))
    for branch in tree.children[2].children:
      if branch.children[0] == 'branch':
        branch_body = branch.children[2]
      else: # defaultBranch
        branch_body = branch.children[1]
      self.annotate_cmd(branch_body, tree.live_out)
      tokset_extend(res, branch_body.live_in)
    self._live_in(tree, res)

  def annotate_while(self, tree):
    self._live_out_loop(tree) # add in to out
    # in(while cond body) = gen(cond) U in(body) U out(while ...)
    cond = tree.children[1]
    body = tree.children[2]
    res = tokset_new()
    tokset_extend(res, self.gen_expression(cond))
    self.annotate_cmd(body, tree.live_out)
    tokset_extend(res, body.live_in)
    tokset_extend(res, tree.live_out)
    self._live_in(tree, res)

  def annotate_repeat(self, tree):
    self._live_out_loop(tree)
    # in (repeat times body)
    #   = gen(times) U in(body) U out(repeat ...)
    res = tokset_new()
    times = tree.children[1]
    body = tree.children[2]
    tokset_extend(res, self.gen_expression(times))
    self.annotate_cmd(body, tree.live_out)
    tokset_extend(res, body.live_in)
    tokset_extend(res, tree.live_out)
    self._live_in(tree, res)

  def annotate_foreach(self, tree):
    var = tree.children[1].value
    kill = tokset_new([var])
    self._live_out_loop(tree, minus=kill) # add in to out
    # in(foreach i in from..to body)
    #   = gen(from) U gen(to) U (in(body) \ {i}) U out(foreach ...)
    from_ = tree.children[2].children[1]
    to_ = tree.children[2].children[2]
    body = tree.children[3]
    res = tokset_new()
    tokset_extend(res, self.gen_expression(from_))
    tokset_extend(res, self.gen_expression(to_))
    self.annotate_cmd(body, tree.live_out)
    tokset_extend(res, tokset_difference(body.live_in, kill))
    tokset_extend(res, tree.live_out)
    self._live_in(tree, res)

  def annotate_block(self, tree):
    block = tree.children[1]
    block.live_out = tree.live_out
    self.annotate_body(block)
    self._live_in(tree, block.live_in)

  def annotate_return(self, tree):
    assert tokset_empty(tree.live_out)
    self._live_in(tree, self.gen_tuple(tree.children[1]))

  def gen_expression(self, tree):
    "Returns the GEN set of an expression."
    if tree.live_gen is not None:
      return tree.live_gen
    exptype = tree.children[0]
    dispatch = {
      'or': self.gen_binary_op,
      'and': self.gen_binary_op,
      'not': self.gen_unary_op,
      'relop': self.gen_binary_op,
      'addsub': self.gen_binary_op,
      'mul': self.gen_binary_op,
      'divmod': self.gen_binary_op,
      'pow': self.gen_binary_op,
      'varName': self.gen_varName,
      'funcCall': self.gen_funcCall,
      'unaryMinus': self.gen_unary_op,
      'literal': self.gen_literal,
    }
    assert exptype in dispatch
    tree.live_gen = dispatch[exptype](tree)
    return tree.live_gen

  def gen_varName(self, tree):
    # this variable name
    tok = tree.children[1]
    return tokset_new_from_dict({tok.value: tok})

  def gen_funcCall(self, tree):
    # union of all arguments
    return self.gen_tuple(tree.children[2])

  def gen_literal(self, tree):
    # empty
    return tokset_new()

  def gen_unary_op(self, tree):
    return self.gen_expression(tree.children[1])

  def gen_binary_op(self, tree):
    s = tokset_new()
    tokset_extend(s, self.gen_expression(tree.children[2]))
    tokset_extend(s, self.gen_expression(tree.children[3]))
    return s

  def gen_tuple(self, tree):
    # union of all its subexpressions
    s = tokset_new()
    for subexpr in tree.children:
      tokset_extend(s, self.gen_expression(subexpr))
    return s

  def check_program(self, tree):
    #imports = tree.children[1].children
    defs = tree.children[2]
    self.check_defs(defs)

  def check_defs(self, tree):
    """Checks that each variable use is defined before and
that each defined variable (except parameters and foreach
indexes) is used later."""
    for def_ in tree.children:
      self.check_unitialized(def_)
      self.check_unused_def(def_)

  def check_unitialized(self, tree):
    params = [p.value for p in def_helper.get_def_params(tree)]
    block = def_helper.get_def_body(tree)
        
    possibly_undef = tokset_difference(block.live_in, tokset_new(params))
    if not tokset_empty(possibly_undef):
      for var, tok in possibly_undef.items():
        msg = i18n.i18n('Variable "%s" possibly uninitialized') % (var,)
        area = common.position.ProgramAreaNear(tok)
        raise GbsUninitializedVarException(msg, area)

  def check_unused_def(self, tree):
    self.check_unused_commands(def_helper.get_def_body(tree))

  def check_unused_commands(self, tree):
    for cmd in tree.children:
      self.check_unused_cmd(cmd)

  def check_unused_cmd(self, tree):
    command = tree.children[0]
    dispatch = {
      'assignVarName': self.check_unused_assignVarName,
      'assignVarTuple1': self.check_unused_assignVarTuple1,
      'if': self.check_unused_if,
      'case': self.check_unused_case,
      'while': self.check_unused_while,
      'foreach': self.check_unused_foreach,
      'block': self.check_unused_block,
    }
    if command in dispatch:
      dispatch[command](tree)

  def check_unused_assignVarName(self, tree, var=None):
    if var is None:
      var = tree.children[1]
    if var.value not in tree.live_out:
      msg = i18n.i18n('Variable "%s" defined but not used') % (var.value,)
      area = common.position.ProgramAreaNear(tree)
      raise GbsUnusedVarException(msg, area)

  def check_unused_assignVarTuple1(self, tree):
    varnames = [v.value for v in tree.children[1].children]
    any_used = False
    for v in varnames:
      if v in tree.live_out:
        any_used = True
        break
    if not any_used:
      if len(varnames) == 1:
        msg = i18n.i18n('Variable "%s" defined but not used') % (varnames[0],)
      else:
        msg = i18n.i18n('Variables "(%s)" defined but not used') % (
                  ', '.join(varnames),)
      area = common.position.ProgramAreaNear(tree)
      raise GbsUnusedVarException(msg, area)

  def check_unused_if(self, tree):
    self.check_unused_block(tree.children[2])
    if tree.children[3] is not None:
      self.check_unused_block(tree.children[3])

  def check_unused_case(self, tree):
    for branch in tree.children[2].children:
      if branch.children[0] == 'branch':
        self.check_unused_block(branch.children[2])
      else: # defaultBranch
        self.check_unused_block(branch.children[1])

  def check_unused_while(self, tree):
    self.check_unused_block(tree.children[2])

  def check_unused_foreach(self, tree):
    self.check_unused_block(tree.children[3])

  def check_unused_block(self, tree):
    self.check_unused_commands(tree.children[1])

def check_live_variables(tree):
  a = GbsLivenessAnalyzer()
  a.annotate_program(tree)
  a.check_program(tree)

