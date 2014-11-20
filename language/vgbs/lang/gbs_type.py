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

#### Represent Gobstones types. Provides a type unification algorithm.

class GbsTypeSyntaxException(StaticException):
  def error_type(self):
    return i18n.i18n('Syntax error')

class GbsType(object):
  def representant(self):
    return self
  def show(self):
    return repr(self)
  kind_arity = 0

## Basic types

class GbsBasicType(GbsType):
  def __repr__(self):
    return self._name
  def occurs(self, var):
    return False
  def instantiate(self, subst=None):
    return self
  def freevars(self):
    return set_new()

class GbsColorType(GbsBasicType):
  def __init__(self):
    self._name = i18n.i18n('Color')

class GbsDirType(GbsBasicType):
  def __init__(self):
    self._name = i18n.i18n('Dir')

class GbsBoolType(GbsBasicType):
  def __init__(self):
    self._name = i18n.i18n('Bool')

class GbsIntType(GbsBasicType):
  def __init__(self):
    self._name = i18n.i18n('Int')

## Type variables

class GbsTypeVar(GbsType):
  def __init__(self, name=None):
    self._indirection = None
    self.name = name
  def representant(self):
    if self._indirection is None:
      return self 
    else:
      return self._indirection.representant()
  def point_to(self, other_type):
    self._indirection = other_type
  def __repr__(self):
    if self._indirection is None:
      name = self.name
      if not name: name = ''
      return '%s_%s' % (name, id(self),)
    else:
      return repr(self._indirection)
  def occurs(self, var):
    return id(self) == id(var)
  def instantiate(self, subst=None):
    if subst is None:
      subst = {}
    if self._indirection is None:
      return subst.get(self, self)
    else:
      return self._indirection.instantiate(subst)
  def freevars(self):
    return set_new([self])

## Tuples

class GbsTupleType(GbsType):
  def __init__(self, types):
    self._types = types
  def __repr__(self):
    return '(' + ', '.join([repr(t) for t in self._types]) + ')'
  def occurs(self, var):
    for t in self._types:
      if t.occurs(var):
        return True
    return False
  def subtypes(self):
    return self._types
  def instantiate(self, subst=None):
    return GbsTupleType([t.instantiate(subst) for t in self._types])
  def freevars(self):
    res = set_new([])
    for t in self._types:
      set_extend(res, t.freevars())
    return res

## Lists

class GbsListType(GbsType):
  def __init__(self, inner_type):
    self._inner_type = inner_type
  def __repr__(self):
    return 'List(' + repr(self._inner_type) + ')'
  def occurs(self, var):
    return self._inner_type.occurs(var)
  def subtypes(self):
    return [self._inner_type]
  def instantiate(self, subst=None):
    return GbsListType(self._inner_type.instantiate(subst))
  def freevars(self):
    res = set_new([])
    set_extend(res, self._inner_type.freevars())
    return res
  kind_arity = 1

## EntryPoint

class GbsEntryPointType(GbsType):  
  def __repr__(self):
    return 'entrypoint'  
  def instantiate(self, subst=None):
    return GbsEntryPointType()

## Procedures and functions

class GbsProcedureType(GbsType):
  def __init__(self, params):
    self._params = params
  def __repr__(self):
    return 'procedure %s' % (repr(self._params),)
  def occurs(self, var):
    return self._params.occurs(var)
  def parameters(self):
    return self._params._types
  def paramtype(self):
    return self._params
  def instantiate(self, subst=None):
    return GbsProcedureType(self._params.instantiate(subst))
  def freevars(self):
    return self._params.freevars()

class GbsFunctionType(GbsType):
  def __init__(self, params, res):
    self._params = params
    self._res = res
  def __repr__(self):
    return 'function %s return %s' % (repr(self._params), repr(self._res))
  def occurs(self, var):
    return self._params.occurs(var) or self._res.occurs(var)
  def parameters(self):
    return self._params._types
  def result(self):
    return self._res._types
  def paramtype(self):
    return self._params
  def restype(self):
    return self._res
  def instantiate(self, subst=None):
    return GbsFunctionType(self._params.instantiate(subst),
                           self._res.instantiate(subst))
  def freevars(self):
    res = set_new([])
    set_extend(res, self._params.freevars())
    set_extend(res, self._res.freevars())
    return res

class GbsForallType(GbsType):
  """Universal type of the form (forall v1,...,vn . t(v1,...,vn))
where v1...vn are type variables."""
  def __init__(self, bound, expr):
    self._bound = bound
    self._expr = expr
  def __repr__(self):
    return 'forall %s . %s' % (','.join([repr(x) for x in self._bound]), self._expr)
  def instantiate(self, subst=None):
    if subst is None:
      subst = {}
    subst2 = {}
    for var, val in subst.items():
      subst2[var] = val
    for bound_var in self._bound:
      subst2[bound_var] = GbsTypeVar()
    return self._expr.instantiate(subst2)
  def parameters(self):
    return self.instantiate().parameters()
  def result(self):
    return self.instantiate().result()
  def freevars(self):
    res = self._params.freevars()
    set_remove(res, self._bound)
    return res

##

BasicTypes = {
  i18n.i18n('Color'): GbsColorType,
  i18n.i18n('Dir'): GbsDirType,
  i18n.i18n('Bool'): GbsBoolType,
  i18n.i18n('Int'): GbsIntType,
  i18n.i18n('List'): GbsListType,
}

class TypeParser:
  "Class to build a type expression from an abstract syntax tree."
  def __init__(self):
    self.typevars = {}
  def parse_declaration(self, tree):
    if tree.children[0] == 'procType':
      return self.parse_procedure(tree)
    else:
      return self.parse_function(tree)
  def parse_procedure(self, tree):
    return GbsProcedureType(self.parse_tuple(tree.children[1]))
  def parse_function(self, tree):
    return GbsFunctionType(self.parse_tuple(tree.children[1]),
                           self.parse_tuple(tree.children[2]))
  def parse_tuple(self, tree):
    return GbsTupleType([self.parse_atom(t) for t in tree.children])
  def parse_atom(self, tree):
    if tree.children[0] == 'typeNameTypeCall':
      tok = tree.children[1]
      args = tree.children[2]
      if args is None:
        args = []
      else:
        args = [self.parse_atom(a) for a in args.children]
      if tok.value not in BasicTypes:
        msg = i18n.i18n('"%s" is not a basic type') % (tok.value,)
        area = common.position.ProgramAreaNear(tok)
        raise GbsTypeSyntaxException(msg, area)
      t = BasicTypes[tok.value]
      if t.kind_arity != len(args):
        msg = i18n.i18n('type "%s" expects %u parameters, but receives %u') % (
                  tok.value, t.kind_arity, len(args))
        area = common.position.ProgramAreaNear(tok)
        raise GbsTypeSyntaxException(msg, area)
      return t(*args)
    elif tree.children[0] == 'typeVar':
      tok = tree.children[1]
      if tok.value in self.typevars:
        return self.typevars[tok.value]
      else:
        fresh = GbsTypeVar(tok.value)
        self.typevars[tok.value] = fresh
        return fresh

def parse_type_declaration(tree):
  decl = TypeParser().parse_declaration(tree)
  return GbsForallType(decl.freevars().keys(), decl)

## Unification algorithm

class UnificationFailedException(Exception):
  def __init__(self, type1, type2):
    self.type1 = type1
    self.type2 = type2

class UnificationOccursCheckException(UnificationFailedException):
  pass

def unify(x, y):
  "Unify the two given types."
  x = x.representant()
  y = y.representant()
  if id(x) == id(y):
    return
  elif isinstance(x, GbsTypeVar):
    if y.occurs(x):
      raise UnificationOccursCheckException(x, y)
    else:
      x.point_to(y)
  elif isinstance(y, GbsTypeVar):
    if x.occurs(y):
      raise UnificationOccursCheckException(x, y)
    else:
      y.point_to(x)
  elif isinstance(x, GbsBasicType):
    if isinstance(y, GbsBasicType) and x._name == y._name:
      pass
    else:
      raise UnificationFailedException(x, y)
  elif isinstance(x, GbsTupleType):
    if isinstance(y, GbsTupleType) and len(x._types) == len(y._types):
      for xi, yi in zip(x._types, y._types):
        unify(xi, yi)
    else:
      raise UnificationFailedException(x, y)
  elif isinstance(x, GbsEntryPointType):
     if isinstance(x, GbsEntryPointType):
       pass
     else:
       raise UnificationFailedException(x, y)
  elif isinstance(x, GbsProcedureType):
    if isinstance(y, GbsProcedureType):
      unify(x._params, y._params)
    else:
      raise UnificationFailedException(x, y)
  elif isinstance(x, GbsFunctionType):
    if isinstance(y, GbsFunctionType):
      unify(x._params, y._params)
      unify(x._res, y._res)
    else:
      raise UnificationFailedException(x, y)
  elif isinstance(x, GbsListType):
    if isinstance(y, GbsListType):
      unify(x._inner_type, y._inner_type)
    else:
      raise UnificationFailedException(x, y)
  else:
    assert False

