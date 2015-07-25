#
# Copyright (C) 2011-2015 Pablo Barenbaum <foones@gmail.com>,
#                         Ary Pablo Batista <abatista@gmail.com>
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

import pygobstoneslang.common.position as position
import pygobstoneslang.common.i18n as i18n

import pygobstoneslang.common.utils as utils

class Token(position.ProgramElement):
    "Represents a token (terminal symbol in the grammar)."

    def __init__(self, type_, value, pos_begin, pos_end):
        position.ProgramElement.__init__(self)
        self.type = type_
        self.value = value
        self.pos_begin = pos_begin
        self.pos_end = pos_end

    def type_description(cls, tok_type):
        """Return the human-readable description of a token type,
        for displaying errors."""
        return i18n.Token_type_descriptions.get(tok_type, '"' + tok_type + '"')
    type_description = classmethod(type_description)

    def __repr__(self):
        if self.type in ['EOF', 'BOF']:
            return Token.type_description(self.type)
        else:
            if len(self.value) > 0 and self.value[0] == '"':
                quoted = self.value
            else:
                quoted = '"' + self.value + '"'
            if self.type in i18n.Token_type_descriptions:
                return '%s %s' % (Token.type_description(self.type), quoted)
            else:
                return '%s' % (quoted,)

    def description(self):
        """Return the human-readable description of a token."""
        return repr(self)

    def has_children(self):
        """A token has no children."""
        return False

    def show_ast(self, indent=0, **_):
        """Display the Token as a leaf AST."""
        return '    ' * indent + self.value

    def negate(self):
        """Negate a token (should represent a numeric value)."""
        assert self.type == 'num'
        return Token(self.type, '-' + self.value, self.pos_begin, self.pos_end)
