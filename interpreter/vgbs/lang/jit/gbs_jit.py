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

import sys

import common.utils
import lang.bnf_parser
import lang.gbs_runnable
import lang.gbs_vm_serializer
import lang.gbs_builtins
import lang.jit.x86_64

def instruction_set():
  try:
    import lang.jit.x86_64
    return lang.jit.x86_64
  except:
    return None

def counter():
  i = 0
  while True:
    i += 1
    yield i

class JitCompiler(object):

  def __init__(self):
    self._arch = instruction_set()
    self._mangler = lang.gbs_vm_serializer.Mangler()
    self._program = self._arch.Program()
  
  def compile(self, compiled_program): 
    "Takes a compiled program (gbs_vm.py) and translates it into native code."
    rtns = self._mangler.mangle_routines(compiled_program)
    rtns = common.utils.seq_sorted(rtns.items())

    self._bytecode_program = compiled_program
    self._vardict = {}
    self._nargs = {}
    self._nlocals = {}
    self._nretvals = {}
    for mangled_name, (prog, rtn) in rtns:
      self.preprocess_routine(prog, rtn)

    self.add_main()
    for mangled_name, (prog, rtn) in rtns:
      self.compile_routine(prog, rtn)

  def preprocess_routine(self, prog, rtn):
    mname = self._mangler.mangle(prog, rtn.name)
    self._vardict[mname] = vardict = self._var_dictionary_for(rtn)

    nargs = 0
    nlocals = 0
    for typ, nm in vardict.values():
      if typ == 'local':
        nlocals += 1
      elif typ == 'param':
        nargs += 1
      else:
        assert False 

    nretvals = 0
    for op in rtn.ops:
      if op[0] in ['return', 'returnVars']:
        nretvals = op[1]

    self._nargs[mname] = nargs
    self._nlocals[mname] = nlocals
    self._nretvals[mname] = nretvals

  def add_main(self):
    self._main_varnames = []
    main_nretvals = self._nretvals['$Main']
    self._program.add(self._arch.BeginMainRoutine())
    self._program.add(self._arch.InitializeBoard())
    self._program.add(self._arch.CallUserDefined('$Main', 0, main_nretvals))
    self._program.add(self._arch.FinalizeBoard())
    self._program.add(self._arch.ReturnFromMain(main_nretvals))
    self._program.add(self._arch.EndMainRoutine())

  def main_nretvals(self):
    return self._nretvals['$Main']

  def main_varnames(self):
    return self._main_varnames

  def compile_routine(self, prog, rtn):
    mname = self._mangler.mangle(prog, rtn.name)
    self._program.add(self._arch.Label(mname))

    vardict = self._vardict[mname]
    nargs = self._nargs[mname]
    nlocals = self._nlocals[mname]
    nretvals = self._nretvals[mname]

    #print('***', rtn.prfn, rtn.name, rtn.params)
    #print('    vardict', vardict)
    #print('    nargs', nargs)
    #print('    nlocals', nlocals)
    #print('    nretvals', nretvals)

    self._program.add(self._arch.BeginRoutine(nlocals))

    _op_i = 0
    while _op_i < len(rtn.ops):
      op = rtn.ops[_op_i]
      opcode = op[0]
      if opcode == 'pushConst':
        self._program.add(self._arch.PushConst(op[1]))
      elif opcode == 'pushFrom':
        self._program.add(self._arch.PushVar(*vardict[op[1]]))
      elif opcode == 'popTo':
        self._program.add(self._arch.Assign(*vardict[op[1]]))
      elif opcode == 'returnVars':
        self._main_varnames = op[2]
        self._program.add(self._arch.ReturnVars(op[1], op[2]))
      elif opcode == 'return':
        self._program.add(self._arch.Return(op[1]))
      elif opcode == 'label':
        self._program.add(self._arch.Label(':%s:' % (op[1],)))
      elif opcode == 'jump':
        self._program.add(self._arch.Jump(':%s:' % (op[1],)))
      elif opcode == 'jumpIfFalse':
        self._program.add(self._arch.JumpIfFalse(':%s:' % (op[1],)))
      elif opcode == 'call':
        if op[1] in self._bytecode_program.builtins:
          margs = self._bytecode_program.builtins[op[1]].num_params()
          routine = self._bytecode_program.builtins[op[1]]
          if routine.type() == 'procedure':
            mretvals = 0
          else:
            mretvals = self._bytecode_program.builtins[op[1]].num_retvals()
          self._program.add(self._arch.CallBuiltin(op[1], margs, mretvals))
        else:
          m = self._mangler.mangle(prog, op[1])
          margs = self._nargs[m]
          mretvals = self._nretvals[m]
          self._program.add(self._arch.CallUserDefined(m, margs, mretvals))
      elif opcode == 'THROW_ERROR':
        self._program.add(self._arch.THROW_ERROR(common.utils.show_string(op[1])))
      elif opcode in ['enter']:
        self._program.add(self._arch.EnterFunction())
      elif opcode in ['leave']:
        _op_i += 1
        assert _op_i < len(rtn.ops)
        op_ret = rtn.ops[_op_i]
        assert op_ret[0] == 'return'
        self._program.add(self._arch.LeaveFunctionAndReturn(op_ret[1]))
      elif opcode in ['delVar']:
        pass # ignore
      elif opcode in ['jumpIfNotIn']:
        self._program.add(self._arch.JumpIfNotIn(op[1], ':%s:' % (op[2],)))
      else:
        print(opcode)
        assert False
      _op_i += 1

    self._program.add(self._arch.EndRoutine(nlocals))

  def _var_dictionary_for(self, rtn):
    d = {}

    # parameter numbers are reversely assigned
    # (the last parameter is 1)
    # for ease of stack handling
    param_id = counter()
    for p in common.utils.seq_reversed(rtn.params):
      d[p] = ('param', param_id.next())

    local_id = counter()
    def addlocal(v):
      if v not in d:
        d[v] = ('local', local_id.next())

    for op in rtn.ops:
      if op[0] in ['pushFrom', 'popTo', 'delVar']:
        addlocal(op[1])
      elif op[0] in ['returnVars']:
        for v in op[2]:
          addlocal(v)

    return d

  def program(self):
    return self._program

  def native_code(self):
    return self._program.code()

  def native_function(self):
    self._program.expand_labels()
    return self._program.native_function()

import lang.board.formats
import ctypes
import common.i18n as i18n

class GbsJitRuntimeException(common.utils.SourceException):
  def error_type(self):
    return i18n.i18n('Runtime error')

class JitCompiledRunnable(lang.gbs_runnable.GbsRunnable):
  def __init__(self, compiled_code):
    self._jit = JitCompiler()
    self._jit.compile(compiled_code)
    self._f = self._jit.native_function()
    self._nretvals = self._jit.main_nretvals()
  def jit_code(self):
    return repr(self._jit.program())
  def native_code(self):
    return repr(self._jit.native_code())
  def run(self, board):
    gbbo_fmt = lang.board.formats.AvailableFormats['gbbo']()

    # generate buffer for the board, with the board data
    board_str = gbbo_fmt.to_string(board)
    buf = ctypes.create_string_buffer(board_str)
    arch = instruction_set()

    # generate result buffer for the return values
    resbuf_len = max(arch.Word_size * self._nretvals, arch.THROW_ERROR_Max_err_len)
    resbuf = ctypes.create_string_buffer(resbuf_len * '\xff')

    # run native function over the buffers
    res = self._f(buf, resbuf)
    if res == 0:
      # if result is ok, retrieve the resulting board and
      # build the list of return values
      gbbo_fmt.from_string(board, buf.raw)
      ws = arch.Word_size
      varnames = self._jit.main_varnames()
      retvals = []
      assert len(varnames) == self._nretvals
      for i in range(self._nretvals):
        vn = lang.gbs_builtins.polyname_name(varnames[i])
        vt = lang.gbs_builtins.polyname_types(varnames[i])[0]
        retvals.append((vn, arch.decode_literal(vt, resbuf[ws * i:ws * i + ws])))
      return retvals
    elif res == arch.THROW_ERROR_Errcode:
      msg = resbuf.raw.split('\0')[0]
      raise GbsJitRuntimeException(msg, lang.bnf_parser.fake_bof())
    else:
      assert False

def jit_compile(compiled_code):
  return JitCompiledRunnable(compiled_code)

class JitInterpreter(object):
  def __init__(self):
    self._compiled_program = None
    self._runnable = None
    self._board = None
  def init_program(self, compiled_program, board):
    if self._compiled_program != compiled_program:
      self._compiled_program = compiled_program
      self._runnable = JitCompiledRunnable(compiled_program)
    self._board = board
  def step(self):
    res = self._runnable.run(self._board)
    return 'END', res
  def current_area(self):
    return lang.bnf_parser.fake_bof()

