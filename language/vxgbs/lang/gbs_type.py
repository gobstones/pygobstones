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
  def is_subtype_of(self, type):
      return isinstance(type, self.__class__)
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
    
class GbsSymbolType(GbsBasicType):
  def __init__(self):
    self._name = i18n.i18n('Symbol')
    
class GbsStringType(GbsBasicType):
  def __init__(self):
    self._name = i18n.i18n('String')

class GbsBoardType(GbsBasicType):
    def __init__(self):
        self._name = i18n.i18n('Board')

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
    if self._indirection is None:
        return set_new([self])
    else:
        return self._indirection.freevars()

## Type Alias

class GbsTypeAlias(GbsType):
    def __init__(self, name=None, type=None):
        if isinstance(type, GbsTypeAlias):
            self.alias_of = type.alias_of
        else:
            self.alias_of = type
        self.name = name
    def __repr__(self):
        return self.name
    def instantiate(self, subst):
        return GbsTypeAlias(self.name, self.alias_of.instantiate(subst))
    def occurs(self, var):
        return self.alias_of.occurs(var)
    def freevars(self):
        return self.alias_of.freevars()

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
  def is_subtype_of(self, type):
      if isinstance(type, GbsTupleType) and len(self.subtypes()) >= len(type.subtypes()):
          for i, inner_type in zip(range(len(type.subtypes())),type.subtypes()):
              if not self.subtypes()[i].is_subtype_of(inner_type):
                  return False
          return True
      else:
          return False
  def instantiate(self, subst=None):
    return GbsTupleType([t.instantiate(subst) for t in self._types])
  def freevars(self):
    res = set_new([])
    for t in self._types:
      set_extend(res, t.freevars())
    return res

## Lists

class GbsListType(GbsType):
    def __init__(self, inner_type=None):
        if inner_type is None:
            self._inner_type = GbsTypeVar()
        else:
            self._inner_type = inner_type
    def __repr__(self):
        return 'List'
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
    def is_subtype_of(self, type):
        return isinstance(type, GbsListType) and self._inner_type.is_subtype_of(type._inner_type)
    kind_arity = 1

## Arrays

class GbsArrayType(GbsType):
    def __init__(self, inner_type=None):
        if inner_type is None:
            self._inner_type = GbsTypeVar()
        else:
            self._inner_type = inner_type
    def __repr__(self):
        return 'Array'
    def occurs(self, var):
        return self._inner_type.occurs(var)
    def subtypes(self):
        return [self._inner_type]
    def instantiate(self, subst=None):
        return GbsArrayType(self._inner_type.instantiate(subst))
    def freevars(self):
        res = set_new([])
        set_extend(res, self._inner_type.freevars())
        return res
    def is_subtype_of(self, type):
        return isinstance(type, GbsArrayType) and self._inner_type.is_subtype_of(type._inner_type)
    kind_arity = 1

# Records  

class GbsFieldType(GbsBasicType):
    def __init__(self):
        self._name = i18n.i18n('Field')

class GbsRecordType(GbsType):
    def __init__(self, name=None, fields={}):
        self.name = name
        self.fields = fields
    def instantiate(self, subst=None):
        inst_fields = {}
        for fn, ft in self.fields.items():
            inst_fields[fn] = ft.instantiate(subst)
        return GbsRecordType(inst_fields)
    def is_subtype_of(self, type):
        if isinstance(type, GbsRecordType):
            for field_name in type.fields.keys():
                if not field_name in self.fields.keys():
                    return False
                try:
                    unify(self.fields[field_name], type.fields[field_name])
                except UnificationFailedException as e:
                    return False
            return True
        else:
            return False
    def occurs(self, var):
        for ft in self.fields.values():
            if ft.occurs(var):
                return True
        return False
    def instantiate(self, subst=None):
        new_fields = {}
        for fname, ftype in self.fields.items():
            new_fields[fname] = ftype.instantiate(subst)
        return GbsRecordType(self.name, new_fields)
    def fields_repr(self):
        return ', '.join([fn + ':' + repr(ft) for fn, ft in self.fields.items()])
    def __repr__(self):
        if self.name is None:
            return 'Record(' + self.fields_repr() + ')'
        else:
            return self.name
    def freevars(self):
        res = set_new([])
        for ft in self.fields.values():
          set_extend(res, ft.freevars())
        return res

class GbsRecordTypeVar(GbsRecordType):
    def __init__(self, fields={}):
        super(GbsRecordTypeVar, self).__init__(None, fields)
    def point_to(self, other_record):
        for label in other_record.fields.keys():
            if label in self.fields.keys():
                unify(self.fields[label], other_record.fields[label])
            else:
                self.fields[label] = other_record.fields[label]
    def instantiate(self, subst=None):
        new_fields = {}
        for fname, ftype in self.fields.items():
            new_fields[fname] = ftype.instantiate(subst)
        return GbsRecordTypeVar(new_fields)

## Variant

class GbsVariantType(GbsType):
    def __init__(self, name=None, cases=None, is_case=None):
        if cases is None:
            cases = {}
        self.cases = cases
        self.name = name
        self.is_case = is_case
    def get_case(self):
        return self.cases[self.is_case]
    """[TODO] Better name """
    def get_case_match(self, record):
        for cname, cvalue in self.cases.items():
            try:
                unify(self.cases[cname], record)
                return cname
            except UnificationFailedException as e:
                pass
        return None
    def __repr__(self):
        if self.name is None:
            rep = 'Variant' + '(' + ' | '.join(self.cases.keys()) + ')'
        else:
            rep = self.name
        return rep 
    def is_subtype_of(self, type):
        if isinstance(type, GbsVariantType) and len(self.cases) <= len(type.cases):
            for cname in self.cases.keys():
                if not cname in type.cases.keys():
                    return False
                try:
                    unify(self.cases[cname], type.cases[cname])
                except UnificationFailedException as e:
                    return False
            return True
        else:
            return False
    def instantiate(self, subst={}):
        inst_cases = {}
        for cname, ctype in self.cases.items():
            inst_cases[cname] = ctype.instantiate(subst)
        return GbsVariantType(self.name, inst_cases, self.is_case)
    def occurs(self, var):
        for case_type in self.cases.values():
            if case_type.occurs(var):
                return True
        return False
    def freevars(self):
        res = set_new([])
        for ctype in self.cases.values():
          set_extend(res, ctype.freevars())
        return res
## EntryPoint

class GbsEntryPointType(GbsType):  
  def __repr__(self):
    return 'entrypoint'  
  def instantiate(self, subst=None):
    return GbsEntryPointType()

## Procedures and functions

class GbsCallableType(GbsType):
    pass

class GbsProcedureType(GbsCallableType):
  def __init__(self, params):
    self._params = params
  def __repr__(self):
    return 'procedure %s' % (repr(self._params),)
  def occurs(self, var):
    return self._params.occurs(var)
  def parameters(self):
    return self._params.representant()._types
  def paramtype(self):
    return self._params.representant()
  def instantiate(self, subst=None):
    return GbsProcedureType(self._params.instantiate(subst))
  def freevars(self):
    return self._params.freevars()

class GbsFunctionType(GbsCallableType):
  def __init__(self, params, res):
    self._params = params
    self._res = res
  def __repr__(self):
    return 'function %s return %s' % (repr(self._params), repr(self._res))
  def occurs(self, var):
    return self._params.occurs(var) or self._res.occurs(var)
  def parameters(self):
    return self._params.representant()._types
  def result(self):
    return self._res.representant()._types
  def paramtype(self):
    return self._params.representant()
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
      subst2[bound_var.representant()] = GbsTypeVar()
    return self._expr.instantiate(subst2)
  def parameters(self):
    return self.instantiate().parameters()
  def result(self):
    return self.instantiate().result()
  def freevars(self):
    res = self._params.freevars()
    set_remove(res, self._bound)
    return res

## Type Printer

class TypePrinter(object):
    def print_(self, type):
        varnames = dict([(repr(freevar), chr(charcode)) for freevar, charcode in zip(seq_reversed(type.freevars().keys()), range(ord('a'), ord('z')))
                         if freevar._indirection is None])
        type_repr = repr(type)
        for var_repr, var_name in varnames.items():
            type_repr = type_repr.replace(var_repr, var_name)
        return type_repr

print_type = TypePrinter().print_

## Type Parser

BasicTypes = {
  i18n.i18n('Color'): GbsColorType,
  i18n.i18n('Dir'): GbsDirType,
  i18n.i18n('Bool'): GbsBoolType,
  i18n.i18n('Int'): GbsIntType,
  i18n.i18n('List'): GbsListType,
  i18n.i18n('Array'): GbsArrayType,
  i18n.i18n('String'): GbsStringType,
  i18n.i18n('Board'): GbsBoardType
}

ComposedTypes = {
}

SpecialTypes = {
  i18n.i18n('Procedure'): GbsProcedureType,
  i18n.i18n('Function'): GbsFunctionType,
  i18n.i18n('EntryPoint'): GbsEntryPointType,
  i18n.i18n('Forall'): GbsForallType,    
}

class TypeParser:
  "Class to build a type expression from an abstract syntax tree."
  def __init__(self, context):
    self.typevars = {}
    self.context = self.only_types(context)
  def only_types(self, ctx):
      return dict([(k, v) for k, v in ctx.items() if isinstance(v, GbsType) and not v.__class__ in SpecialTypes.values()])
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
    if tree.children[0] == 'type':
      tok = tree.children[1]
      args = tree.children[2]
      if args is None:
        args = []
      else:
        args = [self.parse_atom(a) for a in args.children]
      if tok.value in BasicTypes:
          t = BasicTypes[tok.value]
          if t.kind_arity != len(args):
            msg = i18n.i18n('type "%s" expects %u parameters, but receives %u') % (
                      tok.value, t.kind_arity, len(args))
            area = common.position.ProgramAreaNear(tok)
            raise GbsTypeSyntaxException(msg, area)
          return t(*args)
      else:
          if tok.value in self.context.keys():
              return self.context[tok.value]
          else:
              """[TODO] Translate """
              msg = i18n.i18n('Undefined type "%s".') % (tok.value,)
              area = common.position.ProgramAreaNear(tok)
              raise GbsTypeSyntaxException(msg, area)
    elif tree.children[0] == 'typeVar':
      tok = tree.children[1]
      if tok.value in self.typevars:
        return self.typevars[tok.value]
      else:
        fresh = GbsTypeVar(tok.value)
        self.typevars[tok.value] = fresh
        return fresh

def parse_type_declaration(tree, global_context):
  decl = TypeParser(global_context).parse_declaration(tree)
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
    elif isinstance(x, GbsTypeAlias):
        try:
            unify(x.alias_of, y)
        except UnificationFailedException as exception:
            raise UnificationFailedException(x,y)
    elif isinstance(y, GbsTypeAlias):
        try:
            unify(x, y.alias_of)
        except UnificationFailedException as exception:
            raise UnificationFailedException(x,y)
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
    elif isinstance(x, GbsArrayType):
        if isinstance(y, GbsArrayType):
            unify(x._inner_type, y._inner_type)
        else:
            raise UnificationFailedException(x, y)
    elif isinstance(x, GbsRecordTypeVar):
        if y.occurs(x):
            raise UnificationOccursCheckException(x, y)
        elif isinstance(y, GbsRecordType):
            if not isinstance(y, GbsRecordTypeVar):
                for k in x.fields.keys():
                    if not k in y.fields.keys():
                        raise UnificationFailedException(x, y)
            x.point_to(y)
        elif isinstance(y, GbsVariantType):
            unify(x, y.cases[y.is_case])
        else:
            raise UnificationFailedException(x, y)
    elif isinstance(y, GbsRecordTypeVar):
        if x.occurs(y):
            raise UnificationOccursCheckException(x, y)
        elif isinstance(x, GbsRecordType):
            for k in y.fields.keys():
                if not k in x.fields.keys():
                    raise UnificationFailedException(x, y)
            y.point_to(x)
        elif isinstance(x, GbsVariantType):
            unify(x.cases[x.is_case], y)
        else:
            raise UnificationFailedException(x, y)
    elif isinstance(x, GbsRecordType):
        if isinstance(y, GbsRecordType):
            """[TODO] Improve """ 
            if (x.name is None or y.name is None) and x.is_subtype_of(y):
                pass
            elif x.name == y.name:
                pass
            else:
                raise UnificationFailedException(x, y)
        elif isinstance(y, GbsVariantType):
            if x.name is None:
                y.is_case = y.get_case_match(x)
                """[TODO] Check """
                if y.is_case is None:
                    raise UnificationFailedException(x, y)
            elif x.name in y.cases.keys():
                y.is_case = x.name
            else:
                raise UnificationFailedException(x, y)
        else:
            raise UnificationFailedException(x, y)
    elif isinstance(x, GbsVariantType):
        if isinstance(y, GbsVariantType): 
            if (x.name is None or y.name is None) and x.is_subtype_of(y):
                pass
            elif x.name == y.name:
                """[TODO] Improve """
                if x.is_case is None:
                    x.is_case = y.is_case
                else:
                    y.is_case = x.is_case
            else:
                raise UnificationFailedException(x, y)
        elif isinstance(y, GbsRecordType) and y.name in x.cases.keys():
            x.is_case = y.name
        else:
            raise UnificationFailedException(x, y)
    else:
      assert False

