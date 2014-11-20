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

"""Definition of program constructs, used in the lint step.

A program construct is any kind of value that an
identifier might take, such as "user-defined function"
or "built-in constant".
"""

import common.i18n as i18n
import common.position

class ProgramConstruct(object):
    """Base class to represent Gobstones constructs, such as constants,
variables, functions and procedures.
"""

    def __init__(self, name):
        self._name = name

    def name(self):
        "Returns the name of this construct."
        return self._name

    def where(self):
        """Returns a string, describing the place where this construct is
defined.
"""
        return 'at unknown place'

    def area(self):
        """Returns a program area indicating the place where this construct is
defined.
"""
        return common.position.ProgramArea()

    def underlying_construct(self):
        "Returns the original construct (used for renames/aliases)."
        return self

class RenameConstruct(ProgramConstruct):
    "Represents a construct which is an alias for another one."

    def __init__(self, new_name, value):
        self._name = new_name
        self._value = value

    def underlying_construct(self):
        "Returns the original construct, for which this one is an alias."
        return self._value

## Construct kinds (callable and atomic)

class CallableConstruct(ProgramConstruct):
    "Represents a construct that can be called (function or procedure)."

    def kind(self):
        "Returns the kind of this construct."
        return 'callable'

    def num_params(self):
        "Returns the number of arguments of this construct."
        return len(self.params())

class EntryPointConstruct(ProgramConstruct):
    """Represents a construct that cannot be called (entrypoint)"""
    
    def kind(self):
        "Returns the kind of this construct."
        return 'entrypoint'

class AtomicConstruct(ProgramConstruct):
    """Represents an atomic construct, which is not a collection
and cannot be called.
"""

    def kind(self):
        "Returns the kind of this construct."
        return 'atomic'

## Construct types (procedure, function, constant and variable)

class ProgramEntryPoint(EntryPointConstruct):
    """Represents a Gobstones program block"""
    def type(self):
        "Returns the type of this construct."
        return 'program'
    
class InteractiveEntryPoint(EntryPointConstruct):
    """Represents a Gobstones interactive program block"""
    def type(self):
        "Returns the type of this construct."
        return 'interactive'

class Procedure(CallableConstruct):
    "Represents a Gobstones procedure."

    def type(self):
        "Returns the type of this construct."
        return 'procedure'

class Function(CallableConstruct):
    "Represents a Gobstones function."

    def type(self):
        "Returns the type of this construct."
        return 'function'

class Constant(AtomicConstruct):
    "Represents a Gobstones constant."

    def type(self):
        "Returns the type of this construct."
        return 'constant'

class Variable(AtomicConstruct):
    "Represents a Gobstones variable."

    def type(self):
        "Returns the type of this construct."
        return 'variable'
    
class Type(AtomicConstruct):
    "Represents a Gobstones Type"
    def type(self):
        "Returns the type of this construct"
        return 'type'

##

class Builtin(ProgramConstruct):
    "Represents a builtin construct, defined by the Gobstones runtime."

    def __init__(self, name, gbstype, primitive):
        ProgramConstruct.__init__(self, name)
        self._gbstype = gbstype
        self._primitive = primitive

    def gbstype(self):
        "Returns the Gobstones type of this construct."
        return self._gbstype

    def where(self):
        """Returns a string, describing the place where this construct is
defined.
"""
        return i18n.i18n('as a built-in')

    def is_builtin(self):
        """Returns True iff this construct is a builtin. (Builtin constructs
always return True).
"""
        return True

    def primitive(self):
        "Returns the denotated value of this construct."
        return self._primitive

class BuiltinType(Builtin, Type):
    def __init__(self, name, gbstype):
        super(BuiltinType, self).__init__(name, gbstype, gbstype)

class BuiltinCallable(Builtin):
    """Represents a callable builtin construct, a procedure or function
defined by the Gobstones runtime.
"""

    def __init__(self, name, gbstype, primitive):
        Builtin.__init__(self, name, gbstype, primitive)
        self._params = [repr(p).lower() for p in gbstype.parameters()]

    def params(self):
        """Return a list of parameter names for this builtin callable
construct. The names are taken from its types. E.g.: Poner(color).
"""
        return self._params
    
class BuiltinProcedure(BuiltinCallable, Procedure):
    "Represents a builtin procedure."
    pass

class BuiltinFunction(BuiltinCallable, Function):
    "Represents a builtin function."

    def __init__(self, name, gbstype, primitive):
        BuiltinCallable.__init__(self, name, gbstype, primitive)
        self._nretvals = len(gbstype.result())

    def num_retvals(self):
        "Returns the number of values that this function returns."
        return self._nretvals
    
class BuiltinFieldGetter(BuiltinFunction):
    def __init__(self, name, gbstype, primitive=None):
        super(BuiltinFieldGetter, self).__init__(name, gbstype, primitive)

class BuiltinConstant(Builtin, Constant):
    "Represents a builtin constant."
    pass

##

class UserConstruct(ProgramConstruct):
    "Represents a user-defined construct."

    def __init__(self, name, tree):
        ProgramConstruct.__init__(self, name)
        self._tree = tree

    def tree(self):
        """Returns the AST corresponding to this user-defined construct's
definition."""
        return self._tree

    def where(self):
        """Returns a string, describing the place where this construct is
defined.
"""
        return i18n.i18n('at %s') % (self._tree.pos_begin.file_row_col(),)

    def area(self):
        """Returns a program area indicating the place where this user-defined
construct is defined.
"""
        return common.position.ProgramAreaNear(self._tree)

    def is_builtin(self):
        """Returns True iff this construct is a builtin. (User defined
constructs always return False).
"""
        return False


class UserEntryPoint(UserConstruct):
    "Represents a user-defined entrypoint construct."
    def identifier(self):
        return self.tree().children[1]

class UserProgramEntryPoint(UserEntryPoint, ProgramEntryPoint):
    "Represents a user-defined program entrypoint."
    pass
    
class UserInteractiveEntryPoint(UserEntryPoint, ProgramEntryPoint):
    "Represents a user-defined interactive program entrypoint."
    pass


class UserCallable(UserConstruct):
    "Represents a user-defined callable construct."

    def params(self):
        """Return a list of parameter names for this user-defined callable
construct. The names are taken from the callable construct's source code.
"""
        return [p.value for p in self.tree().children[2].children]

    def identifier(self):
        return self.tree().children[1]

class UserProcedure(UserCallable, Procedure):
    "Represents a user-defined procedure."
    pass

class UserFunction(UserCallable, Function):
    "Represents a user-defined function."

    def num_retvals(self):
        """Returns the number of values that this user-defined function
returns.
"""
        body = self.tree().children[3]
        return_clause = body.children[-1]
        tup = return_clause.children[1]
        return len(tup.children)

class UserVariable(UserConstruct, Variable):
    "Represents a user-defined variable."
    def identifier(self):
        return self.tree()

class UserType(UserConstruct, Type):
    "Represents a user-defined type."
    def identifier(self):
        return self.tree().children[1]

class UserParameter(UserVariable):
    "Represents a parameter in a user-defined routine."

    def type(self):
        "Returns the type of this construct."
        return 'parameter'

class UserIndex(UserVariable):
    "Represents an index in a repeatWith, repeat or foreach."

    def type(self):
        "Returns the type of this construct."
        return 'index'

## Compiled constructs

class UserCompiledConstruct(ProgramConstruct):
    "Represents a compiled construct."

    def __init__(self, name):
        ProgramConstruct.__init__(self, name)

    def is_builtin(self):
        """Returns True iff this construct is a builtin. (Compiled
constructs always return False).
"""
        return False

class UserCompiledCallable(ProgramConstruct):
    "Represents a compiled callable construct."

    def __init__(self, name, params):
        ProgramConstruct.__init__(self, name)
        self._params = params

    def params(self):
        "Return the list of names of this compiled callable construct."
        return self._params

class UserCompiledProcedure(UserCompiledCallable, Procedure):
    "Represents a compiled callable procedure."
    pass

class UserCompiledFunction(UserCompiledCallable, Function):
    "Represents a compiled callable function."
    pass

class UserCompiledEntrypoint(UserCompiledConstruct, UserEntryPoint):
    "Represents a compiled entrypoint."
    pass