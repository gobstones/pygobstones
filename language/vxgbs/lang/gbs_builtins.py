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

"""Definition of Gobstones builtin functions, procedures and constants."""

import sys
import functools
import common.utils as utils
from lang.gbs_io import GobstonesKeys

explicit_builtins = True

from lang.gbs_type import (
    BasicTypes,
    GbsTypeVar,
    GbsStringType,
    GbsTupleType,
    GbsRecordTypeVar,
    GbsBoolType,
    GbsIntType,
    GbsColorType,
    GbsDirType,
    GbsSymbolType,
    GbsFieldType,
    GbsRecordType,
    GbsFunctionType,
    GbsProcedureType,
    GbsForallType,
    GbsListType,
    GbsArrayType,
    GbsBoardType,
)
from lang.gbs_constructs import (
    RenameConstruct,
    BuiltinConstant,
    BuiltinFunction,
    BuiltinProcedure,
)

import common.i18n as i18n
from common.utils import (
    DynamicException,
)

#### Definition of built-in functions and constants.

class GbsRuntimeException(DynamicException):
    """Base exception for Gobstones runtime errors."""

    def error_type(self):
        "Description of the exception type."
        return i18n.i18n('Runtime error')

class GbsRuntimeTypeException(GbsRuntimeException):
    """Exception for XGobstones runtime type errors."""
    
    def error_type(self):
        "Description of the exception type."
        return i18n.i18n('Runtime type error')

def is_defined(name):
    return name in get_builtins_by_name().keys()

def is_builtin_constant(name):
    return is_defined(name) and isinstance(get_builtins_by_name()[name], BuiltinConstant)

TYPEVAR_X = GbsTypeVar()
TYPEVAR_Y = GbsTypeVar()
TYPEVAR_Z = GbsTypeVar()

# a -> a
TYPE_AA = GbsForallType(
            [TYPEVAR_X],
            GbsFunctionType(
                GbsTupleType([TYPEVAR_X]),
                GbsTupleType([TYPEVAR_X])))

# a x a -> Bool
TYPE_AAB = GbsForallType(
                [TYPEVAR_X],
                GbsFunctionType(
                    GbsTupleType([TYPEVAR_X, TYPEVAR_X]),
                    GbsTupleType([GbsBoolType()])))

TYPE_SSS = GbsFunctionType(
            GbsTupleType([GbsStringType(), GbsStringType()]),
            GbsTupleType([GbsStringType()]))

# Int x Int -> Int
TYPE_III = GbsFunctionType(
            GbsTupleType([GbsIntType(), GbsIntType()]),
            GbsTupleType([GbsIntType()]))

# Bool x Bool -> Bool
TYPE_BBB = GbsFunctionType(
                GbsTupleType([GbsBoolType(), GbsBoolType()]),
                GbsTupleType([GbsBoolType()]))

# Bool -> Bool
TYPE_BB = GbsFunctionType(
                GbsTupleType([GbsBoolType()]),
                GbsTupleType([GbsBoolType()]))

def clone_value(value):
    if isinstance(value, GbsObject):        
        return value.clone()    
    elif isinstance(value, list):
        return [clone_value(val) for val in value]
    elif isinstance(value, dict):
        new_dict = {}
        for key, value in value.items():
            new_dict[key] = clone_value(value)
        return new_dict
    else:
        if (hasattr(value, 'clone')):
            return value.clone()
        else:
            return value

class GbsObjectRef(object):
    def __init__(self, getter, setter):
        self.get = getter
        self.set = setter

class GbsObject(object):
    def __init__(self, value, type, bindings = {}):
        self.value = value
        self.bindings = bindings
        self.type = type
        
    def full_type(self):
        return self.type
    
    def __repr__(self):
        return repr(self.value)
    
    def clone(self):
        new_value = clone_value(self.value)
            
        new_bindings = {}
        for key, value in self.bindings.items():
            new_bindings[key] = clone_value(value)
        
        return GbsObject(new_value, self.type, new_bindings)
    
    def __getattr__(self, name):
        return self.value.__getattribute__(name)
        
        

class GbsListBindings(object):
    def __init__(self, lstobj):
        self.lstobj = lstobj
        self.bindings = {}
        self.references = {
            i18n.i18n('head'): self.lstobj.first_ref,
            i18n.i18n('last'): self.lstobj.last_ref,
            i18n.i18n('current'): self.lstobj.current_ref,
            i18n.i18n('init'): self.lstobj.init_ref,
            i18n.i18n('tail'): self.lstobj.tail_ref,
        }        
        
    def __getitem__(self, key):
        if key in self.references.keys():
            return self.references[key]()
        else:
            return self.bindings[key]
        
    def __setitem__(self, key, value):
        if key in self.references.keys():
            self.references[key].set(value)
        else:
            self.bindings[key] = value
            
    def __iter__(self):
        return utils.imerge(self.bindings.keys(), self.getters.keys())
    
    def keys(self):
        return self.bindings.keys() + self.getters.keys()

class GbsListObject(GbsObject):
    # [TODO] Not-empty list operations...
    def __init__(self, value = []):        
        super(GbsListObject, self).__init__(value, poly_typeof(value), GbsListBindings(self))
        self.cursor = 0    
        
    def first_ref(self):
        def getter():
            return self.value[0]
        def setter(value):
            self.value[0] = value
        return GbsObjectRef(getter, setter)
    
    def last_ref(self):
        def getter():
            return self.value[-1]
        def setter(value):
            self.value[-1] = value
        return GbsObjectRef(getter, setter)   
        
    def current_ref(self):
        def getter():
            try:
                return self.value[self.cursor]
            except IndexError as e:
                msg = i18n.i18n('List cursor does not refers to a valid value.')
                raise GbsRuntimeException(msg, None)
        def setter(value):
            self.value[self.cursor] = value
        return GbsObjectRef(getter, setter)       
    
    def tail_ref(self):
        def getter():
            if len(self.value) > 1:
                return GbsListObject(self.value[1:])
            else:
                return GbsListObject()
        def setter(obj):
            lst = obj.value
            self.value = [self.value[0]] + lst        
        return GbsObjectRef(getter, setter)
    
    def init_ref(self):
        def getter():
            if len(self.value) > 1:
                return GbsListObject(self.value[:-1])
            else:
                return GbsListObject()
        def setter(obj):
            lst = obj.value
            self.value = lst + [self.value[-1]]
        
        return GbsObjectRef(getter, setter)
    
    def clone(self):
        obj = GbsListObject(clone_value(self.value))
        obj.cursor = self.cursor        
        return obj
        
class GbsFieldObject(GbsObject):
    pass

class GbsArrayObject(GbsObject):
    def clone(self):
        obj = super(GbsArrayObject, self).clone()
        return GbsArrayObject(obj.value, obj.type, obj.bindings)

class GbsRecordObject(GbsObject):
    
    def __init__(self, value, type, bindings = {}):
        if '::' in type:
            realtype, constructor = type.split("::")
        else:
            realtype    = type
            constructor = type 
        super(GbsRecordObject, self).__init__(value, realtype, bindings)
        self.constructor = constructor
        
    def __repr__(self):
        if len(self.value) != 0:
            return self.constructor + '(' + ', '.join([k + ' <- ' + repr(v) for k, v in self.value.items()]) + ')'
        else:
            return self.constructor
    def clone(self):
        obj = super(GbsRecordObject, self).clone()
        rec = GbsRecordObject(obj.value, obj.type, obj.bindings)
        rec.constructor = self.constructor
        return rec
    
    def full_type(self):
        if self.constructor == self.type:
            return self.type
        else:
            return self.type + "::" + self.constructor


def wrap_value(value):
    if isinstance(value, GbsObject):
        return value
    elif poly_typeof(value) == 'List':
        return GbsListObject(value)
    else:
        return GbsObject(value, poly_typeof(value))
    
def unwrap_value(obj):
    if (isinstance(obj, GbsFieldObject ) or 
        isinstance(obj, GbsRecordObject) or 
        isinstance(obj, GbsArrayObject )): #[TODO] Smelly fix
        return obj
    elif isinstance(obj, GbsObject):
        return obj.value
    elif isinstance(obj, GbsObjectRef):
        return obj.get()
    else:
        return obj
    
def unwrap_values(values):
    return [unwrap_value(v) for v in values]

def unwrap_args(f):
    def unwrapper(f, *args):
        unwrapped = []
        for a in args:
            if isinstance(a, GbsObject):
                unwrapped.append(a.value)
            else:
                unwrapped.append(a)
        return f(*unwrapped)
    return functools.partial(unwrapper, f)

def wrap_result(f, wrapper_f):
    def wrapper(f, *args):
        return wrapper_f(f(*args))
    return functools.partial(wrapper, f)

def list_op_adapter(f):
    return wrap_result(f, list_wrapper)

class GbsEnum(object):
    """Represents an enumerated type."""

    def __init__(self, i):
        self._ord = i

    def enum_type(self):
        """Subclasses should implement the method to return the name
        of the enumerated type."""
        raise Exception("Subclass responsibility")

    def enum_size(self):
        """Subclasses should implement the method to return the number
        of elements in the enumerated type."""
        raise Exception("Subclass responsibility")

    def next(self):
        """Returns the next element in the enumerated type. (Wrap around
        if the maximum is reached)."""
        return self.__class__((self._ord + 1) % self.enum_size())

    def prev(self):
        """Returns the previous element in the enumerated type. (Wrap around
        if the minimum is reached)."""
        return self.__class__((self._ord - 1) % self.enum_size())

    def opposite(self):
        """Returns the opposite element in the enumerated type.
        Currently only works for enums of an even number of elements,
        returning the opposite element if they were in a circle."""
        new_i = (self._ord + self.enum_size() / 2) % self.enum_size()
        return self.__class__(new_i)

    def ord(self):
        """Returns the ord of the instance in the enumerated type."""
        return self._ord

    def __eq__(self, other):
        return isinstance(other, GbsEnum) and \
               self.enum_type() == other.enum_type() and \
               self._ord == other.ord()

#### Directions

DIRECTION_NAMES = [
    i18n.i18n('North'),
    i18n.i18n('East'),
    i18n.i18n('South'),
    i18n.i18n('West'),
]

DIRECTION_DELTA = {
    0: (1, 0),
    1: (0, 1),
    2: (-1, 0),
    3: (0, -1),
}

GBS_ENUM_TYPES = ['Dir', 'Color']

class Direction(GbsEnum):
    "Represents a Gobstones direction."

    def enum_type(self):
        "Return the name of the enumerated type."
        return 'Dir'

    def enum_size(self):
        "Return the size of the enumerated type."
        return 4

    def delta(self):
        "Return the delta for this direction."
        return DIRECTION_DELTA[self.ord()]

    def __repr__(self):
        return DIRECTION_NAMES[self.ord()]

NORTH = Direction(0)
EAST  = Direction(1)
SOUTH = Direction(2)
WEST  = Direction(3)

#### Colors

COLOR_NAMES = [
    i18n.i18n('Color0'),
    i18n.i18n('Color1'),
    i18n.i18n('Color2'),
    i18n.i18n('Color3'),
]

class Color(GbsEnum):
    "Represents a Gobstones color."

    def enum_type(self):
        "Return the name of the enumerated type."
        return 'Color'

    def enum_size(self):
        "Return the size of the enumerated type."
        return 4

    def name(self):
        "Return the name of this color."
        return COLOR_NAMES[self.ord()]

    def __repr__(self):
        return self.name()

NUM_COLORS = 4
COLOR0 = Color(0)
COLOR1 = Color(1)
COLOR2 = Color(2)
COLOR3 = Color(3)

def isinteger(value):
    "Return True iff the given Python value is integral."
    if sys.version_info[0] < 3:
        return isinstance(value, int) or isinstance(value, long)
    else:
        return isinstance(value, int)

def isenum(value):
    "Return True iff x is instance of a Gobstones enumerated type."
    return isinstance(value, bool) or \
           isinstance(value, Color) or \
           isinstance(value, Direction)

def typecheck_vals(global_state, val1, val2):
    "Compare value types and raise exception if there is a mismatch."
    if (poly_typeof(val1) != poly_typeof(val2)):
        msg = global_state.backtrace(i18n.i18n('%s type was expected') % (poly_typeof(val2),))
        raise GbsRuntimeTypeException(msg, global_state.area())
    return val1

def poly_typeof(value):
    "Return the name of the type of the value."
    if isinstance(value, bool):
        return 'Bool'
    elif isinteger(value):
        return 'Int'
    elif isinstance(value, list):
        return 'List'
    elif isinstance(value, str) or isinstance(value, unicode):
        return 'String'
    elif isinstance(value, GbsObject):
        return value.type
    else:
        return value.enum_type()

def poly_range(first, last, second):
    "Generate a list between two given basic values. Types must match."
    if poly_typeof(first) == poly_typeof(last):
        if isinstance(first, list):
            assert False
        if poly_typeof(first) == poly_typeof(second):
            if poly_ord(first)[0] == poly_ord(second)[0]:
                return []
            else:
                increment = poly_ord(second)[0] - poly_ord(first)[0]
            assert increment != 0
        elif second == 'NoSecondElementForRange':
            increment = 1
        else:
            assert False
        
        def next_elem(elem):
            if increment >= 0:
                for i in range(increment):
                    elem = poly_next(elem)
            else:
                for i in range(increment*-1):
                    elem = poly_prev(elem)
            return elem
        
        def elem_reached(elem1, elem2):
            if increment >= 0:
                return poly_ord(elem1)[0] >= poly_ord(elem2)[0]
            else:
                return poly_ord(elem1)[0] <= poly_ord(elem2)[0]
        
        elements = []
        elem = first
        while not elem_reached(elem, last):
            elements.append(elem)
            elem = next_elem(elem)
            
        if poly_ord(elem) == poly_ord(last):
            elements.append(elem)

        return elements
    else:
        assert False

def atomic_operation(global_state, value, f):
    """Wrapper for functions that expects atomic values as parameters."""
    if poly_typeof(value) not in ['Dir', 'Int', 'Bool', 'Color']:
        msg = global_state.backtrace(i18n.i18n('%s was expected') % (i18n.i18n('atomic value'),))
        raise GbsRuntimeException(msg, global_state.area())
    else:
        return f(value)

def poly_next(value):
    "Return the next value of the same type as the one given."
    if isinstance(value, bool):
        return not value
    elif isinteger(value):
        return value + 1
    elif isinstance(value, list):
        assert False
    else:
        return value.next()

def poly_prev(value):
    "Return the previous value of the same type as the one given."
    if isinstance(value, bool):
        return not value
    elif isinteger(value):
        return value - 1
    elif isinstance(value, list):
        assert False
    else:
        return value.prev()

def poly_opposite(value):
    "Return the opposite value of the same type as the one given."
    if isinstance(value, bool):
        return not value
    elif isinteger(value):
        return -value
    elif isinstance(value, list):
        assert False
    else:
        return value.opposite()

def gbs_poly_opposite(global_state, value):
    """Gobstones builtin function for the opposite value. Works only
    for directions and integers; raises a GbsRuntimeException if that
    is not the case."""
    if poly_typeof(value) not in ['Dir', 'Int']:
        msg = i18n.i18n(
            'The argument to opposite should be a direction or an integer')
        raise GbsRuntimeException(msg, global_state.area())
    else:
        return poly_opposite(value)

def poly_ord(value):
    """Returns a list of integers representing the ord of the given
    Gobstones value."""
    if isinstance(value, bool):
        if not value:
            return [0]
        else:
            return [1]
    elif isinteger(value):
        return [value]
    elif isinstance(value, list):
        assert False
    else:
        return [value.ord()]


def poly_equal(global_state, value1, value2):
    """ Handles equality between lists and between records """
    value1, value2 = unwrap_value(value1), unwrap_value(value2)
    if poly_typeof(value1) == 'List':
        if len(value1) == len(value2):
            equals = True
            for i in range(len(value1)):
                equals = poly_equal(global_state, value1[i], value2[i]) and equals
            return equals
        else:
            return False
    elif isinstance(value1, GbsRecordObject):
        if poly_typeof(value1) != poly_typeof(value2):
            return False
        else:
            equals = True
            for k in value1.value.keys():
                equals = poly_equal(global_state, value1.value[k], value2.value[k]) and equals
            return equals
    else:
        return poly_cmp(global_state, value1, value2, lambda a, b: a == b)


def poly_cmp(global_state, value1, value2, relop):
    """Returns True iff the given relational operator holds for
    the Gobstones values."""
    value1, value2 = unwrap_value(value1), unwrap_value(value2)
    if poly_typeof(value1) != poly_typeof(value2):
        msg = i18n.i18n(
            'Relational operation between values of different types')
        raise GbsRuntimeException(msg, global_state.area())
        raise GbsRuntimeException(msg, global_state.area())
    elif poly_typeof(value1) == 'List':
        msg = i18n.i18n('Relational operation different from equalities between values of %s are not allowed') % ('list type',)
    elif isinstance(value1, GbsRecordObject):
        msg = i18n.i18n('Relational operation different from equalities between values of %s are not allowed') % ('record types',)
        raise GbsRuntimeException(msg, global_state.area())
    else:
        if poly_typeof(value1) == "String":
            return relop(value1.lower(), value2.lower())
        else:
            return relop(poly_ord(value1), poly_ord(value2))
        

def arith_add(_, x, y):
    "Add the numbers."
    return x + y

def arith_sub(_, x, y):
    "Subtract the numbers."
    return x - y

def arith_mul(_, x, y):
    "Multiply the numbers."
    return x * y

def arith_pow(global_state, x, y):
    "Return x power y. Check for negative exponents."
    if y < 0:
        msg = global_state.backtrace(i18n.i18n('Negative exponent'))
        raise GbsRuntimeException(msg, global_state.area())
    else:
        return x ** y

def arith_div(global_state, x, y):
    "Return x div y. Check for zero division."
    if y == 0:
        msg = global_state.backtrace(i18n.i18n('Division by zero'))
        raise GbsRuntimeException(msg, global_state.area())
    else:
        return x / y

def arith_mod(global_state, x, y):
    "Return x mod y. Check for zero division."
    if y == 0:
        msg = global_state.backtrace(i18n.i18n('Division by zero'))
        raise GbsRuntimeException(msg, global_state.area())
    else:
        return x % y

def arith_op(opr, global_state, *values):
    """Given an n-ary arithmetic operator, and n values, return
    the result, dynamically checking that the values are all of the
    right Int type. If that is not the case, raise a GbsRuntimeException."""
    for value in values:
        if poly_typeof(value) != 'Int':
            msg = i18n.i18n('Arithmetic operation over non-numeric values')
            raise GbsRuntimeException(msg, global_state.area())
    return opr(global_state, *values)

def logical_op(opr, global_state, *values):
    """Given an n-ary logical operator, and n values, return
    the result, dynamically checking that the values are all of the
    right Bool type. If that is not the case, raise a GbsRuntimeException."""
    for value in values:
        if poly_typeof(value) != 'Bool':
            msg = i18n.i18n('Logical operation over non-boolean values')
            raise GbsRuntimeException(msg, global_state.area())
    return opr(global_state, *values)

def logical_not(_, value):
    "Return the logical negation of the given value."
    return not value

def logical_and(_, value1, value2):
    "Return the logical conjunction of the values."
    return value1 and value2

def logical_or(_, value1, value2):
    "Return the logical disjunction of the values."
    return value1 or value2

#######################################
# Board operations
#######################################

def board_go_to_origin(global_state, board):
    "Set header position to (0,0)"
    board.value.go_to_origin()
    return board

def board_go_to_boundary(global_state, board, direction):    
    board.value.go_to_boundary(direction)
    return board

def board_clear(global_state, board):
    "Clear board."
    board.value.hard_clear_board()
    return board

def board_put_stone(global_state, board, color):
    """Put a stone in the board."""
    if poly_typeof(color) != 'Color':
        msg = i18n.i18n('The argument to PutStone should be a color')
        raise GbsRuntimeException(msg, global_state.area())
    board.value.put_stone(color)
    return board

def board_binary_operation(global_state, board, v2, f):
    if poly_typeof(board) != 'Board':        
        msg = i18n.i18n('The procedure call variable should be a board.')
        raise GbsRuntimeException(msg, global_state.area())
    return f(global_state, board, v2)

def board_unary_operation(global_state, board, f):
    if poly_typeof(board) != 'Board':
        msg = i18n.i18n('The procedure call variable should be a board.')
        raise GbsRuntimeException(msg, global_state.area())
    return f(global_state, board)

def board_take_stone(global_state, board, color):
    """Take a stone from the board."""
    if poly_typeof(color) != 'Color':
        msg = i18n.i18n('The argument to TakeStone should be a color')
        raise GbsRuntimeException(msg, global_state.area())
    if board.value.num_stones(color) > 0:
        board.value.take_stone(color)
    else:
        msg = global_state.backtrace(
            i18n.i18n('Cannot take stones of color %s') % (color,))
        raise GbsRuntimeException(msg, global_state.area())
    return board

def board_move(global_state, board, direction):
    """Move the head."""
    if poly_typeof(direction) != 'Dir':
        msg = i18n.i18n('The argument to Move should be a direction')
        raise GbsRuntimeException(msg, global_state.area())
    if board.value.can_move(direction):
        board.value.move(direction)
    else:
        msg = global_state.backtrace(
            i18n.i18n('Cannot move to %s') % (direction,))
        raise GbsRuntimeException(msg, global_state.area())
    return board

def board_num_stones(global_state, board, color):
    """Number of stones of the given color."""
    if poly_typeof(color) != 'Color':
        msg = i18n.i18n('The argument to numStones should be a color')
        raise GbsRuntimeException(msg, global_state.area())
    return board.num_stones(color)

def board_exist_stones(global_state, board, color):
    """Return True iff there are stones of the given color."""
    if poly_typeof(color) != 'Color':
        msg = i18n.i18n('The argument to existStones should be a color')
        raise GbsRuntimeException(msg, global_state.area())
    return board.exist_stones(color)

def board_can_move(global_state, board, direction):
    """Return True iff the head can move to the given direction."""
    if poly_typeof(direction) != 'Dir':
        msg = i18n.i18n('The argument to canMove should be a direction')
        raise GbsRuntimeException(msg, global_state.area())
    return board.can_move(direction)

def internal_read(global_state):
    return global_state.interpreter.interactive_api.read()

def internal_show(global_state, board):
    global_state.interpreter.interactive_api.show(board.value.clone())
    return board

def internal_freevars(global_state, board):
    global_state.interpreter.ar.free_bindings()
    return board

#### String

def str_concat(global_state, str1, str2):
    if poly_typeof(str1) == poly_typeof(str2) and poly_typeof(str1) == "String":
        return str1 + str2
    else:
        msg = global_state.backtrace(i18n.i18n('%s was expected') % (i18n.i18n('string type value'),))
        raise GbsRuntimeException(msg, global_state.area())

############### 
## References
###############

TYPE_GETREF = GbsForallType(
                    [TYPEVAR_X, TYPEVAR_Y, TYPEVAR_Z],
                    GbsFunctionType(
                        GbsTupleType([TYPEVAR_X, TYPEVAR_Y]),
                        GbsTupleType([TYPEVAR_Z])))
 
TYPE_GETREFVALUE = GbsForallType([TYPEVAR_X, TYPEVAR_Y],
                                 GbsFunctionType(
                                     GbsTupleType([TYPEVAR_X]),
                                     GbsTupleType([TYPEVAR_Y])))
 
TYPE_SETREFVALUE = GbsForallType(
                    [TYPEVAR_X, TYPEVAR_Y],
                    GbsFunctionType(
                        GbsTupleType([TYPEVAR_X, TYPEVAR_Y]),
                        GbsTupleType([])))

TYPE_CHECKPROJECTABLEVAR = GbsProcedureType(GbsTupleType([GbsSymbolType()]))

def check_projectable_var(global_state, varname):
    activation_rec = global_state.interpreter.ar
    routine = activation_rec.routine
    if activation_rec.is_immutable(varname):
        if varname in routine.params:
            is_a = i18n.i18n('"%s" is a parameter')
        else:
            is_a = i18n.i18n('"%s" is an index')
        msg = global_state.backtrace(". ".join([i18n.i18n('Cannot apply "." operator to "%s"'), 
                                      is_a]) % 
                                     (varname, varname))
        raise GbsRuntimeException(msg, global_state.area())

def get_ref_value(global_state, ref):
    if isinstance(ref, GbsObject) and not isinstance(ref.value, dict):
        return ref.value
    elif isinstance(ref, GbsObjectRef):
        obj = ref.get()
        if isinstance(obj, GbsObject):
            return obj.value
        else:
            return obj
    else:
        return ref

def dict_setter(dictionary, index):
    def set_dict(value):
        dictionary[index] = value
    return set_dict

def list_setter(lst, index):
    def set_list(value):
        lst[index] = value
    return set_list

def get_ref(global_state, from_, index):    
    if isinstance(from_, list):
        if isinstance(index, str):
            msg = global_state.backtrace(i18n.i18n('Cannot apply "." operator to "%s"') % (poly_typeof(from_),))
        else:
            msg = global_state.backtrace(i18n.i18n('"%s" is not indexable.') % (poly_typeof(from_),))
        raise GbsRuntimeException(msg, global_state.area())
        
    if isinstance(from_, GbsArrayObject):
        if index in range(0, len(from_.value)):
            content = from_.value
            return GbsObjectRef(lambda: content[index], 
                                list_setter(content, index))
        elif index in from_.bindings.keys():
            content = from_.bindings
            return GbsObjectRef(lambda: content[index], 
                                dict_setter(content, index))
        else:
            if isinstance(index, str):
                msg = global_state.backtrace(i18n.i18n('"%s" is not a valid field.') % (index,))
            else:
                msg = global_state.backtrace(i18n.i18n('"%s" is not indexable.') % (poly_typeof(from_),))
            raise GbsRuntimeException(msg, global_state.area())
        
    else:
        if index in from_.value.keys():
            dic = from_.value
        elif index in from_.bindings.keys():
            dic = from_.bindings
        else:
            msg = global_state.backtrace(i18n.i18n('"%s" is not a valid field.') % (index,))
            raise GbsRuntimeException(msg, global_state.area())
    
        return GbsObjectRef(lambda: dic[index], 
                            dict_setter(dic, index))
        
def assign_ref(global_state, ref, value):
    if isinstance(value, GbsObject):
        rvalue = value.clone()        
    else:
        rvalue = wrap_value(value)
        
    # [TODO] getter and setter for array position
    if isinstance(ref, GbsObject):
        ref.value = rvalue.value
        ref.type = rvalue.type
        ref.bindings = rvalue.bindings
    else:
        ref.set(rvalue)

BUILTINS_EXPLICIT_BOARD = [
    #### Procedures
    BuiltinFunction(
      i18n.i18n('_getRef'),
      TYPE_GETREF,
      get_ref
    ),  
    BuiltinFunction(
      i18n.i18n('_getRefValue'),
      TYPE_GETREFVALUE,
      get_ref_value
    ),  
    BuiltinFunction(
      i18n.i18n('_SetRefValue'),
      TYPE_SETREFVALUE,
      assign_ref
    ),
    BuiltinProcedure(
        i18n.i18n('_checkProjectableVar'),
        TYPE_CHECKPROJECTABLEVAR,
        check_projectable_var
    ),
                           
    BuiltinProcedure(
      i18n.i18n('_FreeVars'),
      GbsProcedureType(GbsTupleType([GbsBoardType()])),
      internal_freevars
    ),
                           
    BuiltinProcedure(
      i18n.i18n('_Show'),
      GbsProcedureType(GbsTupleType([GbsBoardType()])),
      internal_show
    ),
                                                      
    BuiltinProcedure(
        i18n.i18n('PutStone'),
        GbsProcedureType(GbsTupleType([GbsBoardType(), GbsColorType()])),
        lambda gs, board, color: board_binary_operation(gs, board, color, board_put_stone)
    ),

    BuiltinProcedure(
        i18n.i18n('TakeStone'),
        GbsProcedureType(GbsTupleType([GbsBoardType(), GbsColorType()])),
        lambda gs, board, color: board_binary_operation(gs, board, color, board_take_stone)
    ),

    BuiltinProcedure(
        i18n.i18n('Move'),
        GbsProcedureType(GbsTupleType([GbsBoardType(), GbsDirType()])),
        lambda gs, board, v: board_binary_operation(gs, board, v, board_move)
    ),
            
    BuiltinProcedure(
        i18n.i18n('GoToBoundary'),
        GbsProcedureType(GbsTupleType([GbsBoardType(), GbsDirType()])),
        lambda gs, board, v: board_binary_operation(gs, board, v, board_go_to_boundary)
    ),

    BuiltinProcedure(
        i18n.i18n('ClearBoard'),
        GbsProcedureType(GbsTupleType([GbsBoardType()])),
        lambda gs, board: board_unary_operation(gs, board, board_clear)
    ),

    #### Functions

    BuiltinFunction(
        i18n.i18n('numStones'),
        GbsFunctionType(
            GbsTupleType([GbsBoardType(), GbsColorType()]),
            GbsTupleType([GbsIntType()])),
        board_num_stones
    ),

    BuiltinFunction(
        i18n.i18n('existStones'),
        GbsFunctionType(
            GbsTupleType([GbsBoardType(), GbsColorType()]),
            GbsTupleType([GbsBoolType()])),
        board_exist_stones
    ),

    BuiltinFunction(
        i18n.i18n('canMove'),
        GbsFunctionType(
            GbsTupleType([GbsBoardType(), GbsDirType()]),
            GbsTupleType([GbsBoolType()])),
        board_can_move
    ),
]

def implicit_board_func(f):
    def ff(gs, *values):
        return f(gs, gs.board.clone(), *values)
    return ff

def implicit_board_proc(f):
    def ff(gs, *values): 
        f(gs, GbsObject(gs.board, 'Board'), *values)
    return ff

def disabled_references(global_state, *args):
    msg = i18n.i18n('Passing by reference is disabled when using implicit board.')
    raise GbsRuntimeException(msg, global_state.area())

BUILTINS_IMPLICIT_BOARD = [
    #### Procedures
    BuiltinFunction(
      i18n.i18n('_getRef'),
      TYPE_GETREF,
      disabled_references
    ),  
    BuiltinFunction(
      i18n.i18n('_getRefValue'),
      TYPE_GETREFVALUE,
      disabled_references
    ),  
    BuiltinFunction(
      i18n.i18n('_SetRefValue'),
      TYPE_SETREFVALUE,
      disabled_references
    ),
    BuiltinProcedure(
        i18n.i18n('_checkProjectableVar'),
        TYPE_CHECKPROJECTABLEVAR,
        disabled_references
    ),
    BuiltinProcedure(
      i18n.i18n('_FreeVars'),
      GbsProcedureType(GbsTupleType([])),
      implicit_board_proc(internal_freevars)
    ),
                           
    BuiltinProcedure(
      i18n.i18n('_Show'),
      GbsProcedureType(GbsTupleType([])),
      implicit_board_proc(internal_show)
    ),
                           
    BuiltinProcedure(
        i18n.i18n('PutStone'),
        GbsProcedureType(GbsTupleType([GbsColorType()])),
        implicit_board_proc(board_put_stone)
    ),

    BuiltinProcedure(
        i18n.i18n('TakeStone'),
        GbsProcedureType(GbsTupleType([GbsColorType()])),
        implicit_board_proc(board_take_stone)
    ),

    BuiltinProcedure(
        i18n.i18n('Move'),
        GbsProcedureType(GbsTupleType([GbsDirType()])),
        implicit_board_proc(board_move)
    ),
            
    BuiltinProcedure(
        i18n.i18n('GoToBoundary'),
        GbsProcedureType(GbsTupleType([GbsDirType()])),
        implicit_board_proc(board_go_to_boundary)
    ),

    BuiltinProcedure(
        i18n.i18n('ClearBoard'),
        GbsProcedureType(GbsTupleType([])),
        implicit_board_proc(board_clear)
    ),

    #### Functions

    BuiltinFunction(
        i18n.i18n('numStones'),
        GbsFunctionType(
            GbsTupleType([GbsColorType()]),
            GbsTupleType([GbsIntType()])),
        implicit_board_func(board_num_stones)
    ),

    BuiltinFunction(
        i18n.i18n('existStones'),
        GbsFunctionType(
            GbsTupleType([GbsColorType()]),
            GbsTupleType([GbsBoolType()])),
        implicit_board_func(board_exist_stones)
    ),

    BuiltinFunction(
        i18n.i18n('canMove'),
        GbsFunctionType(
            GbsTupleType([GbsDirType()]),
            GbsTupleType([GbsBoolType()])),
        implicit_board_func(board_can_move)
    ),
]

BUILTINS = [

    #### Internal operations
    
    BuiltinFunction(
      i18n.i18n('_read'),
      GbsFunctionType(GbsTupleType([]), GbsTupleType([GbsIntType()])),
      internal_read
    ),
            
    BuiltinFunction(
        i18n.i18n('minBool'),
        GbsFunctionType(
            GbsTupleType([]),
            GbsTupleType([GbsBoolType()])),
        lambda global_state: False
    ),

    BuiltinFunction(
        i18n.i18n('maxBool'),
        GbsFunctionType(
            GbsTupleType([]),
            GbsTupleType([GbsBoolType()])),
        lambda global_state: True
    ),

    BuiltinFunction(
        i18n.i18n('minDir'),
        GbsFunctionType(GbsTupleType([]), GbsTupleType([GbsDirType()])),
        lambda global_state: NORTH
    ),

    BuiltinFunction(
        i18n.i18n('maxDir'),
        GbsFunctionType(GbsTupleType([]), GbsTupleType([GbsDirType()])),
        lambda global_state: WEST
    ),

    BuiltinFunction(
        i18n.i18n('minColor'),
        GbsFunctionType(GbsTupleType([]), GbsTupleType([GbsColorType()])),
        lambda global_state: COLOR0
    ),

    BuiltinFunction(
        i18n.i18n('maxColor'),
        GbsFunctionType(GbsTupleType([]), GbsTupleType([GbsColorType()])),
        lambda global_state: COLOR3
    ),

    BuiltinFunction(
        i18n.i18n('next'),
        TYPE_AA,
        lambda global_state, x: atomic_operation(global_state, x, poly_next)
    ),
    BuiltinFunction(
        i18n.i18n('prev'),
        TYPE_AA,
        lambda global_state, x: atomic_operation(global_state, x, poly_prev) 
    ),
    BuiltinFunction(
        i18n.i18n('opposite'),
        TYPE_AA,
        gbs_poly_opposite
    ),

    ## Strings
    BuiltinFunction(
        i18n.i18n('concat'),
        TYPE_SSS,
        str_concat
    ),

    #### Operators

    ## Relational operators

    BuiltinFunction(
        i18n.i18n('=='),
        TYPE_AAB,
        poly_equal        
    ),

    BuiltinFunction(
        i18n.i18n('/='),
        TYPE_AAB,
        lambda global_state, x, y:
            not poly_equal(global_state, x, y)
    ),
    BuiltinFunction(
        i18n.i18n('<'),
        TYPE_AAB,
        lambda global_state, x, y:
            poly_cmp(global_state, x, y, lambda a, b: a < b)
    ),
    BuiltinFunction(
        i18n.i18n('<='),
        TYPE_AAB,
        lambda global_state, x, y:
            poly_cmp(global_state, x, y, lambda a, b: a <= b)
    ),
    BuiltinFunction(
        i18n.i18n('>='),
        TYPE_AAB,
        lambda global_state, x, y:
            poly_cmp(global_state, x, y, lambda a, b: a >= b)
    ),
    BuiltinFunction(
        i18n.i18n('>'),
        TYPE_AAB,
        lambda global_state, x, y:
            poly_cmp(global_state, x, y, lambda a, b: a > b)
    ),

    ## Logical operators
    ##
    ## NOTE: logical operators in Gobstones are not
    ##       short-circuiting

    BuiltinFunction(
        i18n.i18n('not'),
        TYPE_BB,
        lambda global_state, x:
            logical_op(logical_not, global_state, x)
    ),
    BuiltinFunction(
        i18n.i18n('&&'),
        TYPE_BBB,
        lambda global_state, x, y:
            logical_op(logical_and, global_state, x, y)
    ),
    BuiltinFunction(
        i18n.i18n('||'),
        TYPE_BBB,
        lambda global_state, x, y:
            logical_op(logical_or, global_state, x, y)
    ),

    # Arithmetic operators

    BuiltinFunction(
        i18n.i18n('+'),
        TYPE_III,
        lambda global_state, x, y:
            arith_op(arith_add, global_state, x, y)
    ),
    BuiltinFunction(
        i18n.i18n('-'),
        TYPE_III,
        lambda global_state, x, y:
            arith_op(arith_sub, global_state, x, y)
    ),
    BuiltinFunction(
        i18n.i18n('*'),
        TYPE_III,
        lambda global_state, x, y:
            arith_op(arith_mul, global_state, x, y)
    ),
    BuiltinFunction(
        i18n.i18n('^'),
        TYPE_III,
        lambda global_state, x, y:
            arith_op(arith_pow, global_state, x, y)
    ),
    BuiltinFunction(
        i18n.i18n('div'),
        TYPE_III,
        lambda global_state, x, y:
            arith_op(arith_div, global_state, x, y)
    ),
    BuiltinFunction(
        i18n.i18n('mod'),
        TYPE_III,
        lambda global_state, x, y:
            arith_op(arith_mod, global_state, x, y)
    ),
    BuiltinFunction(
        i18n.i18n('unary-'),
        TYPE_AA,
        gbs_poly_opposite
    ),
            
    #### Constants

    BuiltinConstant(i18n.i18n('True'), GbsBoolType(), True),
    BuiltinConstant(i18n.i18n('False'), GbsBoolType(), False),
    BuiltinConstant(i18n.i18n('North'), GbsDirType(), NORTH),
    BuiltinConstant(i18n.i18n('South'), GbsDirType(), SOUTH),
    BuiltinConstant(i18n.i18n('East'), GbsDirType(), EAST),
    BuiltinConstant(i18n.i18n('West'), GbsDirType(), WEST),
    BuiltinConstant(i18n.i18n('Color0'), GbsColorType(), COLOR0),
    BuiltinConstant(i18n.i18n('Color1'), GbsColorType(), COLOR1),
    BuiltinConstant(i18n.i18n('Color2'), GbsColorType(), COLOR2),
    BuiltinConstant(i18n.i18n('Color3'), GbsColorType(), COLOR3),
]

#### Key constants
class KeyConstantBuilder:
    def build_key_constant(self, keyname, value):
        return BuiltinConstant(keyname, GbsIntType(), value)
    
    def build_ascii_key_constants_in_range(self, prefix, min, max):
        keys = []
        for ascii_code in range(min, max + 1):
             keys.append(self.build_key_constant(prefix + '_' + str.upper(chr(ascii_code)), ascii_code))
        return keys     
    
    def build_ascii_key_constants(self):
        keys = []
        # Build C_0 .. C_9 key constants
        keys.extend(self.build_ascii_key_constants_in_range("K", 48, 57))
        # Build C_A .. C_Z key constants
        keys.extend(self.build_ascii_key_constants_in_range("K", 97, 122))
        # Build SHILF_A .. SHIFT_Z key constants
        keys.extend(self.build_ascii_key_constants_in_range("K_SHIFT", 65, 90))
        return keys
    
    def build_special_key_constants(self):
        return [
                self.build_key_constant(i18n.i18n("K_ARROW_LEFT"), GobstonesKeys.ARROW_LEFT),
                self.build_key_constant(i18n.i18n("K_ARROW_UP"), GobstonesKeys.ARROW_UP),
                self.build_key_constant(i18n.i18n("K_ARROW_RIGHT"), GobstonesKeys.ARROW_RIGHT),
                self.build_key_constant(i18n.i18n("K_ARROW_DOWN"), GobstonesKeys.ARROW_DOWN),
                self.build_key_constant('K_CTRL_D', 4),
                self.build_key_constant('K_ENTER', 13),
                self.build_key_constant('K_SPACE', 32),
                self.build_key_constant('K_DELETE', 46),
                self.build_key_constant('K_BACKSPACE', 8),
                self.build_key_constant('K_TAB', 9),
                self.build_key_constant('K_ESCAPE', 27),
                ]
    
    def build(self):
        keys = []
        keys.extend(self.build_ascii_key_constants())
        keys.extend(self.build_special_key_constants())
        return keys;
    
BUILTINS.extend(KeyConstantBuilder().build())

#### List functions

TYPE_NIL = GbsForallType(
                [TYPEVAR_X],
                GbsFunctionType(
                    GbsTupleType([]),
                    GbsTupleType([GbsListType(TYPEVAR_X)])))

TYPE_LIST_GEN = GbsForallType(
                [TYPEVAR_X],
                GbsFunctionType(
                    GbsTupleType([TYPEVAR_X]),
                    GbsTupleType([GbsListType(TYPEVAR_X)])))

TYPE_CONCAT = GbsForallType(
                [TYPEVAR_X, TYPEVAR_Y, TYPEVAR_Z],
                GbsFunctionType(
                    GbsTupleType([GbsListType(TYPEVAR_X), GbsListType(TYPEVAR_Y)]),
                    GbsTupleType([GbsListType(TYPEVAR_Z)])))

TYPE_RANGE = GbsForallType(
                [TYPEVAR_X],
                GbsFunctionType(
                    GbsTupleType([TYPEVAR_X, TYPEVAR_X, TYPEVAR_X]),
                    GbsTupleType([GbsListType(TYPEVAR_X)])))

TYPE_CONS = GbsForallType(
                [TYPEVAR_X],
                GbsFunctionType(
                    GbsTupleType([TYPEVAR_X, GbsListType(TYPEVAR_X)]),
                    GbsTupleType([GbsListType(TYPEVAR_X)])))

TYPE_SNOC = GbsForallType(
                [TYPEVAR_X],
                GbsFunctionType(
                    GbsTupleType([GbsListType(TYPEVAR_X), TYPEVAR_X]),
                    GbsTupleType([GbsListType(TYPEVAR_X)])))

TYPE_IS_EMPTY = GbsForallType(
                [TYPEVAR_X],
                GbsFunctionType(
                    GbsTupleType([GbsListType(TYPEVAR_X)]),
                    GbsTupleType([GbsBoolType()])))

TYPE_HEAD_LAST = GbsForallType(
                    [TYPEVAR_X],
                    GbsFunctionType(
                        GbsTupleType([GbsListType(TYPEVAR_X)]),
                        GbsTupleType([TYPEVAR_X])))

TYPE_TAIL_INIT = GbsForallType(
                    [TYPEVAR_X],
                    GbsFunctionType(
                        GbsTupleType([GbsListType(TYPEVAR_X)]),
                        GbsTupleType([GbsListType(TYPEVAR_X)])))

def list_inner_type_eq(lst1, lst2):
    return len(lst1) == 0 or len(lst2) == 0 or poly_typeof(lst1[0]) == poly_typeof(lst2[0])

def list_binary_operation(global_state, lst1, lst2, f):
    """Wrapper for binary list operations to ensure list types"""
    if poly_typeof(lst1) == poly_typeof(lst2) and poly_typeof(lst1) == 'List' and list_inner_type_eq(lst1, lst2):
        return f(lst1, lst2)
    else:
        if poly_typeof(lst1) != 'List':
            msg = global_state.backtrace(i18n.i18n('%s was expected') % (i18n.i18n('list type value'),))
            raise GbsRuntimeException(msg, global_state.area())
        else:
            msg = global_state.backtrace(i18n.i18n('Concatenation between lists with different inner type.'))
            raise GbsRuntimeException(msg, global_state.area())
    
def notempty_list_operation(global_state, lst, f):
    """Wrapper for list binary operations that require the list not to be
    empty (head, tail, init, last).
    """
    def inner_(global_state, lst):
        if len(lst) == 0:
            msg = global_state.backtrace(i18n.i18n('Empty list'))
            raise GbsRuntimeException(msg, global_state.area())
        else:
            return f(lst)
    return list_operation(global_state, lst, inner_)
    
def list_operation(global_state, lst, f):
    """Ensures list type"""
    if poly_typeof(lst) != 'List':
        msg = global_state.backtrace(i18n.i18n('%s was expected.') % (i18n.i18n('list type value'),))
        raise GbsRuntimeException(msg, global_state.area())
    else:
        return f(global_state, lst)

def list_isempty(global_state, lst):
    "Return the whether list is nil or not."
    return list_operation(global_state, lst, lambda global_state, x: len(x) == 0)

def list_head(global_state, lst):
    "Return the first element of the list."
    return notempty_list_operation(global_state, lst, lambda lst: lst[0])

def list_tail(global_state, lst):
    "Return the tail of the list."
    return notempty_list_operation(global_state, lst, lambda lst: lst[1:])

def list_concat(global_state, lst1, lst2):
    return list_binary_operation(global_state, lst1, lst2, lambda lst1, lst2: lst1 + lst2)

def list_last(global_state, lst):
    "Return the last element of the list."
    return notempty_list_operation(global_state, lst, lambda lst: lst[-1])

def list_init(global_state, lst):
    "Return the initial segment of the list."
    return notempty_list_operation(global_state, lst, lambda lst: lst[:-1])

def list_gen(global_state, value):
    return [wrap_value(value)]

def list_nil(global_state):
    return []

def list_range(global_state, x, y, z):
    return poly_range(x,y,z)

def list_wrapper(lst):
    return GbsListObject(lst)

def list_has_next(global_state, lst):
    return lst.cursor < len(lst.value) -1

def list_go_to_start(global_state, lst):
    lst.cursor = 0
    return lst
    
def list_next(global_state, lst):
    lst.cursor += 1
    return lst

def list_append(global_state, lst, element):
    lst.append(wrap_value(element))
    return lst

def list_add_first(global_state, lst, element):
    lst.insert(0, wrap_value(element))
    return lst

def list_drop_first(global_state, lst):
    def inner_impl(lst):
        if len(lst) > 1:
            return lst[1:]
        else:
            return []
    return notempty_list_operation(global_state, lst, inner_impl)

def list_drop_last(global_state, lst):
    def inner_impl(lst):
        if len(lst) > 1:
            return lst[:-1]
        else:
            return []
    return notempty_list_operation(global_state, lst, inner_impl)

TYPE_LB = GbsForallType(
            [TYPEVAR_X],
            GbsFunctionType(
                GbsTupleType([GbsListType(TYPEVAR_X)]),
                GbsTupleType([GbsBoolType()]),
            )
          )

LIST_BUILTINS = [
    BuiltinProcedure(
        i18n.i18n('AddFirst'),
        GbsForallType([TYPEVAR_X], GbsProcedureType(GbsTupleType([GbsListType(TYPEVAR_X), TYPEVAR_X]))),
        list_op_adapter(list_add_first)
    ),
    BuiltinProcedure(
        i18n.i18n('Append'),
        GbsForallType([TYPEVAR_X], GbsProcedureType(GbsTupleType([GbsListType(TYPEVAR_X), TYPEVAR_X]))),
        list_op_adapter(list_append)
    ),
    BuiltinProcedure(
        i18n.i18n('DropFirst'),
        GbsForallType([TYPEVAR_X], GbsProcedureType(GbsTupleType([GbsListType(TYPEVAR_X)]))),
        list_op_adapter(list_drop_first)
    ),
    BuiltinProcedure(
        i18n.i18n('DropLast'),
        GbsForallType([TYPEVAR_X], GbsProcedureType(GbsTupleType([GbsListType(TYPEVAR_X)]))),
        list_op_adapter(list_drop_last)
    ),
    BuiltinProcedure(
        i18n.i18n('GoToStart'),
        GbsForallType([TYPEVAR_X], GbsProcedureType(GbsTupleType([GbsListType(TYPEVAR_X)]))),
        list_go_to_start
    ),
    BuiltinProcedure(
        i18n.i18n('Next'),
        GbsForallType([TYPEVAR_X], GbsProcedureType(GbsTupleType([GbsListType(TYPEVAR_X)]))),
        list_next
    ),
    BuiltinFunction(
        i18n.i18n('hasNext'),
        TYPE_LB,
        list_has_next
    ),
    BuiltinFunction(
        i18n.i18n('[]'),
        TYPE_NIL,
        wrap_result(list_nil, list_wrapper)
    ),
    BuiltinFunction(
        i18n.i18n('[x]'),
        TYPE_LIST_GEN,
        wrap_result(list_gen, list_wrapper)
    ),
    BuiltinFunction(
        i18n.i18n('++'),
        TYPE_CONCAT,
        list_op_adapter(list_concat)
    ),
    BuiltinFunction(
        i18n.i18n('_range'),
        TYPE_RANGE,
        list_op_adapter(list_range)
    ),
#                 
# Uncomment to enable cons and snoc builtin functions
#
#    BuiltinFunction(
#        i18n.i18n('cons'),
#        TYPE_CONS,
#        lambda global_state, x, xs: [x] + xs
#    ),
#    BuiltinFunction(
#        i18n.i18n('snoc'),
#        TYPE_SNOC,
#        lambda global_state, xs, x: xs + [x]
#    ),
    BuiltinFunction(
        i18n.i18n('isEmpty'),
        TYPE_IS_EMPTY,
        list_isempty
    ),
    BuiltinFunction(
        i18n.i18n('head'),
        TYPE_HEAD_LAST,
        list_head
    ),
    BuiltinFunction(
        i18n.i18n('last'),
        TYPE_HEAD_LAST,
        list_last
    ),
    BuiltinFunction(
        i18n.i18n('tail'),
        TYPE_TAIL_INIT,
        list_op_adapter(list_tail)
    ),
    BuiltinFunction(
        i18n.i18n('init'),
        TYPE_TAIL_INIT,
        list_op_adapter(list_init)
    ),
]

##################
## Record builtins
###################

def mk_field(global_state, symbol, value):
    return GbsFieldObject((symbol, value), 'Field')

def mk_record(global_state, type, fields, bindings={}):
    try:
        _bindings = {}
        for k in bindings.keys():
            _bindings[k] = bindings[k].clone()        
        for field in fields:
            _bindings[field.value[0]] = wrap_value(field.value[1])
        return GbsRecordObject(_bindings, type, _bindings)
    except Exception as exception:
        "Just in case..."
        msg = global_state.backtrace(i18n.i18n('Error while building type %s') % (type,))
        raise GbsRuntimeException(msg, global_state.area())
    
def mk_record_from(global_state, type, fields, from_record):
    if from_record.type != type.split("::")[0] or from_record.constructor != type.split("::")[1]:
        if type.split("::")[0] == type.split("::")[1]:
            type = type.split("::")[0]
        msg = global_state.backtrace(i18n.i18n("Error while building type %s") % (type,) + ": " + i18n.i18n("the given value has type %s") % (from_record.full_type(),))
        raise GbsRuntimeException(msg, global_state.area())
    else:  
        return mk_record(global_state, type, fields, from_record.bindings)

def projection(global_state, record, field_name):
    if isinstance(record, GbsObject):
        record = record.value
    
    try:
        return unwrap_value(record[field_name])
    except Exception as exception:
        msg = global_state.backtrace(i18n.i18n('The record doesn\'t have a field named "%s"\n' +
                                               'The available field names for this record are: %s') 
                                     % (field_name, ', '.join(record.keys()),))
        raise GbsRuntimeException(msg, global_state.area())

def _extract_case(global_state, value):
    try:
        return value.constructor
    except Exception as exception:
        msg = global_state.backtrace(i18n.i18n('\'match\' expression can only be used with a Variant-type value.'))
        raise GbsRuntimeException(msg, global_state.area())


TYPE_GET_FIELD = GbsForallType(
                [TYPEVAR_Y],
                GbsFunctionType(
                    GbsTupleType([GbsRecordTypeVar(), GbsSymbolType()]),
                    GbsTupleType([TYPEVAR_Y])))

TYPE_GETTER_FUNC = GbsForallType([TYPEVAR_Y],
                                 GbsFunctionType(
                                     GbsTupleType([GbsRecordTypeVar()]),
                                     GbsTupleType([TYPEVAR_Y])))

TYPE_MKFIELD = GbsForallType(
                [TYPEVAR_X],
                GbsFunctionType(
                    GbsTupleType([GbsSymbolType(), TYPEVAR_X]),
                    GbsTupleType([GbsFieldType()])))

TYPE_CONSTRUCT = GbsForallType(
                [TYPEVAR_X],
                GbsFunctionType(GbsTupleType([TYPEVAR_X,
                                              GbsListType(GbsFieldType())]),
                                GbsTupleType([TYPEVAR_X])))

TYPE_CONSTRUCT_FROM = GbsForallType([TYPEVAR_X],
                        GbsFunctionType(GbsTupleType([TYPEVAR_X,
                                                      GbsListType(GbsFieldType()),
                                                      GbsRecordTypeVar()]),
                                        GbsTupleType([TYPEVAR_X])))

RECORD_BUILTINS = [
    BuiltinFunction(
        '_extract_case',
        GbsForallType([TYPEVAR_X, TYPEVAR_Y],
                      GbsFunctionType(GbsTupleType([TYPEVAR_X]),
                                      GbsTupleType([TYPEVAR_Y]))),
        _extract_case
    ),
    BuiltinFunction(
        i18n.i18n('_get_field'),
        TYPE_GET_FIELD,
        projection
    ),
    BuiltinFunction(
        i18n.i18n('_mk_field'),
        TYPE_MKFIELD,
        mk_field
    ),
    BuiltinFunction(
        i18n.i18n('_construct'),
        TYPE_CONSTRUCT,
        mk_record
    ),
    BuiltinFunction(
        i18n.i18n('_construct_from'),
        TYPE_CONSTRUCT_FROM,
        mk_record_from
    ),
]
BUILTINS += RECORD_BUILTINS





############### 
## Arrays
###############

TYPE_MKARRAY = GbsForallType(
                    [TYPEVAR_X],
                    GbsFunctionType(
                        GbsTupleType([GbsSymbolType(), GbsListType(GbsFieldType())]),
                        GbsTupleType([GbsArrayType(TYPEVAR_X)])))

def mk_array(global_state, type, fields):
    fields = unwrap_value(fields)
    field = fields[0]
    if len(fields) > 1:
        msg = global_state.backtrace(i18n.i18n('%s constructor expects %s field(s).') % (i18n.i18n('Array'), 1))
        raise GbsRuntimeTypeException(msg, global_state.area())
    elif field.value[0] != 'size':
        msg = global_state.backtrace(i18n.i18n('"%s" is not a valid field.') % ('size',))
        raise GbsRuntimeTypeException(msg, global_state.area())
    elif poly_typeof(field.value[1]) != 'Int':
        msg = global_state.backtrace(
            i18n.i18n('"%s" field has type %s, but type %s was expected.') % (
                        'size', 
                        poly_typeof(field.value[1]), 
                        i18n.i18n('Int'),))
        raise GbsRuntimeTypeException(msg, global_state.area())
    else:
        size = field.value[1]
        return GbsArrayObject([GbsObject(None, GbsTypeVar()) for i in range(size)], 'Array', {'size':size})

ARRAY_BUILTINS = [
    BuiltinFunction(
        i18n.i18n('_mkArray'),
        TYPE_MKARRAY,
        mk_array
    ),
]

BUILTINS += ARRAY_BUILTINS

######

def _is_int_constant(string):
    """Return True if the string represents an integer constant.
    - It can start with a minus sign.
    - It should have at least one digit.
    - The remaining elements should all be digits in 0..9."""
    digs = '0123456789'
    if len(string) == 0 or (string[0] == '-' and len(string) == 1):
        return False
    if string[0] not in '-' + digs:
        return False
    for char in string[1:]:
        if char not in digs:
            return False
    return True
        
BUILTINS += LIST_BUILTINS

#### OPTIMIZATIONS

def board_move_count(global_state, direction, count):
    """Move the head."""
    if poly_typeof(direction) != 'Dir' or poly_typeof(count) != 'Int':
        msg = i18n.i18n('The argument to Move should be a direction and a Integer')
        raise GbsRuntimeException(msg, global_state.area())
    if global_state.board.can_move(direction, count):
        global_state.board.move(direction, count)
    else:
        msg = global_state.backtrace(
            i18n.i18n('Cannot move to %s') % (direction,))
        raise GbsRuntimeException(msg, global_state.area())

def board_put_stone_count(global_state, color, count):
    """Put a stone in the board."""
    if poly_typeof(color) != 'Color' or poly_typeof(count) != 'Int':
        msg = i18n.i18n('The arguments should be a color and a integer')
        raise GbsRuntimeException(msg, global_state.area())
    board.value.put_stone(color, count)
    return board

def board_take_stone_count(global_state, color, count):
    """Take a stone from the board."""
    if poly_typeof(color) != 'Color' or poly_typeof(count) != 'Int':
        msg = i18n.i18n('The arguments should be a color and a integer')
        raise GbsRuntimeException(msg, global_state.area())
    if count > 0:
        if global_state.board.num_stones(color) >= count:
            global_state.board.take_stone(color, count)
        else:
            msg = global_state.backtrace(
                i18n.i18n('Cannot take stones of color %s') % (color,))
            raise GbsRuntimeException(msg, global_state.area())

OPTIMIZATIONS = [BuiltinProcedure("_"+i18n.i18n('PutStone') + 'N',
                 GbsProcedureType(GbsTupleType([GbsColorType(), GbsIntType()])),
                 board_put_stone_count),
                 BuiltinProcedure("_"+i18n.i18n('TakeStone') + 'N',
                 GbsProcedureType(GbsTupleType([GbsColorType(), GbsIntType()])),
                 board_take_stone_count),
                 BuiltinProcedure("_"+i18n.i18n('Move') + 'N',
                 GbsProcedureType(GbsTupleType([GbsDirType(), GbsIntType()])),
                 board_move_count)
                 ]

BUILTINS += OPTIMIZATIONS

####

COLORS_BY_INITIAL = {
    i18n.i18n('Color0')[0].lower(): COLOR0,
    i18n.i18n('Color1')[0].lower(): COLOR1,
    i18n.i18n('Color2')[0].lower(): COLOR2,
    i18n.i18n('Color3')[0].lower(): COLOR3,
}

def _color_name_to_index_dict():
    """Return a dictionary mapping color names to color index.
    Color names are accepted in various forms:
    - capitalized (Rojo)
    - lowercase (rojo)
    - upper initial (R)
    - lower initial (r)
    The index is the order of the color in the Color enumerated
    type."""
    dic = {}
    for coli in range(NUM_COLORS):
        name = Color(coli).name()
        dic[name] = coli
        dic[name.lower()] = coli
        dic[name[0]] = coli
        dic[name[0].lower()] = coli
        dic[coli] = coli
    return dic

COLOR_NAME_TO_INDEX_DICT = _color_name_to_index_dict()

#### Polymorphic builtins

BUILTINS_POLYMORPHIC = {
    i18n.i18n('next'): True,
    i18n.i18n('prev'): True,
    i18n.i18n('opposite'): True,
    i18n.i18n('unary-'): True,
}

def poly_encode_type(type_name):
    """Return an encoding of the given type name."""
    return type_name

def polyname(fname, types):
    """Given a function name and a list of types, return a
    "polymorphic function name", which corresponds to the concrete
    function name that is going to be called when applying the
    function to arguments of those types. For instance, when
    applying siguiente to an integer, the polyname might be
    something like "siguiente@Int"."""
    return fname + '@' + '@'.join([poly_encode_type(typ) for typ in types])

def polyname_name(name):
    """Given the polyname of a function, return the original
    function name."""
    return name.split('@')[0]

def polyname_types(name):
    """Given the polyname of a function, return the names of
    the types of its arguments."""
    return name.split('@')[1:]

def _poly_args(builtin):
    """Given a builtin function or procedure, successively
    yield all possible instantiations of the types of its
    parameters. For a monomorphic function, this yields a single
    list of parameter types. For a polymorphic function, the
    number of possible parameter types could grow exponentially
    on the number of parameters."""
    def gen(length):
        """Generate all possible lists of parameter types, of the
        given length."""
        if length == 0:
            yield []
        else:
            for param_types in gen(length - 1):
                for basic_type in BasicTypes.keys():
                    yield [basic_type] + param_types
    for param_types in gen(len(builtin.gbstype().parameters())):
        yield param_types

def _initialize_poly_builtins():
    """Add one builtin function/procedure for each polyname of
    every polymorphic builtin function/procedure."""
    for builtin in BUILTINS:
        if builtin.name() not in BUILTINS_POLYMORPHIC:
            continue
        for param_types in _poly_args(builtin):
            pname = polyname(builtin.name(), param_types)
            BUILTINS.append(RenameConstruct(pname, builtin))

_initialize_poly_builtins()


def _initialize_builtins_by_name(builtins):
    """Initialize the dictionary of builtins mapping builtin
    names to constructs."""
    dic = {}
    for builtin in builtins:
        dic[builtin.name()] = builtin
        
    return dic



##

def parse_constant(string):
    """Given a string that represents a Gobstones constant, return
    an object representing that value."""
    if _is_int_constant(string):
        return int(string)
    if string in get_builtins_by_name():
        return get_builtins_by_name()[string].primitive()
    else:
        return None


# Builtins getters

def get_builtins():
    if explicit_builtins:
        return BUILTINS + BUILTINS_EXPLICIT_BOARD
    else:
        return BUILTINS + BUILTINS_IMPLICIT_BOARD

BUILTINS_NAMES = []
def get_builtins_names():    
    if len(BUILTINS_NAMES) == 0:
        BUILTINS_NAMES.extend([b.name() for b in get_builtins()])
    return BUILTINS_NAMES
    
BUILTINS_BY_NAME = {}
def get_builtins_by_name():
    if len(BUILTINS_BY_NAME.keys()) == 0:
        BUILTINS_BY_NAME.update(_initialize_builtins_by_name(get_builtins()))
    return BUILTINS_BY_NAME
    
def get_correct_names():
    return get_builtins_names()