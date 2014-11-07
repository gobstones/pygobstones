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

import re

import common.utils
import common.i18n as i18n

import lang.gbs_vm
import lang.gbs_builtins
import lang.ast

def external_programs(compiled_program):
  exts = {}
  for eprog, ertn in compiled_program.external_routines.values():
    exts[eprog] = True
  return exts

def base_alpha(n):
  _alpha = 'abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789_'
  r = ''
  while n > 0:
    r = _alpha[n % len(_alpha)] + r
    n /= len(_alpha)
  return r

class Mangler(object):
  def __init__(self):
    self._rtns = {}

  def mangle_routines(self, compiled_program):
    for eprog in external_programs(compiled_program):
      self.mangle_routines(eprog)
    # Overwrite on collisions
    # This should be ok, since mangling ensures
    # same mangled name <=> same implementation
    for rtn in compiled_program.routines.values():
      self._rtns[self.mangle(compiled_program, rtn.name)] = (compiled_program, rtn)
    return self._rtns

  def mangle(self, compiled_program, rtn_name):
    prf = compiled_program.module_prefix 
    if rtn_name in compiled_program.builtins:
      return rtn_name
    elif rtn_name in compiled_program.routines:
      return prf + '$' + rtn_name
    elif rtn_name in compiled_program.external_routines:
      called_prog, called_rtn = compiled_program.external_routines[rtn_name]
      return self.mangle(called_prog, called_rtn.name)
    else:
      assert False

  def mangle_var(self, compiled_program, rtn_name, varname):
    return varname

  def mangle_label(self, label_name):
    return label_name

  def mangle_opcode(self, opcode):
    return opcode

  def tabulation(self):
    return '    '

Opcode_to_compact = {
 'pushConst':    'p',
 'pushFrom':      'v',
 'popTo':       'a',
 'call':         'c',
 'THROW_ERROR':         'b',
 'label':        'l',
 'jump':         'j',
 'jumpIfFalse':  'f',
 'jumpIfNotIn':  'n',
 'return':       'r',
 'returnVars':   'x',
 'enter':        'e',
 'leave':        'z',
 'delVar':       'd',
#
 'procedure':    'P',
 'function':     'F',
 'end':          'X',
}
Compact_to_opcode = {} 
for k, v in Opcode_to_compact.items():
  Compact_to_opcode[v] = k

class CompactMangler(object):
  def __init__(self):
    self._rtns = {}
    self._rtn_cache = {}
    self._var_cache = {}
    self._lab_cache = {}
    self._last_rtn_id = 0
    self._last_var_id = 0
    self._last_lab_id = 0

  def mangle_routines(self, compiled_program):
    for eprog in external_programs(compiled_program):
      self.mangle_routines(eprog)
    # Overwrite on collisions
    # This should be ok, since mangling ensures
    # same mangled name <=> same implementation
    for rtn in compiled_program.routines.values():
      self._rtns[self.mangle(compiled_program, rtn.name)] = (compiled_program, rtn)
    return self._rtns

  def next_rtn_id(self):
    res = 'R%s' % (base_alpha(self._last_rtn_id),)
    self._last_rtn_id += 1
    return res

  def next_var_id(self):
    res = 'V%s' % (base_alpha(self._last_var_id),)
    self._last_var_id += 1
    return res

  def next_lab_id(self):
    res = 'L%s' % (base_alpha(self._last_lab_id),)
    self._last_lab_id += 1
    return res

  def mangle(self, compiled_program, rtn_name):
    prf = compiled_program.module_prefix 
    if rtn_name in compiled_program.builtins:
      return rtn_name
    elif rtn_name in compiled_program.routines and rtn_name == 'Main':
      return prf + '$' + rtn_name
    elif rtn_name in compiled_program.routines:
      k = (compiled_program, rtn_name)
      if k not in self._rtn_cache:
        self._rtn_cache[k] = self.next_rtn_id()
      return self._rtn_cache[k]
    elif rtn_name in compiled_program.external_routines:
      called_prog, called_rtn = compiled_program.external_routines[rtn_name]
      return self.mangle(called_prog, called_rtn.name)
    else:
      assert False

  def mangle_var(self, compiled_program, rtn_name, varname):
    if varname not in self._var_cache:
      self._var_cache[varname] = self.next_var_id()
    return self._var_cache[varname]

  def mangle_label(self, label_name):
    if label_name not in self._lab_cache:
      self._lab_cache[label_name] = self.next_lab_id()
    return self._lab_cache[label_name]

  def mangle_opcode(self, opcode):
    return Opcode_to_compact[opcode]

  def tabulation(self):
    return ''

class GbsVmWriter(object):
  def __init__(self, f, style='verbose'):
    if style == 'verbose':
      self._mangler = Mangler()
    elif style == 'compact':
      self._mangler = CompactMangler()
    else:
      assert False
    self._f = f
  def dump_program(self, compiled_program):
    self._f.write('GBO/1.0\n')
    rtns = self._mangler.mangle_routines(compiled_program)
    rtns = common.utils.seq_sorted(rtns.items())
    for mangled_name, (prog, rtn) in rtns:
      self.dump_routine(prog, rtn)
    self._f.write('%%\n')
  def dump_routine(self, prog, rtn):
    def showop(op):
      # preprocess (mangle)
      if op[0] in ['pushFrom', 'popTo', 'delVar']:
        op = op[0], self._mangler.mangle_var(prog, rtn, op[1])
      elif op[0] in ['label', 'jump', 'jumpIfFalse']:
        op = op[0], self._mangler.mangle_label(op[1])
      elif op[0] in ['jumpIfNotIn']:
        op = op[0], op[1], self._mangler.mangle_label(op[2])
      #
      T = self._mangler.tabulation()

      if op[0] == 'jumpIfNotIn':
        opname, lits, label = op
        return T + '%s %s %s' % (
          self._mangler.mangle_opcode(opname), label, ' '.join([str(x) for x in lits]))
      elif op[0] == 'returnVars':
        opname, nvrs, vrs = op
        return T + '%s %s %s' % (
          self._mangler.mangle_opcode(opname), nvrs, ' '.join([str(x) for x in vrs]))
      elif op[0] == 'call':
        opname, rtn_name, nargs = op
        return T + '%s %s %u' % (
          self._mangler.mangle_opcode(opname), self._mangler.mangle(prog, rtn_name), nargs)
      else:
        op = list(op)
        op[0] = self._mangler.mangle_opcode(op[0])
        return T + ' '.join([str(x) for x in op])

    mname = self._mangler.mangle(prog, rtn.name)

    mangled_params = []
    for p in rtn.params:
      mangled_params.append(self._mangler.mangle_var(prog, rtn.name, p))

    params = ' '.join(mangled_params)
    self._f.write('%s %s %s\n' % (self._mangler.mangle_opcode(rtn.prfn), mname, params))
    for op in rtn.ops:
      self._f.write('%s\n' % (showop(op),))
    self._f.write(self._mangler.mangle_opcode('end') +'\n\n')

class GbsObjectFormatException(Exception):
  pass

class FakeAST(object):
  def __init__(self, filename='???'):
    self.source_filename = filename
    self._source = ''
    self.pos_begin = self.pos_end = common.position.Position(self._source, filename=filename)
  def source(self):
    return self._source
  def description(self):
    return '???'

class GbsVmReader(object):
  def __init__(self, f, filename='...'):
    self._f = f
    self._filename = filename
    self._f_lines = common.utils.read_stripped_lines(f)

  def fail(self, msg):
    raise GbsObjectFormatException(i18n.i18n('Malformed gbo object') + '\n' +
                                  '  ' + i18n.i18n('Near line:') + ' "' + self.curline.strip('\r\n') + '"\n' +
                                  '  ' + msg)

  def line(self):
    if len(self._f_lines) == 0:
      self.curline = 'EOF'
      return None
    else:
      self.curline = self._f_lines.pop(0)
      return self.curline

  def unmangle(self, rtn_name):
    if rtn_name[0] == '$':
      return rtn_name[1:]
    else:
      return rtn_name

  def unmangle_opcode(self, opcode):
    return Compact_to_opcode.get(opcode, opcode)

  def load_program(self):
    code = lang.gbs_vm.GbsCompiledProgram(None)
    hdr = self.line()
    if hdr != 'GBO/1.0':
      self.fail('Expected header line "GBO/1.0"')
    while True:
      rtn = self.load_routine()
      if rtn is None:
        break
      code.routines[rtn.name] = rtn
    code.tree = FakeAST(filename=self._filename)
    return code

  def load_routine(self):
    decl = self.line()
    if decl is None:
      return None
    decl = decl.split(' ')

    prfn = self.unmangle_opcode(decl[0])
    name = self.unmangle(decl[1])
    args = decl[2:]
    tree = FakeAST(filename=self._filename)
    code = lang.gbs_vm.GbsCompiledCode(tree, prfn, name, args)
    while True:
      l = self.line()
      if l in ['end', Opcode_to_compact['end']]:
        break
      op = l.split(' ')
      op[0] = self.unmangle_opcode(op[0])
      if op[0] == 'pushConst':
        op[1] = self._parse_constant(op[1])
      elif op[0] in ['jump', 'jumpIfFalse']:
        op[1] = intern(op[1])
      elif op[0] == 'jumpIfNotIn':
        op = op[0], [self._parse_constant(x) for x in op[2:]], intern(op[1])
      elif op[0] == 'returnVars':
        op = op[0], int(op[1]), op[2:]
      elif op[0] == 'call':
        op[1] = self.unmangle(op[1])
        op[2] = int(op[2])
      elif op[0] == 'return':
        op[1] = int(op[1])
      elif op[0] == 'label':
        op[1] = intern(op[1])
      code.push(op)
    code.build_label_table()
    return code

  def _parse_constant(self, name):
    val = lang.gbs_builtins.parse_constant(name)
    if val is None:
      self.fail('Unknown constant %s' % (name,))
    return val

def dump(program, f, style='verbose'):
  w = GbsVmWriter(f, style=style)
  w.dump_program(program)

def load(f, filename='...'):
  r = GbsVmReader(f, filename=filename)
  return r.load_program()

