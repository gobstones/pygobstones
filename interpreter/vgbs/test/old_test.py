#!/usr/bin/python
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

import os
import sys
import platform
import subprocess

def msg(x):
  sys.stdout.write(x)
  sys.stdout.flush()

def program_for(exprs):
  variables = []
  def expr_eval(i, e):
    if isinstance(e, Operation):
      if e.nretvals == 1: 
        variables.append('x_%i' % (i,))
        return 'x_%i := f0_%i()' % (i, i,)
      else:
        vs = ['x_%i_%i' % (i, j) for j in range(e.nretvals)]
        variables.extend(vs)
        return '(%s) := f0_%i()' % (','.join(vs), i,)
    else:
      variables.append('x_%i' % (i,))
      return 'x_%i := %s' % (i, e)
  R = range(len(exprs))
  prog = []
  for i, e in zip(R, exprs):
    if isinstance(e, Operation):
      prog.append('function f0_%i() {' % (i,))
      prog.append(e.code)
      prog.append('}')
  prog.append('procedure Main() {')
  prog.append(''.join(['  %s\n' % (expr_eval(i, e),) for i, e in zip(R, exprs)]))
  prog.append('  return (%s)\n' % (', '.join(variables),))
  prog.append('}\n')
  return '\n'.join(prog)

def group(lst, n):
  res = []
  sublst = []
  for x in lst:
    sublst.append(x)
    if len(sublst) == n:
      res.append(sublst)
      sublst = []
  if len(sublst) > 0:
    res.append(sublst)
  return res

def flatten(lst):
  res = []
  for x in lst:
    if isinstance(x, list):
      res.extend(flatten(x))
    else:
      res.append(x)
  return res

def list_half1(lst): return lst[:len(lst) / 2]
def list_half2(lst): return lst[len(lst) / 2:]

def all_permutations(xs):
  if xs == []:
    yield []
  else:
    for i in range(len(xs)): 
      for p in all_permutations(xs[:i] + xs[i + 1:]):
        yield [xs[i]] + p

def all_subsets(xs):
  if xs == []:
    yield []
  else:
    for s in all_subsets(xs[1:]):
      yield s
      yield [xs[0]] + s

def all_slicings(xs):
  if len(xs) == 0:
    yield []
  elif len(xs) == 1:
    yield [xs]
  else:
    for s in all_slicings(xs[1:]):
      yield [[xs[0]]] + s
      yield [[xs[0]] + s[0]] + s[1:]

class Operation:
  def __init__(self, nretvals, code, replace={}):
    self.nretvals = nretvals
    for k, v in replace.items():
      code = code.replace('@' + k, v)
    self.code = code

def Block(code):
  return Operation(1, code)

def build_all_switches(mn, values):
  i = 0
  for subset in all_subsets(values):
    for perm in all_permutations(subset):
      for branches in all_slicings(perm):
        stmt = 'x := %s\n' % (mn,)
        stmt += 'repeatWith i in 1..2{'
        stmt += 'case(x)of\n'
        for branch in branches:
          stmt += ','.join([str(br) for br in branch]) + '->{x:=%s;res:=%s;}' % (values[i % len(values)], i,)
          i += 1
        stmt += '_->{x:=%s;res:=%s}' % (values[i % len(values)], i,)
        stmt += '}\n'
        stmt += 'return (res)'
        yield Block(stmt)

def build_all_if_switches(mn, values):
  i = 0
  for subset in all_subsets(values):
    for perm in all_permutations(subset):
      for branches in all_slicings(perm):
        stmt = 'x := %s\n' % (mn,)
        stmt += 'if (False) {}\n'
        for branch in branches:
          stmt += 'else { if (%s) {res:=%s;}' % (
                    '||'.join(['x == %s' % (lit,) for lit in branch]), i)
          i += 1
        stmt += 'else {res:=%s}' % (i,)
        stmt += '}' * len(branches)
        stmt += 'return (res)'
        yield Block(stmt)

def build_nested_while(n, k):
  if n == 0:
    return 'res := res + 1 + x1'
  else:
    return 'x%i := 0; while (x%i < %i) { %s x%i := x%i + 1 }' % (
           n, n, k, build_nested_while(n - 1, k), n, n)

def build_nested_repeatWith(n, mn, mx):
  if n == 0:
    return 'res := res + 1'
  else:
    return 'repeatWith x%i in %s..%s { %s }' % (
           n, mn, mx, build_nested_repeatWith(n - 1, mn, mx))

def build_nested_if(n):
  if n == 0:
    return '{}'
  else:
    return 'if (k mod 2 == 1) { k := k div 2; res := 10 * res + 1; %s } else { k := k div 2; res := 10 * res; %s }' % (
             build_nested_if(n - 1), build_nested_if(n - 1))

def run_gobstones(command):
  result = os.popen(command).read()
  result = result.split('\n')
  while len(result) > 0 and result[-1] == '': result = result[:-1]
  if len(result) == 0 or result[-1] != 'OK':
    return 'FAILED', {}
  else:
    result = result[:-1]
    dic = []
    for res in result:
      var, val = res.split('->')
      dic.append((var.strip(' \t\r\n'), val.strip(' \t\r\n')))
    return 'OK', dic

def run_windows(cmd):
    return subprocess.Popen((cmd), stdout=subprocess.PIPE).stdout.read()

def run_gobstones_windows(command):
    result = run_windows(command)
    
    #result = os.popen(command).read()
    result = result.replace('\r', '')
    result = filter(None, result.split('\n'))
    while len(result) > 0 and result[-1] == '': result = result[:-1]
    if len(result) == 0 or result[-1] != 'OK':
        return 'FAILED', {}
    else:
        result = result[:-1]
        dic = []
        for res in result:
            var, val = res.split('->')
            dic.append((var.strip(' \t\r\n'), val.strip(' \t\r\n')))
        return 'OK', dic

class Tester:
  def __init__(self):
    self.total = 0
    self.ok = 0
    self.failed = 0
  def run_py_gobstones(self):
      return run_gobstones('./pyMain')
  def run_hs_gobstones(self):
      return run_gobstones('./hsMain')
  def test_retvals(self, count=1):
    msg('\tHaskell...')
    rh = self.run_hs_gobstones()
    if rh[0] == 'OK':
      msg(' (the program gives a result)')
    else:
      msg(' (THE PROGRAM FAILS)')

    msg('\n\tPython...')
    rp = self.run_py_gobstones()
    if rp[0] == 'OK':
      msg(' (the program gives a result)')
    else:
      msg(' (THE PROGRAM FAILS)')

    if rh == rp:
      msg('   [OK]\n')
      self.ok += count
    else:
      print()
      print('--!!! Tests differ.')
      print('--------Haskell:\n', rh)
      print('--------Python :\n', rp)
      self.failed += count
      #assert False
    self.total += count

class WindowsTester(Tester):
    def run_hs_gobstones(self):
        return run_gobstones_windows('python hsMain_win.py')
    def run_py_gobstones(self):
        return run_gobstones_windows('python pyMain_win.py')

types = ['Bool', 'Color', 'Dir', 'Int']
values = {
  'Bool':  ['True', 'False'],
  'Color': ['Azul', 'Negro', 'Rojo', 'Verde'],
  'Dir':   ['Norte', 'Este', 'Sur', 'Oeste'],
  'Int':   [-5, -1, 0, 1, 2, 3, 10]
}
all_values = flatten([values[t] for t in types])
operators = {
  'relop': ['==', '<', '<=', '>=', '>', '/='],
  'boolop': ['&&', '||'],
  'arith': ['+', '-', '*'],
  'arith_div': ['div', 'mod'],
  'arith_pow': ['^'],
  'all_arith': ['+', '-', '*', 'div', 'mod', '^']
}
functions = {
  'poly': ['siguiente', 'previo'],
  'poly(dir,int)': ['opuesto', '-'],
}

test_basic_values = [
  values['Bool'],
  values['Color'],
  values['Dir'],
]

test_operators = [
  ['%s %s %s' % (x, op, y) for t in types for x in values[t] for y in values[t] for op in operators['relop']],
  ['%s %s %s' % (x, op, y) for t in ['Bool'] for x in values[t] for y in values[t] for op in operators['boolop']],
  ['%s %s %s' % (x, op, y) for t in ['Int'] for x in values[t] for y in values[t] for op in operators['arith']],
  ['%s %s %s' % (x, op, y) for t in ['Int'] for x in values[t] for y in values[t] if y >= 0 for op in operators['arith_pow']], # non-negative exponents
  ['%s %s %s' % (x, op, y) for t in ['Int'] for x in values[t] for y in values[t] if y != 0 for op in operators['arith_div']], # division by non-zero
  ['not %s' % (x,) for x in values['Bool']],
  ['%s(%s)' % (f, x,) for t in types for x in values[t] for f in functions['poly']],
  ['%s(%s)' % (f, x,) for t in ['Dir', 'Int'] for x in values[t] for f in functions['poly(dir,int)']],
]

test_precedence = [
  [Block('''res := True
            repeatWith x in 1..5 {
            repeatWith y in 1..5 {
            repeatWith z in 1..5 {
               if ( (x %s y %s z) /= ((x %s y) %s z) ) { res := False }
            }}}
            return (res)''' % (op1, op2, op1, op2))
              for op1 in operators['arith'] + operators['arith_pow']
              for op2 in operators['arith'] + operators['arith_pow']],
  [Block('''res := True
            repeatWith x in minBool()..maxBool() {
            repeatWith y in minBool()..maxBool() {
            repeatWith z in minBool()..maxBool() {
               if ( (x %s y %s z) /= ((x %s y) %s z) ) { res := False }
            }}}
            return (res)''' % (op1, op2, op1, op2))
              for op1 in operators['boolop']
              for op2 in operators['boolop']],
  [Block('''res := True
            repeatWith a in 2..5 {
            repeatWith b in 2..5 {
            repeatWith c in -1..1 {
            repeatWith d in minBool()..maxBool() {
               r := (a %s b) + c
               if ((a %s b %s r %s d) /= (((a %s b) %s r) %s d)) { res := False }
               r := (b %s a) + c
               if ((d %s r %s b %s a) /= (d %s (r %s (b %s a)))) { res := False }
            }}}}
            return (res)''' % (op1,
                               op1, op2, op3, op1, op2, op3,
                               op1,
                               op3, op2, op1, op3, op2, op1))
              for op1 in operators['all_arith']
              for op2 in operators['relop']
              for op3 in operators['boolop']],
  Block('''res := True
            repeatWith x in minBool()..maxBool() {
            repeatWith y in minBool()..maxBool() {
               if ( not x && not y /= (not x) && (not y) ) { res := False }
               if ( not x || not y /= (not x) || (not y) ) { res := False }
            }}
            return (res)'''),
  '1 - 2 - 3 - 4 - 5 - 6 - 7 - 8 - 9',
  '-1 * -2 * -3 * -4 * -5 * -6 * -7 * -8 * -9',
  Block('x := 10; res := x-1; return (res)'),
]

test_control1 = [
  Block('''Skip
            res := 0
            Skip
            res := res + 1
            Skip
            res := res + 1
            Skip
            res := res + 1
            Skip
            res := res + 1
            Skip
            res := 0
            Skip
            res := res + 1
            Skip
            res := res + 1
            Skip
            res := res + 1
            Skip
            res := res + 1
            Skip
            return (3 * res + 1)'''),
# if
  [Block('res := Rojo if (%s) { res := Azul } return (res)' % (x,)) for x in values['Bool']],
  [Block('res := Rojo; if (%s) { res := Azul; }; return (res)' % (x,)) for x in values['Bool']],
  [Block('res := Rojo if (not %s) { res := Azul } return (res)' % (x,)) for x in values['Bool']],
  [Block('if (%s) { res := Azul } else { res := Rojo } return (res)' % (x,)) for x in values['Bool']],
  [Block('if (not %s) { res := Azul } else { res := Rojo } return (res)' % (x,)) for x in values['Bool']],
  [Block('res := Rojo if (%s == %s) { res := Azul }; return (res)' % (x, y))
           for t in types
           for x in values[t]
           for y in values[t]],
  [Block('res := Verde if (%s == %s) { res := Azul } else { res := Rojo } return (res)' % (x, y))
           for t in types
           for x in values[t]
           for y in values[t]],
  [Block('res := 0; k := %i; %s; return (res);' % (k, build_nested_if(2),)) for k in range(2**2)],
  [Block('res := 0; k := %i; %s; return (res);' % (k, build_nested_if(3),)) for k in range(2**3)],
# case
  [Block('''res := 0
            case (res) of
              0 -> { res := 1 }
              1 -> { res := 2 }
              _ -> { res := 3 }
            return (res)''')],
  [Block('''res := 0
            case (res) of
              1 -> { res := 2 }
              0 -> { res := 1 }
              _ -> { res := 3 }
            return (res)''')],
  [Block('''res := 0
            case (res) of
              1 -> { res := 2 }
              2 -> { res := 1 }
              _ -> { res := 3 }
            return (res)''')],
  [Block('''res := 0
            case (res) of
              0,1 -> { res := 2 }
              2 -> { res := 1 }
              _ -> { res := 3 }
            return (res)''')],
  [Block('''res := 0
            case (res) of
              1,0 -> { res := 2 }
              2 -> { res := 1 }
              _ -> { res := 3 }
            return (res)''')],
  [Block('''res := 0
            case (res) of
              1 -> { res := 2 }
              2,3,4,5,0,6,7 -> { res := 1 }
              _ -> { res := 3 }
            return (res)''')],
  list(build_all_switches('0', [-1, 0, 1])),
  list(build_all_switches('minBool()', values['Bool'])),
  list(build_all_switches('minDir()', ['Este', 'Sur'])),
  list(build_all_switches('minColor()', ['Azul', 'Negro', 'Rojo'])),
]

test_control2 = [
  list(build_all_if_switches('-1', [-1, 0, 1])),
  list(build_all_if_switches('maxBool()', values['Bool'])),
  list(build_all_if_switches('maxDir()', ['Norte', 'Oeste', 'Sur'])),
  list(build_all_if_switches('maxColor()', ['Rojo', 'Verde'])),
]

#VeryBigInteger = 340282366920938463463374607431768211453
VeryBigInteger = 1125899906842624

test_control3 = [
# blocks
  Block('''res := 0
           { { res := res + 1 }
             { { res := res + 2 }
               { { res := res + 4 }
                 { { res := res + 8 }
                   { res := res + 16 } } } } }
           return (res)
        '''),
# while
  # sum and count digits
  [Block('''{ { { { x := %s ds := 0 cd := 0 } } } }
            while (x > 0) { { { {
                {
                if (x mod 2 == 1) { { { {
                   ds := ds + 1
                } } } }
                }
                repeatWith i in 1..1 {
                  {
                   if (True) { { { { { x := x div 2 } } } } }
                   if (True) { cd := cd + 1 }
                  }
                }
            } } } }
            return (100 * ds + cd)
        ''' % (num,)) for num in [0,1,10,15,16,100,1000,VeryBigInteger]],
  # nested whiles
  [Block('res := 0; %s; return (res)' % (build_nested_while(n, 2),)) for n in range(1, 10)],
  [Block('res := 0; %s; return (res)' % (build_nested_while(n, 3),)) for n in range(1, 7)],
  [Block('res := 0; %s; return (res)' % (build_nested_while(n, 5),)) for n in range(1, 5)],
  [Block('res := 0; %s; return (res)' % (build_nested_while(n, 7),)) for n in range(1, 4)],
  [Block('res := 0; %s; return (res)' % (build_nested_while(n, 10),)) for n in range(1, 3)],
  # Collatz conjecture (3n + 1)
  [Block('x:=%s n:=0 while(x/=1){if(x mod 2==0){x:=x div 2}else{x:=3*x+1}n:=n+1}return(n)' % (
           num,)) for num in range(1, 50)],
  # while (False)
  [Block('res := Azul while(False) { res := Rojo } return (res)')],
  [Block('res := False while(res) { res := True } return (res)')],
# repeatWith
  [Block('res := 0 repeatWith i in %s..%s { res := res + 1 } return (res)' % rg)
    for rg in [ # min/max
                ('minBool()', 'maxBool()'),
                ('minDir()', 'maxDir()'),
                ('minColor()', 'maxColor()'),
                # max/min
                ('maxBool()', 'minBool()'),
                ('maxDir()', 'minDir()'),
                ('maxColor()', 'minColor()'),
                # max/max
                ('maxBool()', 'maxBool()'),
                ('maxDir()', 'maxDir()'),
                ('maxColor()', 'maxColor()'),
                # min/min
                ('minBool()', 'minBool()'),
                ('minDir()', 'minDir()'),
                ('minColor()', 'minColor()')] +
              [ (x, x) for x in all_values ] +
              [ (x, 'siguiente(%s)' % (x,)) for x in all_values ] +
              [ ('previo(%s)' % (x,), x) for x in all_values ] +
              [ ('previo(%s)' % (x,), 'siguiente(%s)' % (x,)) for x in all_values ] +
              [ (i, j) for i in [-10,-1,0,1,10] for j in [-10,-1,0,1,10]]
  ],
  [Block('res := 0; %s; return (res)' % (build_nested_repeatWith(n, 'minBool()', 'maxBool()'),)) for n in range(1, 10)],
  [Block('res := 0; %s; return (res)' % (build_nested_repeatWith(n, 'minDir()', 'maxDir()'),)) for n in range(1, 7)],
  [Block('res := 0; %s; return (res)' % (build_nested_repeatWith(n, 'minColor()', 'maxColor()'),)) for n in range(1, 7)],
]

PuedeAvanzar = '(puedeMover(Norte) || puedeMover(Este))'
Avanzar = '''{ 
      if (puedeMover(Norte)) {
        Mover(Norte)
      } else {
        Mover(Este)
        while (puedeMover(Sur)) { Mover(Sur) }
      }
  }'''
lstIrAlOrigen = ['IrAlOrigen()', '{ while (puedeMover(Sur)) { Mover(Sur) } while (puedeMover(Oeste)) { Mover(Oeste) } }']
lstVaciarTablero = ['VaciarTablero()',
    '''
      while (puedeMover(Sur)) { Mover(Sur) }
      while (puedeMover(Oeste)) { Mover(Oeste) }

      repeatWith col in minColor()..maxColor() { while (hayBolitas(col)) { Sacar(col) } }
      while (puedeMover(Norte) || puedeMover(Este)) {
      if (puedeMover(Norte)) {
        Mover(Norte)
      } else {
        Mover(Este)
        while (puedeMover(Sur)) { Mover(Sur) }
      }
      repeatWith col in minColor()..maxColor() {
        while (hayBolitas(col)) { Sacar(col) }
      }
    }''']
              
test_builtins = [
  [Operation(2, '''
    @VaciarTablero @IrAlOrigen 
    np := 0
    repeatWith i in 1..10 {
      Poner(@Elegido)
      if (not hayBolitas(@Elegido)) { BOOM("hayBolitas") }
      if (nroBolitas(@Elegido) /= i) { BOOM("nroBolitas") }
      repeatWith c in minColor()..maxColor() {
        np := np + 1
        if (c /= @Elegido) {
          if (hayBolitas(c)) { BOOM("hayBolitas") }
          if (nroBolitas(c) /= 0) { BOOM("nroBolitas") }
        }
      }
    }
    return (nroBolitas(@Elegido), np)
    ''', replace={'VaciarTablero': vt, 'IrAlOrigen': io, 'Elegido': col})
        for vt in lstVaciarTablero
        for io in lstIrAlOrigen
        for col in values['Color']],

  Operation(1, '''
    VaciarTablero() IrAlOrigen()
    np := 0
    repeatWith elegido in minColor()..maxColor() {
      repeatWith i in 1..10 {
        Poner(elegido)
        if (not hayBolitas(elegido)) { BOOM("hayBolitas") }
        if (nroBolitas(elegido) /= i) { BOOM("nroBolitas") }
        repeatWith c in minColor()..maxColor() {
          np := np + 1
          if (c /= elegido) {
            if (hayBolitas(c)) { BOOM("hayBolitas") }
            if (nroBolitas(c) /= 0) { BOOM("nroBolitas") }
          }
        }
      }
      repeatWith i in 1..10 {
          if (not hayBolitas(elegido)) { BOOM("hayBolitas") }
          if (nroBolitas(elegido) /= 10 - i + 1) { BOOM("nroBolitas") }
          repeatWith c in minColor()..maxColor() {
            np := np + 1
            if (c /= elegido) {
              if (hayBolitas(c)) { BOOM("hayBolitas") }
              if (nroBolitas(c) /= 0) { BOOM("nroBolitas") }
            }
          }
          Sacar(elegido)
      }
      if (hayBolitas(elegido)) { BOOM("hayBolitas") }
      if (nroBolitas(elegido) /= 0) { BOOM("nroBolitas") }
    }
    return (np)
    '''),

  [Operation(6, '''
    @VaciarTablero
    @IrAlOrigen
    totA := 0
    totN := 0
    totR := 0
    totV := 0
    while (@PuedeAvanzar) {
      @Avanzar
      totA := totA + nroBolitas(Azul)
      totN := totN + nroBolitas(Negro)
      totR := totR + nroBolitas(Rojo)
      totV := totV + nroBolitas(Verde)
    }
    if (totA /= 0 || totN /= 0 || totR /= 0 || totV /= 0) {
      BOOM("VaciarTablero")
    }
    @IrAlOrigen
    fils := 1; while (puedeMover(Norte)) { Mover(Norte); fils := fils + 1 }
    cols := 1; while (puedeMover(Este)) { Mover(Este); cols := cols + 1 }
    if (fils /= 9 || cols /= 9) { 
      BOOM("IrAlOrigen")
    }

    @IrAlOrigen
    xA := 0
    xN := 42
    xR := 127
    xV := 90000
    while (@PuedeAvanzar) {
      xA := (6 * xA + 5) mod 11
      xN := (12 * xN + 3) mod 17
      xR := (14 * xR + 9) mod 23
      xV := (3 * xV + 5) mod 31

      if (hayBolitas(Azul)) { BOOM("hayAzul") }
      if (hayBolitas(Negro)) { BOOM("hayNegro") }
      if (hayBolitas(Rojo)) { BOOM("hayRojo") }
      if (hayBolitas(Verde)) { BOOM("hayVerde") }

      if (nroBolitas(Azul) /= 0) { BOOM("nroAzul") }
      if (nroBolitas(Negro) /= 0) { BOOM("nroNegro") }
      if (nroBolitas(Rojo) /= 0) { BOOM("nroRojo") }
      if (nroBolitas(Verde) /= 0) { BOOM("nroVerde") }
      repeatWith i in 1..xA { Poner(Azul) }
      if (nroBolitas(Azul) /= xA) { BOOM("nroAzul") }
      if (nroBolitas(Negro) /= 0) { BOOM("nroNegro") }
      if (nroBolitas(Rojo) /= 0) { BOOM("nroRojo") }
      if (nroBolitas(Verde) /= 0) { BOOM("nroVerde") }
      repeatWith i in 1..xN { Poner(Negro) }
      if (nroBolitas(Azul) /= xA) { BOOM("nroAzul") }
      if (nroBolitas(Negro) /= xN) { BOOM("nroNegro") }
      if (nroBolitas(Rojo) /= 0) { BOOM("nroRojo") }
      if (nroBolitas(Verde) /= 0) { BOOM("nroVerde") }
      repeatWith i in 1..xR { Poner(Rojo) }
      if (nroBolitas(Azul) /= xA) { BOOM("nroAzul") }
      if (nroBolitas(Negro) /= xN) { BOOM("nroNegro") }
      if (nroBolitas(Rojo) /= xR) { BOOM("nroRojo") }
      if (nroBolitas(Verde) /= 0) { BOOM("nroVerde") }
      repeatWith i in 1..xV { Poner(Verde) }
      if (nroBolitas(Azul) /= xA) { BOOM("nroAzul") }
      if (nroBolitas(Negro) /= xN) { BOOM("nroNegro") }
      if (nroBolitas(Rojo) /= xR) { BOOM("nroRojo") }
      if (nroBolitas(Verde) /= xV) { BOOM("nroVerde") }
      @Avanzar
    }

    @IrAlOrigen
    xA := 0
    xN := 42
    xR := 127
    xV := 90000
    while (@PuedeAvanzar) {
      xA := (6 * xA + 5) mod 11
      xN := (12 * xN + 3) mod 17
      xR := (14 * xR + 9) mod 23
      xV := (3 * xV + 5) mod 31
      if (nroBolitas(Azul) /= xA) { BOOM("nroAzul") }
      if (nroBolitas(Negro) /= xN) { BOOM("nroNegro") }
      if (nroBolitas(Rojo) /= xR) { BOOM("nroRojo") }
      if (nroBolitas(Verde) /= xV) { BOOM("nroVerde") }
      repeatWith col in minColor()..maxColor() {
        while (hayBolitas(col)) { Sacar(col) }
        if (hayBolitas(col)) { BOOM("hay/Sacar") }
      }
      @Avanzar
    }

    @IrAlOrigen
    while (@PuedeAvanzar) {
      @Avanzar
      totA := totA + nroBolitas(Azul)
      totN := totN + nroBolitas(Negro)
      totR := totR + nroBolitas(Rojo)
      totV := totV + nroBolitas(Verde)
    }
    return (totA, totN, totR, totV, fils, cols)
  ''', replace={'PuedeAvanzar': PuedeAvanzar, 'Avanzar': Avanzar, 'VaciarTablero': vt, 'IrAlOrigen': io})
        for vt in lstVaciarTablero
        for io in lstIrAlOrigen],
]

test_cases = [
  test_basic_values,
  test_operators,
  test_precedence,
  test_control1,
  test_control2,
  test_control3,
  test_builtins,
]

test_cases = group(flatten(test_cases), 128)

if platform.system() == "Windows":
    tester = WindowsTester()
else:
    tester = Tester()

Nskip = 0
#Nskip = 1

it = 0
for exprs in test_cases:
  print('[%.3i] Testing %i expressions' % (it, len(exprs),))
  it += 1
  if it <= Nskip:
    print('\t(skipped)')
    continue
  f = open('examples/test.gbs', 'w')
  f.write(program_for(exprs))
  f.close()
  tester.test_retvals(len(exprs))

print('*** Finished testing')
print('  Total   :', tester.total)
print('  OK      :', tester.ok)

