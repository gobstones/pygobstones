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

import common.i18n as i18n
import lang.gbs_builtins

def maxint(nbytes):
  res = 0
  for i in range(nbytes):
    res = (res << 8) | 0xff
  return res

def numtol(n, nbytes=4):
  if n < 0:
    n = maxint(nbytes) + n + 1
  s = ''
  for i in range(nbytes):
    s += chr(n & 0xff)
    n >>= 8
  return s

## Error messages

Max_err_len = 512
def boom_code_for(msg):
  msg = msg[:Max_err_len - 1] + '\0'
  res = []

  # go back to the point in the stack where the Main routine started
  # (longjmp to rsi)
  res.extend([
    '\x48\x89\xf4', # mov rsp, rsi
    '\x5d',         # pop rbp
  ])

  # copy message to result buffer in [r15]
  res.extend([
    '\x48\x31\xc0', # xor rax, rax
  ])
  for x in msg:
    res.extend([
      '\x41\xc6\x04\x07' + x, # mov byte [r15 + rax], <msg[i]>
      '\x48\xff\xc0'          # inc rax
    ])

  # return error code (0x7fffffffffffffff)
  res.extend([
    '\x48\xb8\xff\xff\xff\xff\xff\xff\xff\x7f', # mov rax, 0x7fffffffffffffff
    '\xc3',         # ret
  ])
  return ''.join(res)

def relop(setx_al):
  return ''.join([
      '\x58',             # pop rax
      '\x5a',             # pop rdx
      '\x48\x39\xc2',     # cmp rdx, rax
      setx_al,            # setXXX al
      '\x48\x0f\xb6\xc0', # movzx rax, al
      '\x50',             # push rax
  ])

def _primitive_PutStone():
  return ''.join([
      '\x41\x59',             # pop r9 ; pop a color
      '\x4c\x89\xe0',         # mov rax, r12  ; rax = y
      '\x49\xf7\xed',         # imul r13 ; rax = width * y
      '\x4c\x01\xd8',         # add rax, r11  ; rax = width * y + x
      '\x48\xc1\xe0\x04',     # shl rax, 4    ; rax = 16 * width * y + 16 * x
      '\x48\x01\xd8',         # add rax, rbx  ; rax = rbx[16 * width * y + 16 * x]
      '\x42\xff\x04\x88',     # inc dword [rax + 4 * r9]
  ])

def _primitive_TakeStone():
  boom_code = boom_code_for(i18n.i18n('Cannot take stones'))
  return ''.join([
      '\x41\x59',         # pop r9        ; pop a color
      '\x4c\x89\xe0',     # mov rax, r12  ; rax = y
      '\x49\xf7\xed',     # imul r13 ; rax = width * y
      '\x4c\x01\xd8',     # add rax, r11  ; rax = width * y + x
      '\x48\xc1\xe0\x04', # shl rax, 4    ; rax = 16 * width * y + 16 * x
      '\x48\x01\xd8',     # add rax, rbx  ; rax = rbx[16 * width * y + 16 * x]
      '\x4a\x8b\x14\x88', # mov rdx, [rax + 4 * r9]
      '\x48\x85\xd2',     # test rdx, rdx
      # jnz .end
      '\x0f\x85' + numtol(len(boom_code), 4),
      boom_code,
      # .end:
      '\x42\xff\x0c\x88', # dec dword [rax + 4 * r9]
  ])

def _switch(indices, code):
  res = ''
  destination = {}
  for x in indices:
    destination[x] = len(res)
    res += code[x]
  destination['Z'] = len(res)
  for x in indices + 'Z':
    key = '__' + x + '_'
    while True:
      pos = res.find(key)
      if pos == -1: break
      res = res[:pos] + numtol(destination[x] - pos - 4, 4) + res[pos + 4:]
  return res

def P(name, *types):
  return lang.gbs_builtins.polyname(name, types)

def _primitive_Move():
  code = {}
  code['A'] = ''.join([
     '\x41\x59',          # pop r9 ; pop a direction
     '\x49\x83\xf9\x00',  # cmp r9, 1
     '\x0f\x84' + '__N_', # je <code_e>
     '\x49\x83\xf9\x01',  # cmp r9, 1
     '\x0f\x84' + '__E_', # je <code_e>
     '\x49\x83\xf9\x02',  # cmp r9, 2
     '\x0f\x84' + '__S_', # je <code_s>
     '\x49\x83\xf9\x03',  # cmp r9, 3
     '\x0f\x84' + '__W_', # je <code_w>
     '\xe9' + '__X_',     # jmp <error>
  ])
  code['N'] = ''.join([
     '\x49\xff\xc4',      # inc r12
     '\x4d\x39\xf4',      # cmp r12, r14
     '\x0f\x8d' + '__X_', # jge <error>
     '\xe9' + '__Z_',     # jmp <end>
  ])
  code['E'] = ''.join([
     '\x49\xff\xc3',      # inc r11
     '\x4d\x39\xeb',      # cmp r11, r13
     '\x0f\x8d' + '__X_', # jge <error>
     '\xe9' + '__Z_',     # jmp <end>
  ])
  code['S'] = ''.join([
     '\x49\xff\xcc',      # dec r12
     '\x0f\x8c' + '__X_', # jl <error>
     '\xe9' + '__Z_',     # jmp <end>
  ])
  code['W'] = ''.join([
     '\x49\xff\xcb',      # dec r11
     '\x0f\x8c' + '__X_', # jl <error>
     '\xe9' + '__Z_',     # jmp <end>
  ])
  code['X'] = boom_code_for(i18n.i18n('Cannot move'))
  return _switch('ANESWX', code)

def _primitive_canMove():
  code = {}
  code['A'] = ''.join([
     '\x41\x59',          # pop r9 ; pop a direction
     '\x49\x83\xf9\x00',  # cmp r9, 1
     '\x0f\x84' + '__N_', # je <code_e>
     '\x49\x83\xf9\x01',  # cmp r9, 1
     '\x0f\x84' + '__E_', # je <code_e>
     '\x49\x83\xf9\x02',  # cmp r9, 2
     '\x0f\x84' + '__S_', # je <code_s>
     '\x49\x83\xf9\x03',  # cmp r9, 3
     '\x0f\x84' + '__W_', # je <code_w>
     '\xe9' + '__X_',     # jmp <error>
  ])
  code['N'] = ''.join([
     '\x4c\x89\xe2',      # mov rdx, r12
     '\x48\xff\xc2',      # inc rdx
     '\x4c\x39\xf2',      # cmp rdx, r14
     '\x0f\x9c\xc0',      # setl al
     '\xe9' + '__R_',     # jmp <continue>
  ])
  code['E'] = ''.join([
     '\x4c\x89\xda',      # mov rdx, r11
     '\x48\xff\xc2',      # inc rdx
     '\x4c\x39\xea',      # cmp rdx, r13
     '\x0f\x9c\xc0',      # setl al
     '\xe9' + '__R_',     # jmp <continue>
  ])
  code['S'] = ''.join([
     '\x4d\x85\xe4',      # test r12, r12
     '\x0f\x95\xc0',      # setnz al
     '\xe9' + '__R_',     # jmp <continue>
  ])
  code['W'] = ''.join([
     '\x4d\x85\xdb',      # test r11, r11
     '\x0f\x95\xc0',      # setnz al
     '\xe9' + '__R_',     # jmp <continue>
  ])
  code['X'] = boom_code_for(i18n.i18n('Invalid direction'))
  code['R'] = ''.join([
    '\x48\x0f\xb6\xc0',   # movzx rax, al
    '\x50',               # push rax
  ])
  return _switch('ANESWXR', code)

def _primitive_ClearBoard():
  code = {}
  code['A'] = ''.join([
    '\x4c\x89\xe8',     # mov rax, r13   ; rax = width
    '\x49\xf7\xee',     # imul r14  ; rax = width * height
    '\x48\xc1\xe0\x04', # shl rax, 4     ; rax = 16 * rax (times the cell size in bytes)
    '\x48\x31\xd2',     # xor rdx, rdx
  ])
  code['B'] = ''.join([
    '\x48\xff\xc8',       # sub rax, 8 ; qword size
    '\x0f\x8c' + '__Z_',  # jl <end>
    '\x88\x14\x03',       # mov qword [rbx + rax], rdx ; zero it out
    '\xe9' + '__B_',      # jmp <B>
  ])
  return _switch('AB', code)

def _primitive_divmod(div_mod):
  code = {}
  if div_mod == 'div':
    push_result = ''.join([
      '\x50', # push rax
    ])
  else:
    push_result = ''.join([
      '\x4c\x29\xca', # sub rdx, r9
      '\x52',         # push rdx
    ])
  code['A'] = ''.join([
    '\x41\x5a',          # pop r10 ; divisor
    '\x58',              # pop rax ; dividend
    '\x4d\x85\xd2',      # test r10, r10 ; check for zero divisor
    '\x0f\x84' + '__X_', # jz <error>
    '\x49\x89\xc1',      # mov r9, rax   ; check if (dividend is negative) XOR (divisor is negative)
    '\x4c\x89\xd2',      # mov rdx, r10  ;   .
    '\x49\xc1\xe9\x3f',  # shr r9, 63    ;   .
    '\x48\xc1\xea\x3f',  # shr rdx, 63   ;   .
    '\x49\x31\xd1',      # xor r9, rdx   ;   .
    '\x0f\x84' + '__B_', # jz <B>        ;   (if not, goto B)
    '\x4d\x31\xc9',      # xor r9, r9    ; r9 := -divisor + sign(divisor)
    '\x4d\x29\xd1',      # sub r9, r10   ;   subtract divisor
    '\x4c\x89\xd2',      # mov rdx, r10  ;   add sign of divisor
    '\x48\xc1\xfa\x3f',  # sar rdx, 63   ;     .
    '\x48\x83\xca\x01',  # or rdx, 1     ;     .
    '\x49\x01\xd1',      # add r9, rdx   ;     .
  ])
  code['B'] = ''.join([
    '\x4c\x01\xc8',      # add rax, r9
    '\x48\x99',          # cqo ; sign extend rax to rdx:rax
    '\x49\xf7\xfa',      # idiv r10
    push_result,
    '\xe9' + '__Z_',     # jmp .end
  ])
  code['X'] = boom_code_for(i18n.i18n('Division by zero'))
  return _switch('ABX', code)

def _primitive_pow():
  code = {}
  code['A'] = ''.join([
    '\x5a',                 # pop rdx       ; exponent
    '\x48\x85\xd2',         # test rdx, rdx ; (check for negative exponent)
    '\x0f\x8c' + '__X_',    # jl <error>
    '\x41\x5a',             # pop r10       ; base
    '\x48\xb8\x01\x00\x00\x00\x00\x00\x00\x00', # mov rax, 1 ; accumulator
  ])
  #.loop:
  code['B'] = ''.join([
    '\x48\x85\xd2',         # test rdx, rdx
    '\x0f\x84' + '__D_',    # jz .end
    '\x49\x89\xd1',         # mov r9, rdx
    '\x49\x83\xe1\x01',     # and r9, 1
    '\x49\x83\xf9\x00',     # cmp r9, 0
    '\x0f\x84' + '__C_',    # jz .cont
    '\x49\x0f\xaf\xc2',     # imul rax, r10
  ])
  #.cont:
  code['C'] = ''.join([
    '\x4d\x0f\xaf\xd2',     # imul r10, r10
    '\x48\xd1\xea',         # shr rdx, 1
    '\xe9' + '__B_',        # jmp .loop
  ])
  #.end:
  code['D'] = ''.join([
    '\x50',                 # push rax
    '\xe9' + '__Z_',        # jmp .end
  ])
  code['X'] = boom_code_for(i18n.i18n('Negative exponent'))
  return _switch('ABCDX', code)

Inline = {

## board commands

  i18n.i18n('PutStone'): _primitive_PutStone(),

  i18n.i18n('TakeStone'): _primitive_TakeStone(), 

  i18n.i18n('Move'): _primitive_Move(),

  i18n.i18n('GoToOrigin'): ''.join([
    '\x4d\x31\xdb', # xor r11, r11
    '\x4d\x31\xe4', # xor r12, r12
  ]),

  i18n.i18n('ClearBoard'): _primitive_ClearBoard(),

  i18n.i18n('numStones'): ''.join([
      '\x41\x59',             # pop r9 ; pop a color
      '\x4c\x89\xe0',         # mov rax, r12  ; rax = y
      '\x49\xf7\xed',         # imul r13 ; rax = width * y
      '\x4c\x01\xd8',         # add rax, r11  ; rax = width * y + x
      '\x48\xc1\xe0\x04',     # shl rax, 4    ; rax = 16 * width * y + 16 * x
      '\x48\x01\xd8',         # add rax, rbx  ; rax = rbx[16 * width * y + 16 * x]
      '\x48\x31\xd2',         # xor rdx, rdx
      '\x42\x8b\x14\x88',     # mov edx, dword [rax + 4 * r9] ; rdx -> num stones
      '\x52',                 # push rdx
  ]),

  i18n.i18n('existStones'): ''.join([
      '\x41\x59',             # pop r9 ; pop a color
      '\x4c\x89\xe0',         # mov rax, r12  ; rax = y
      '\x49\xf7\xed',         # imul r13 ; rax = width * y
      '\x4c\x01\xd8',         # add rax, r11  ; rax = width * y + x
      '\x48\xc1\xe0\x04',     # shl rax, 4    ; rax = 16 * width * y + 16 * x
      '\x48\x01\xd8',         # add rax, rbx  ; rax = rbx[16 * width * y + 16 * x]
      '\x48\x31\xd2',         # xor rdx, rdx
      '\x42\x8b\x14\x88',     # mov edx, dword [rax + 4 * r9] ; edx -> num stones
      '\x85\xd2',             # test edx, edx
      '\x0f\x95\xc2',         # setnz dl
      '\x48\x0f\xb6\xd2',     # movzx rdx, dl
      '\x52',                 # push rdx
  ]),

  i18n.i18n('canMove'): _primitive_canMove(),

## min / max functions

  i18n.i18n('minBool'): '\x6a\x00',  # push 0
  i18n.i18n('maxBool'): '\x6a\x01',  # push 1
  i18n.i18n('minColor'): '\x6a\x00', # push 0
  i18n.i18n('maxColor'): '\x6a\x03', # push 3
  i18n.i18n('minDir'): '\x6a\x00',   # push 0
  i18n.i18n('maxDir'): '\x6a\x03',   # push 3

## relational operators

  i18n.i18n('=='): relop('\x0f\x94\xc0'), # sete al
  i18n.i18n('/='): relop('\x0f\x95\xc0'), # setne al
  i18n.i18n('<'): relop('\x0f\x9c\xc0'),  # setl al
  i18n.i18n('<='): relop('\x0f\x9e\xc0'), # setle al
  i18n.i18n('>'): relop('\x0f\x9f\xc0'),  # setg al
  i18n.i18n('>='): relop('\x0f\x9d\xc0'), # setge al

## boolean operators

  i18n.i18n('not'): ''.join([
      '\x48\x83\x34\x24\x01', # xor qword [rsp], 1
  ]),
  i18n.i18n('&&'): ''.join([
      '\x58',         # pop rax
      '\x5a',         # pop rdx
      '\x48\x21\xd0', # and rax, rdx
      '\x50',         # push rax
  ]),
  i18n.i18n('||'): ''.join([
      '\x58',         # pop rax
      '\x5a',         # pop rdx
      '\x48\x09\xd0', # or rax, rdx
      '\x50',         # push rax
  ]),

## arithmetic operators

  i18n.i18n('+'): ''.join([
      '\x58',         # pop rax
      '\x5a',         # pop rdx
      '\x48\x01\xd0', # add rax, rdx
      '\x50',         # push rax
  ]),
  i18n.i18n('-'): ''.join([
      '\x5a',         # pop rdx
      '\x58',         # pop rax
      '\x48\x29\xd0', # sub rax, rdx
      '\x50',         # push rax
  ]),
  i18n.i18n('*'): ''.join([
      '\x58',         # pop rax
      '\x5a',         # pop rdx
      '\x48\xf7\xe2', # mul rdx
      '\x50',         # push rax
  ]),

  i18n.i18n('^'): _primitive_pow(),
  #''.join([
  #   '\x5a\x41\x5a\xb8\x01\x00\x00\x00\x48\x85\xd2\x74\x1a\x49\x89\xd1',
  #   '\x49\x83\xe1\x01\x49\x83\xf9\x00\x74\x04\x49\x0f\xaf\xc2\x4d\x0f',
  #   '\xaf\xd2\x48\xd1\xea\xeb\xe1\x50'
  #]),

  i18n.i18n('div'): _primitive_divmod('div'),

  i18n.i18n('mod'): _primitive_divmod('mod'),

## polymorphic "next"

  P(i18n.i18n('next'), 'Bool'): ''.join([
      '\x58',             # pop rax
      '\x48\x83\xf0\x01', # xor rax, 1
      '\x50',             # push rax
  ]),

  P(i18n.i18n('next'), 'Int'): ''.join([
      '\x58',             # pop rax
      '\x48\xff\xc0',     # inc rax
      '\x50',             # push rax
  ]),

  P(i18n.i18n('next'), 'Color'): ''.join([
      '\x58',             # pop rax
      '\x48\xff\xc0',     # inc rax
      '\x48\x83\xe0\x03', # and rax, 0x3
      '\x50',             # push rax
  ]),

  P(i18n.i18n('next'), 'Dir'): ''.join([
      '\x58',             # pop rax
      '\x48\xff\xc0',     # inc rax
      '\x48\x83\xe0\x03', # and rax, 0x3
      '\x50',             # push rax
  ]),

## polymorphic "prev"

  P(i18n.i18n('prev'), 'Bool'): ''.join([
      '\x58',             # pop rax
      '\x48\x83\xf0\x01', # xor rax, 1
      '\x50',             # push rax
  ]),

  P(i18n.i18n('prev'), 'Int'): ''.join([
      '\x58',             # pop rax
      '\x48\xff\xc8',     # dec rax
      '\x50',             # push rax
  ]),

  P(i18n.i18n('prev'), 'Color'): ''.join([
      '\x58',             # pop rax
      '\x48\x83\xc0\x03', # add rax, 0x3
      '\x48\x83\xe0\x03', # and rax, 0x3
      '\x50',             # push rax
  ]),

  P(i18n.i18n('prev'), 'Dir'): ''.join([
      '\x58',             # pop rax
      '\x48\x83\xc0\x03', # add rax, 0x3
      '\x48\x83\xe0\x03', # and rax, 0x3
      '\x50',             # push rax
  ]),

## polymorphic "opposite"

  P(i18n.i18n('opposite'), 'Bool'):
    boom_code_for(i18n.i18n('The argument to opposite should be a direction or an integer')),

  P(i18n.i18n('opposite'), 'Int'): ''.join([
      '\x58',             # pop rax
      '\x48\xf7\xd8',     # neg rax
      '\x50',             # push rax
  ]),

  P(i18n.i18n('opposite'), 'Color'):
    boom_code_for(i18n.i18n('The argument to opposite should be a direction or an integer')),

  P(i18n.i18n('opposite'), 'Dir'): ''.join([
      '\x58',             # pop rax
      '\x48\x83\xf0\x02', # xor rax, 0x2
      '\x50',             # push rax
  ]),

}

for bt in ['Bool', 'Int', 'Color', 'Dir']:
  Inline[P(i18n.i18n('unary-'), bt)] = Inline[P(i18n.i18n('opposite'), bt)]

#### Undo builtins

def _primitive_undo_enter():
  code = {}
  code['A'] = ''.join([
    '\x4c\x89\xe8',     # mov rax, r13   ; rax = width
    '\x49\xf7\xee',     # imul r14  ; rax = width * height
    '\x48\xc1\xe0\x04', # shl rax, 4     ; rax = 16 * rax (times the cell size in bytes)
    '\x48\x31\xd2',     # xor rdx, rdx
  ])
  code['B'] = ''.join([
    # while rax > 0
    '\x48\x83\xe8\x08',   # sub rax, 8 ; qword size
    '\x0f\x8c' + '__C_',  # jl <end>
    '\xff\x34\x03',       # push qword [rbx + rax]
    '\xe9' + '__B_',      # jmp <B>
  ])
  code['C'] = ''.join([
    '\x41\x53', # push r11 ; x
    '\x41\x54', # push r12 ; y
  ])
  return _switch('ABC', code)

def _primitive_undo_leave():
  code = {}
  code['A'] = ''.join([
    '\x41\x5c',         # pop r12 ; y
    '\x41\x5b',         # pop r11 ; x

    '\x4c\x89\xe8',     # mov rax, r13   ; rax = width
    '\x49\xf7\xee',     # imul r14  ; rax = width * height
    '\x48\xc1\xe0\x04', # shl rax, 4     ; rax = 16 * rax (times the cell size in bytes)
    '\x4d\x31\xc9',     # xor r9, r9
  ])
  code['B'] = ''.join([
    # while r9 < rax
    '\x49\x39\xc1',       # cmp r9, rax
    '\x0f\x8d' + '__Z_',  # jge <end>
    '\x5a',               # pop rdx
    '\x4a\x89\x14\x0b',   # mov qword [rbx + r9], rdx
    '\x49\x83\xc1\x08',   # add r9, 8 ; qword size
    '\xe9' + '__B_',      # jmp <B>
  ])
  return _switch('AB', code)

Undo_builtins = {
  'enter': _primitive_undo_enter(),
  'leave': _primitive_undo_leave(),
}

