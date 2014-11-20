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

import lang.gbs_builtins
import lang.gbs_constructs
import lang.gbs_runnable
import lang.gbs_io
import common.position
import common.i18n as i18n
import random
from common.utils import *

#### Gobstones virtual machine

## A compiled program consists of a dictionary of
## routine definitions.
##
## Each "routine" is basically a list of opcodes
## for a simple stack-based machine.
##
## Opcodes:
## ---
## pushConst   const_name                  |           -- const
## pushFrom     var_name                    |           -- var
## popTo      var_name                    | value     --
## call        rtn_name, nargs             | a1 ... an -- r1 ... rm
## THROW_ERROR        str                         |           --
## label       label                       |           --
## jump        label                       |           --
## jumpIfFalse label                       |      cond --
## jumpIfNotIn lits, label                 |     value --
## return      nvals                       | a1 ... an -- a1 ... an
## enter                                   | push global state when entering function
## leave                                   | pop global state when leaving function
## delVar      var_name                    | remove variable from local environment
## ---
##
## Arguments are always processed from left to right.
##

class GbsVmException(DynamicException):
  def error_type(self):
    return i18n.i18n('Runtime error')

class GbsCompiledProgram(object):
  def __init__(self, tree, module_prefix=''):
    self.tree = tree
    self.module_prefix = module_prefix
    self.builtins = {}
    for b in lang.gbs_builtins.BUILTINS:
      bname, b = b.name(), b.underlying_construct()
      self.builtins[bname] = b
    self.routines = {}
    self.external_routines = {}
    
  def __repr__(self):
    sr = seq_sorted(self.routines.values(), key=lambda r: r.name)
    return '\n\n'.join([repr(x) for x in sr])

class GbsCompiledCode(object):
  def __init__(self, tree, prfn, name, params):
    self.tree = tree
    self.prfn = prfn
    self.name = name
    self.params = params
    self.ops = []
    self.label_table = {}
    self.nearby_elems = {}
    
  def push(self, op, near=None):
    if near:
      self.nearby_elems[len(self.ops)] = near
    self.ops.append(op)
    
  def build_label_table(self):
    i = 0
    for op in self.ops:
      if op[0] == 'label':
        self.label_table[id(op[1])] = i + 1
      i += 1
      
  def add_enter(self):
    if self.prfn == 'function':
      self.push(('enter',))
      
  def add_leave_return(self):
    if self.name == 'Main' or (self.prfn == 'entrypoint' and self.name == 'program'):
      self.add_leave_return_to_Main()
    elif len(self.ops) == 0 or self.ops[-1][0] != 'return':
      assert self.prfn == 'procedure'
      self.push(('return', 0))
    elif len(self.ops) > 0 and self.ops[-1][0] == 'return' and self.prfn == 'function':
      self.ops.insert(-1, ('leave',))
      
  def add_leave_return_to_Main(self):
    if len(self.ops) == 0 or self.ops[-1][0] != 'returnVars':
      self.push(('returnVars', 0, []))
      
  def construct(self):
    if self.prfn == 'function':
      return lang.gbs_constructs.UserCompiledFunction(self.name, self.params)
    else:
      return lang.gbs_constructs.UserCompiledProcedure(self.name, self.params)
  def __repr__(self):
    def showop(op):
      if op[0] == 'jumpIfNotIn':
        opname, lits, label = op
        return '    %s %s %s' % (
          opname, label, ' '.join([str(x) for x in lits]))
      elif op[0] == 'returnVars':
        opname, nvrs, vrs = op
        return '    %s %s %s' % (
          opname, nvrs, ' '.join([str(x) for x in vrs]))
      else:
        return '    ' + ' '.join([str(x) for x in op])
    p = ' '.join(self.params)
    hd = '%s %s %s\n' % (self.prfn, self.name, p)
    ##hd += str(self.label_table) + '\n'
    return hd + '\n'.join([showop(x) for x in self.ops]) + '\nend'


class ActivationRecord(object):

  def __init__(self, program, routine):
    self.program = program
    self.routine = routine
    self.ip = 0
    self.bindings = {}
    self.immutable_names = []

  def is_immutable(self, name):
    return name in self.immutable_names
    
  def set_immutable(self, name):        
    self.immutable_names.append(name)
        
  def unset_immutable(self, name):
    self.immutable_names.remove(name)

  def free_bindings(self):
    self.bindings = {}
    self.immutable_names = []


class GlobalState(object):
  def __init__(self, interpreter, board):
    self.interpreter = interpreter
    self.board = board
  def push(self):
    self.board.push_state()
  def pop(self):
    self.board.pop_state()
  def backtrace(self, msg):
    return self.interpreter.backtrace(msg)
  def area(self):
    return self.interpreter.current_area()

class GbsVmInterpreter(object):
  def __init__(self, toplevel_filename=None):
    self.toplevel_filename = toplevel_filename

  def area_near(self, ar):
    elem = ar.routine.nearby_elems.get(ar.ip, self.program.tree)
    return common.position.ProgramAreaNear(elem)

  def current_area(self):
    cs = self.callstack + [self.ar]
    for ar in common.utils.seq_reversed(cs):
      if ar.program.tree.source_filename == self.toplevel_filename:
        return self.area_near(ar)
    # if everything else fails
    return self.area_near(self.ar)

  def init_program(self, program, board, interactive_api=None):
    if interactive_api:
        self.interactive_api = interactive_api
    else:
        self.interactive_api = NullInteractiveAPI()
      
    if self.toplevel_filename is None:
      self.toplevel_filename = program.tree.source_filename
    self.program = program

    if 'program' not in program.routines:
      if 'Main' not in program.routines:
          raise GbsVmException(i18n.i18n('Program has no entrypoint'),
                               common.position.ProgramAreaNear(program.tree))
      else:
        self.ar = ActivationRecord(program, program.routines['Main'])
    else:
      self.ar = ActivationRecord(program, program.routines['program'])
      

    self.callstack = []
    self.stack = []          
    self.global_state = GlobalState(self, board)

  def _read_arguments(self, params):
    args = []
    for i in range(len(params)):
      args.insert(0, self.stack.pop())
    for p, a in zip(params, args):
      self.ar.bindings[p] = a

  def show_state(self):
    return '\n'.join([
      '  IP: %s(%i)' % (self.ar.routine.name, self.ar.ip),
      '  STACK: %s' % (self.stack,),
      '  LOCALS: %s' % (self.ar.bindings,),
    ])

  def backtrace(self, msg):
    def describe(ar, indent):
      loc = ar.routine.nearby_elems.get(ar.ip, self.program.tree).pos_begin.file_row()
      return '%s%s %s %s' % ('  ' * indent, ar.routine.prfn, ar.routine.name, loc)
    cs = self.callstack + [self.ar]
    res = ''
    res += msg + '\n\n'
    res += i18n.i18n('At:') + '\n'
    res += indent('\n'.join([
                         describe(x, y)
                         for x, y in zip(cs, range(0, len(cs)))
                       ])) + '\n'
    bindings = [(k, v) for k, v in seq_sorted(self.ar.bindings.items())
                       if k[0] != '_']
    if len(bindings) > 0:
      res += i18n.i18n('Locals:') + '\n'
      res += indent('\n'.join(['%s: %s' % (k, v) for k, v in bindings]))
    return res

  def arity_check(self, construct, nargs):
    nparams = construct.num_params()
    if nparams == nargs: return
    if nparams < nargs:
      many_few = 'many'
    else:
      many_few = 'few'
    msg = 'Too %s arguments for %s "%%s".\nExpected %%i (%%s), received %%i' % (
               many_few, construct.type())
    raise GbsVmException(i18n.i18n(msg) % (construct.name(),
                                           nparams,
                                           ', '.join(construct.params()),
                                           nargs),
                         self.current_area())

  def step(self):
    assert self.ar.ip < len(self.ar.routine.ops)
    op = self.ar.routine.ops[self.ar.ip]
    opcode = op[0]

    if opcode == 'pushConst':
      self.stack.append(op[1])
      self.ar.ip += 1

    elif opcode == 'pushFrom':
      if op[1] not in self.ar.bindings:
       raise GbsVmException(i18n.i18n('Uninitialized variable: "%s"') % (op[1],),
                            self.current_area())
      self.stack.append(self.ar.bindings[op[1]])
      self.ar.ip += 1

    elif opcode == 'delVar':
      assert op[1] in self.ar.bindings
      del self.ar.bindings[op[1]]
      self.ar.ip += 1

    elif opcode == 'popTo':
      assert len(self.stack) > 0
      val = self.stack.pop()
      self.ar.bindings[op[1]] = val
      self.ar.ip += 1

    elif opcode == 'call':
      funcName = op[1]
      nargs = op[2]
      assert len(self.stack) >= nargs
      if funcName in self.program.builtins:
        builtin = self.program.builtins[funcName]
        self.arity_check(builtin, nargs)
        args = []
        for i in range(nargs):
          args.insert(0, self.stack.pop())
        res = builtin.primitive()(self.global_state, *args)
        if builtin.type() == 'function':
          self.stack.append(res) # push result
        self.ar.ip += 1
      elif funcName in self.program.routines:
        self.callstack.append(self.ar)
        rtn = self.program.routines[funcName]
        self.arity_check(rtn.construct(), nargs)
        self.ar = ActivationRecord(self.program, rtn)
        self._read_arguments(self.ar.routine.params)
      elif funcName in self.program.external_routines:
        self.callstack.append(self.ar)
        module, rtn = self.program.external_routines[funcName]
        self.arity_check(rtn.construct(), nargs)
        self.ar = ActivationRecord(module, rtn)
        self._read_arguments(self.ar.routine.params)
        self.program = module
      else:
        raise GbsVmException(i18n.i18n('function "%s" is not defined') % (
                    funcName,), self.current_area())

    elif opcode == 'THROW_ERROR':
      msg = i18n.i18n('Self destruction:') 
      msg = '\n'.join([msg, show_string(op[1])])
      msg = self.backtrace(msg)
      area = self.current_area()
      raise GbsVmException(msg, area)

    elif opcode == 'label':
      self.ar.ip += 1

    elif opcode == 'jump':
      dest = id(op[1])
      assert dest in self.ar.routine.label_table
      self.ar.ip = self.ar.routine.label_table[dest]

    elif opcode == 'jumpIfFalse':
      dest = id(op[1])
      assert dest in self.ar.routine.label_table
      assert len(self.stack) > 0
      val = self.stack.pop()

      if lang.gbs_builtins.poly_typeof(val) != 'Bool':
        raise GbsVmException(i18n.i18n('Condition should be a boolean'),
                             self.current_area())
      if not val:
        self.ar.ip = self.ar.routine.label_table[dest]
      else:
        self.ar.ip += 1

    elif opcode == 'jumpIfNotIn':
      dest = id(op[2])
      assert dest in self.ar.routine.label_table
      assert len(self.stack) > 0
      val = self.stack.pop()
      if val not in op[1]:
        self.ar.ip = self.ar.routine.label_table[dest]
      else:
        self.ar.ip += 1

    elif opcode == 'enter':
      self.global_state.push()
      self.ar.ip += 1

    elif opcode == 'leave':
      self.global_state.pop()
      self.ar.ip += 1

    elif opcode == 'return':
      assert len(self.callstack) > 0
      nvals = op[1]
      assert len(self.stack) >= nvals
      self.ar = self.callstack.pop()
      self.ar.ip += 1
      self.program = self.ar.program

    elif opcode == 'setImmutable':
      assert op[1] in self.ar.bindings
      self.ar.set_immutable(op[1])
      self.ar.ip += 1     
      
    elif opcode == 'unsetImmutable':
      assert op[1] in self.ar.bindings and self.ar.is_immutable(op[1])
      self.ar.unset_immutable(op[1])
      self.ar.ip += 1      

    elif opcode == 'returnVars':
      nvals = op[1]
      if len(self.callstack) == 0:
        assert self.ar.routine.name == 'Main' or self.ar.routine.name == 'program'
        return_vars = [lang.gbs_builtins.polyname_name(x) for x in op[2]]
        assert len(return_vars) == nvals
        #else:
        #  return_vars = [x.children[1].value
        #                    for x in self.ar.routine.tree.children[3].children[-1].children[1].children]
        return_vals = self.stack[-len(return_vars):]
        return 'END', list(zip(return_vars, return_vals))
      else:
        # pop the return results in case of having a recursive Main
        # (Main is a procedure, so the values it returns are not used)
        for i in range(nvals):
          self.stack.pop()
        self.ar = self.callstack.pop()
        self.ar.ip += 1
        self.program = self.ar.program

    else:
        raise GbsVmException(i18n.i18n('Unknown bytecode instruction: %s.') % (
                    opcode,), self.current_area())

    ## DEBUG
    #print(op)
    #print(self.show_state())
    return 'CONTINUE', None

def interp(compiled_program, board, interactive_api=None):
    vm = GbsVmInterpreter()
  
    vm.init_program(compiled_program, board, lang.gbs_io.CrossPlatformApiAdapter(interactive_api))
    
    while True:
        r = vm.step()
        if r[0] == 'END':
            return r[1]

class VmCompiledRunnable(lang.gbs_runnable.GbsRunnable):
    def __init__(self, compiled_program):
        self._prog = compiled_program
    def run(self, board, interactive_api = None):
        return interp(self._prog, board, interactive_api)

class NullInteractiveAPI(lang.gbs_io.InteractiveApi):
    def __init__(self):
        self.key_sequence = self.build_key_sequence()    
    def read(self):
        return self.key_sequence.pop();
    def build_key_sequence(self):
        keys = [4]
        selectableKeys = [x for x in range(65,90)]
        selectableKeys.extend([x for x in range(48,57)])
        selectableKeys.extend([x for x in range(97,122)])
        selectableKeys.extend([lang.gbs_io.GobstonesKeys.ARROW_LEFT,
                               lang.gbs_io.GobstonesKeys.ARROW_UP,
                               lang.gbs_io.GobstonesKeys.ARROW_RIGHT,
                               lang.gbs_io.GobstonesKeys.ARROW_DOWN,])
        for i in range(1,random.randrange(5, 20, 1)):
            keys.append(random.choice(selectableKeys))
        return keys