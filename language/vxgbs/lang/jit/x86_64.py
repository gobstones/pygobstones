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
import ctypes
import mmap

import lang.gbs_builtins
import lang.jit.x86_64_builtins
from lang.jit.x86_64_builtins import numtol
import common.utils
import common.i18n as i18n

class GbsJitPrimitiveException(Exception):
  pass

## Helper class to build a callable given native code

class NativeFunc(object):
  def __init__(self, native_code):
    buf = ctypes.create_string_buffer(native_code)
    size = ctypes.sizeof(buf)

    # keep it as an instance variable to avoid
    # garbage collection (and free)
    self._mmap_buf = mmap.mmap(
      -1,
      size,
      mmap.MAP_ANONYMOUS | mmap.MAP_PRIVATE,
      mmap.PROT_READ | mmap.PROT_WRITE | mmap.PROT_EXEC
    )

    addr = ctypes.addressof(ctypes.c_void_p.from_buffer(self._mmap_buf))
    addr = ctypes.c_void_p(addr)

    ctypes.memmove(addr, buf, size)

    mkfunc = ctypes.CFUNCTYPE(
      ctypes.c_longlong,             # result
      ctypes.POINTER(ctypes.c_char), # arg1 (board buffer)
      ctypes.POINTER(ctypes.c_char), # arg2 (result buffer)
    )
    self._addr = addr
    self._function = ctypes.cast(addr, mkfunc)

  def __call__(self, *args):
    return self._function(*args)

  def __del__(self):
    # free operations would go here
    pass

## VM opcodes for the x86_64 instruction set, including label
## pseudo-instructions

# Notes:
#
#   Assume that the program has been typechecked to preserve
#   semantics.
#
#   Integer overflows are not handled.
#
#   rsp            --> stack
#   [rbp - offset] --> local variables
#   [rbp + offset] --> parameters
#   rdi            --> for marking places in the stack
#                      used for returning parameters
#   rax, rdx       --> temp
#   rbx            --> board data pointer
#   r11            --> header position X
#   r12            --> header position Y
#   r13            --> board size Width
#   r14            --> board size Height
#   r15            --> pointer to result buffer
#   r9, r10        --> temp
#   rcx            --> unused
#   rsi            --> return point from Main routine
#
## Board representation
#
#   r11            --> header position X
#   r12            --> header position Y
#   r13            --> board size Width
#   r14            --> board size Height
#   rbx            --> board data pointer
#     each cell uses 16 bytes, 4 bytes per color:
#        [Azul][Negro][Rojo][Verde]
#     the board is an array of <width> * <height> cells
#     in row major order
#
#   Cell (i,j) can be found at:
#     rbx[16 * (board_height * head_y + head_x) + 4 * color_index]
#
## Undo operations:
#
#   each function pushes the whole board on an "enter" instruction,
#   and pops it on a "leave" instruction

Word_size = 8
Undefined_value = 0x7fffffffffffffff

class Instruction(object):
  def __init__(self):
    self._ip = None
  def maxlen(self):
    raise GbsJitPrimitiveException('subclass responsibility')
  def code(self):
    raise GbsJitPrimitiveException('subclass responsibility')
  def is_jump(self):
    return False
  def is_label(self):
    return False
  def len(self):
    return len(self.code())

class Nop(Instruction):
  def code(self):
    return '\x90'
  def __repr__(self):
    return 'Nop'

class Label(Instruction):
  def __init__(self, name):
    Instruction.__init__(self)
    self._name = name
  def code(self):
    return ''
  def is_label(self):
    return True
  def __repr__(self):
    return 'Label %s' % (self._name,)

class Jump(Instruction):
  def __init__(self, label_name):
    Instruction.__init__(self)
    self._label_name = label_name
    self._label_ip = None
  def is_jump(self):
    return True
  def len(self):
    return 5
  def code(self):
    next_ip = self._ip + self.len()
    res = '\xe9' + numtol(self._label_ip - next_ip) # jmp near <label>
    assert len(res) == self.len()
    return res
  def __repr__(self):
    return 'Jump %s' % (self._label_name,)

class JumpIfFalse(Instruction):
  def __init__(self, label_name):
    Instruction.__init__(self)
    self._label_name = label_name
    self._label_ip = None
  def is_jump(self):
    return True
  def len(self):
    return 10
  def code(self):
    next_ip = self._ip + self.len()
    res = ''
    res += '\x58'         # pop rax
    res += '\x48\x85\xc0' # test rax, rax
    res += '\x0f\x84' + numtol(self._label_ip - next_ip) # jz near <label>
    assert len(res) == self.len()
    return res
  def __repr__(self):
    return 'JumpIfFalse %s' % (self._label_name,)

class JumpIfNotIn(Instruction):
  def __init__(self, values, label_name):
    Instruction.__init__(self)
    self._values = values
    self._label_name = label_name
    self._label_ip = None
  def is_jump(self):
    return True
  def len(self):
    return 4 + len(self._values) * 23 + 9
  def code(self):
    next_ip = self._ip + self.len()
    res = []
    res.extend([
      '\x58',         # pop rax       ; reference value
      '\x4d\x31\xc9', # xor r9, r9    ; 0 iff should jump
    ])
    for val in self._values:
      res.extend([
        '\x48\xba' + x86_64_literal(val), # mov rdx, <value> ; compared value
        '\x48\x39\xd0',                   # cmp rax, rdx
        '\x0f\x94\xc2',                   # sete dl
        '\x48\x0f\xb6\xd2',               # movzx rdx, dl
        '\x49\x01\xd1',                   # add r9, rdx
      ])
    res.extend([
      '\x4d\x85\xc9',                                # test r9, r9
      '\x0f\x84' + numtol(self._label_ip - next_ip), # jz near <label>
    ])
    res = ''.join(res)
    assert len(res) == self.len()
    return res
  def __repr__(self):
    return 'JumpIfFalse %s %s' % (self._values, self._label_name,)

class PushVar(Instruction):
  # Reference to a local var. Indices are 1-based, can be negative (for parameters).
  def __init__(self, local_param, var_num):
    self._local_param = local_param
    self._var_num = var_num
  def code(self):
    if self._local_param == 'local':
      return self.code_local()
    else:
      return self.code_param()
  def code_local(self):
    offset = -self._var_num * Word_size
    boom_code = lang.jit.x86_64_builtins.boom_code_for(i18n.i18n('Uninitialized variable'))
    res = ''.join([
      '\x48\x8b\x85' + numtol(offset, nbytes=4),  # mov rax, [rbp + <offset>]
      '\x48\xba\xff\xff\xff\xff\xff\xff\xff\x7f', # mov rdx, <Undefined_value>
      '\x48\x39\xd0',                             # cmp rax, rdx
      '\x0f\x85' + numtol(len(boom_code), 4),     # jne .end
      boom_code,
      '\xff\xb5' + numtol(offset, nbytes=4),      # push qword [rbp + <offset>]
    ])
    return res
  def code_param(self):
    offset = (self._var_num + 1) * Word_size
    return '\xff\xb5' + numtol(offset, nbytes=4) # push qword [rbp + <offset>]
  def __repr__(self):
    return 'PushVar %s %s' % (self._local_param, self._var_num,)

def x86_64_literal(lit):
  def _repr(lit):
    if -0x8000000000000000 <= lit and lit < 0x7fffffffffffffff:
      return numtol(lit, nbytes=8)
    else:
      raise GbsJitPrimitiveException('integer literal too big')

  if lang.gbs_builtins.isinteger(lit):
    return _repr(lit)
  elif lang.gbs_builtins.isenum(lit):
    return _repr(lang.gbs_builtins.poly_ord(lit)[0])
  else:
    raise GbsJitPrimitiveException('not implemented')
  return res

def decode_literal(typ, lit):
  def unpack(s):
    r = 0
    for x in common.utils.seq_reversed(s):
      r = (r << 8) | ord(x)
    return r
  def signed(x):
    if x >= 0x7fffffffffffffff:
      return -(0xffffffffffffffff + 1 - x)
    else:
      return x
  value = signed(unpack(lit))
  if typ == 'Int':
    return value
  elif typ == 'Bool':
    return value == 1
  elif typ == 'Color':
    return lang.gbs_builtins.Color(value)
  elif typ == 'Dir':
    return lang.gbs_builtins.Direction(value)
  else:
    assert False

class PushConst(Instruction):
  def __init__(self, lit):
    self._lit = lit
  def code(self):
    if lang.gbs_builtins.isinteger(self._lit):
      res = self.code_int()
    elif lang.gbs_builtins.isenum(self._lit):
      res = self.code_enum()
    else:
      raise GbsJitPrimitiveException('not implemented')
    return res
  def code_int(self):
    return ''.join([
      '\x48\xb8' + x86_64_literal(self._lit), # mov rax, <const>
      '\x50',                                 # push rax
    ])
  def code_enum(self):
    # push <ord>
    res = '\x6a' + chr(lang.gbs_builtins.poly_ord(self._lit)[0])
    return res
  def __repr__(self):
    return 'PushConst %s' % (self._lit,)

class Assign(Instruction):
  # Assign a local var. Indices are 1-based, can be negative (for parameters).
  def __init__(self, local_param, var_num):
    self._local_param = local_param
    self._var_num = var_num
  def code(self):
    offset = self._var_num * Word_size
    if self._local_param == 'local':
      sig = -1
    else:
      sig = 1
    # pop qword [rbp +/- <offset>]
    res = '\x8f'
    if offset < 0x80:
      res += '\x45' + numtol(sig * offset, nbytes=1)
    else:
      res += '\x85' + numtol(sig * offset, nbytes=4)
    return res
  def __repr__(self):
    return 'Assign %s %s' % (self._local_param, self._var_num)

class CallBuiltin(Instruction):
  def __init__(self, funcname, nargs, nretvals):
    self._funcname = funcname
    self._nargs = nargs
    self._nretvals = nretvals
  def code(self):
    if self._funcname in lang.jit.x86_64_builtins.Inline:
      return lang.jit.x86_64_builtins.Inline[self._funcname]
    elif self._funcname in lang.gbs_builtins.BUILTINS_POLYMORPHIC:
      raise GbsJitPrimitiveException('builtin call of polymorphic "%s" not supported -- should typecheck the program' % (self._funcname,))
    else:
      raise GbsJitPrimitiveException('builtin call of %s not supported' % (self._funcname,))
  def __repr__(self):
    return 'CallBuiltin %s : %u -> %u' % (self._funcname, self._nargs, self._nretvals)

class CallUserDefined(Instruction):
  def __init__(self, label_name, nargs, nretvals):
    self._label_name = label_name
    self._nargs = nargs
    self._nretvals = nretvals
  def is_jump(self):
    return True
  def len(self):
    return 5 + 7 + 6 * self._nretvals
  def code(self):
    res = ''
    next_ip = self._ip + 5
    res += '\xe8' + numtol(self._label_ip - next_ip)         # call near <label>
    res += '\x48\x81\xc4' + numtol(Word_size * self._nargs)  # add rsp, Word_size*<nargs> ; pop pushed parameters
    for i in range(self._nretvals):
      # take the return values and push them in the stack
      offset = -Word_size * (i + 1)
      res += '\xff\xb7' + numtol(offset) # push qword [rdi - Word_size * i]
    assert len(res) == self.len()
    return res
  def __repr__(self):
    return 'CallUserDefined %s : %u -> %u' % (self._label_name, self._nargs, self._nretvals)

class Data(Instruction):
  def __init__(self, data):
    Instruction.__init__(self)
    self._data = data
  def code(self):
    return self._data
  def __repr__(self):
    return 'CallData %s' % (''.join(['%.2x' % (x,) for x in self._data]))

class BeginRoutine(Instruction):
  def __init__(self, num_locals):
    Instruction.__init__(self)
    self._num_locals = num_locals
  def code(self):
    res = ''
    res += '\x55'         # push rbp
    res += '\x48\x89\xe5' # mov rbp, rsp
    for i in range(self._num_locals):
      res += '\x48\xb8' + numtol(Undefined_value, nbytes=8) # mov rax, <Undefined_value>
      res += '\x50'                                         # push rax
    return res
  def __repr__(self):
    return 'BeginRoutine %u' % (self._num_locals,)

class EndRoutine(Instruction):
  def __init__(self, num_locals):
    Instruction.__init__(self)
    self._num_locals = num_locals
  def code(self):
    res = ''
    if self._num_locals != 0:
      res += '\x48\x81\xc4' + numtol(Word_size * self._num_locals) # add rsp, Word_size * <num_locals> ; pop locals
    res += '\x5d' # pop rbp
    res += '\xc3' # ret
    return res
  def __repr__(self):
    return 'EndRoutine %u' % (self._num_locals,)

class EnterFunction(Instruction):
  def code(self):
    return lang.jit.x86_64_builtins.Undo_builtins['enter']
  def __repr__(self):
    return 'EnterFunction'

class Return(Instruction):
  def __init__(self, nretvals):
    self._nretvals = nretvals
  def code(self):
    # to return, leave the values in the stack, but return the
    # stack top as if popping them and save in "rdi" the place
    # where they start
    res = ''.join([
      '\x48\x81\xc4' + numtol(Word_size * self._nretvals), # add rsp, Word_size * num_retvals
      '\x48\x89\xe7', # mov rdi, rsp
    ])
    return res
  def __repr__(self):
    return 'Return %u' % (self._nretvals,)

class LeaveFunctionAndReturn(Instruction):
  def __init__(self, nretvals):
    Instruction.__init__(self)
    self._nretvals = nretvals
  def code(self):
    # to return, leave the values in the stack, but return the
    # stack top as if popping them and save in "rdi" the place
    # where they start
    res = ''.join([
      '\x48\x81\xc4' + numtol(Word_size * self._nretvals), # add rsp, Word_size * num_retvals
      '\x48\x89\xe7', # mov rdi, rsp
      lang.jit.x86_64_builtins.Undo_builtins['leave'],
    ])
    return res
  def __repr__(self):
    return 'LeaveFunctionAndReturn %u' % (self._nretvals,)

class ReturnVars(Instruction):
  def __init__(self, nretvals, varnames):
    self._nretvals = nretvals
    self._varnames = varnames
  def code(self):
    # to return, leave the values in the stack, but return the
    # stack top as if popping them and save in "rdi" the place
    # where they start
    res = ''
    res += '\x48\x81\xc4' + numtol(Word_size * self._nretvals) # add rsp, Word_size * num_retvals
    res += '\x48\x89\xe7' # mov rdi, rsp
    return res
  def __repr__(self):
    return 'ReturnVars %u %s' % (self._nretvals, self._varnames)

## Instructions for the entry point

class BeginMainRoutine(Instruction):
  def code(self):
    res = ''.join([
    
#      '\x53',     # push rbx
#      '\x56',     # push rsi
#      '\x57',     # push rdi
#      '\x41\x54', # push r12
#      '\x41\x55', # push r13
#      '\x41\x56', # push r14
#      '\x41\x57', # push r15

      '\x55',         # push rbp
      '\x48\x89\xe5', # mov rbp, rsp
      '\x49\x89\xf7', # mov r15, rsi ; save result buffer pointer in r15
      '\x48\x89\xe6', # mov rsi, rsp ; save Main stack pointer in rsi
    ])
    return res
  def __repr__(self):
    return 'BeginMainRoutine'

class EndMainRoutine(Instruction):
  def code(self):
    res = ''.join([
      '\x5d', # pop rbp

#      '\x41\x5f', # pop r15
#      '\x41\x5e', # pop r14
#      '\x41\x5d', # pop r13
#      '\x41\x5c', # pop r12
#      '\x5f', # pop rdi
#      '\x5e', # pop rsi
#      '\x5e', # pop rbx

      '\xc3', # ret
    ])
    return res
  def __repr__(self):
    return 'EndMainRoutine'

THROW_ERROR_Errcode = 0x7fffffffffffffff
THROW_ERROR_Max_err_len = lang.jit.x86_64_builtins.Max_err_len
class THROW_ERROR(Instruction):
  def __init__(self, msg):
    self._msg = msg
  def code(self):
    return lang.jit.x86_64_builtins.boom_code_for(self._msg)
  def __repr__(self):
    return 'THROW_ERROR'

class InitializeBoard(Instruction):
  def code(self):
    res = ''.join([
        # zero registers out
        '\x4d\x31\xdb', # xor r11, r11
        '\x4d\x31\xe4', # xor r12, r12
        '\x4d\x31\xed', # xor r13, r13
        '\x4d\x31\xf6', # xor r14, r14
        # read data from array
        '\x44\x8b\x2f',     # mov r13d, [rdi]     ; width
        '\x44\x8b\x77\x04', # mov r14d, [rdi + 4] ; height
        '\x44\x8b\x5f\x08', # mov r11d, [rdi + 8]  ; X
        '\x44\x8b\x67\x0c', # mov r12d, [rdi + 12] ; Y
        # save board pointer in rbx
        '\x48\x8d\x5f\x10', # lea rbx, [rdi + 16]
    ])
    return res
  def __repr__(self):
    return 'InitializeBoard'

class FinalizeBoard(Instruction):
  def code(self):
    res = ''.join([
        '\x48\x8d\x5b\xf0', # lea rbx, [rbx - 16]
        # write width, height, and header position back
        '\x44\x89\x2b',     # mov [rbx], r13d      ; width
        '\x44\x89\x73\x04', # mov [rbx + 4], r14d  ; height
        '\x44\x89\x5b\x08', # mov [rbx + 8], r11d  ; X
        '\x44\x89\x63\x0c', # mov [rbx + 12], r12d ; Y
    ])
    return res
  def __repr__(self):
    return 'FinalizeBoard'

class ReturnFromMain(Instruction):
  def __init__(self, nretvals):
    self._nretvals = nretvals
  def code(self):
    res = []
    res.extend([
      '\x48\xb8' + numtol(self._nretvals, 8) # mov rax, <nretvals>
    ])
    for i in range(self._nretvals):
      res.extend([
        '\x48\xff\xc8',     # dec rax
        '\x41\x8f\x04\xc7', # pop qword [r15 + 8 * rax]
      ])
    return ''.join(res)
  def __repr__(self):
    return 'ReturnFromMain %u' % (self._nretvals,)

## Class to represent a program (basically a list of instructions)

class Program(object):

  def __init__(self):
    self._prog = []

  def expand_labels(self):
    labels = {}
    ip = 0
    for instr in self._prog:
      instr._ip = ip
      if instr.is_label():
        labels[instr._name] = ip
      ip += instr.len()
    for instr in self._prog:
      if instr.is_jump():
        if instr._label_name not in labels:
          raise GbsJitPrimitiveException('jump to undefined label: "%s"' % (instr._label_name,))
        instr._label_ip = labels[instr._label_name]

  def code(self):
    return ''.join([instr.code() for instr in self._prog])

  def add(self, instruction):
    self._prog.append(instruction)

  def __repr__(self):
    res = []
    for instr in self._prog:
      s = repr(instr)
      if isinstance(instr, Label):
        s = '\n' + s
      else:
        s = '  ' + s
      res.append(s) 
    return '\n'.join(res)

  def native_function(self):
    return NativeFunc(self.code())

