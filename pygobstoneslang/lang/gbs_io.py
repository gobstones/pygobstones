#
# Copyright (C) 2013 Pablo Barenbaum <foones@gmail.com>, Ary Pablo Batista <arypbatista@gmail.com>
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


""" Gosbtones Keycodes """

class GobstonesKeys(object):
    ARROW_UP = 1001
    ARROW_DOWN = 1002
    ARROW_RIGHT = 1003
    ARROW_LEFT = 1004
    CTRL_D = 4

    

""" Interactive API """

class InteractiveApi(object):
    """Provides a common interface for I/O"""
    def read(self):
        "Returns an integer representing a keycode"
        return GobstonesKeys.CTRL_D
    def show(self, board):
        pass
    def write(self, str):
        pass
    def read_line(self):
        "Returns a String of characters"
        pass



""" Cross-Platform API Adapter and Helper Classes"""

class KeyBuffer(object):
    def __init__(self, special_keys):
        self._buffer = []
        self._special_keys = special_keys
        self._buffer_size = self.max_combination_size(special_keys) +1
    def max_combination_size(self, special_keys):
        max_size = 0
        for special_key in special_keys:
            max_size = max(max_size, len(special_key.combination))
        return max_size
    def clear(self):
        self._buffer = []
    def add_key(self, key):
        self._buffer.append(key)
        if len(self._buffer) > self._buffer_size:
            self._buffer.pop(0)
    def matches_special_key(self):
        return not (self.get_special_key() is None)
    def get_special_key(self):
        for special_key in self._special_keys:
            if self.is_combination_in_buffer(special_key.combination):
                return special_key.gbs_value
    def is_combination_in_buffer(self, combination):
        for i in range(len(self._buffer)):
            if self._buffer[i] == combination[0] and self._buffer[i:i+len(combination)] == combination:
                return combination
    
class SpecialKey(object):
    def __init__(self, combination, gbs_value):
        self.combination = combination
        self.gbs_value = gbs_value
    
class CrossPlatformApiAdapter(InteractiveApi):
    def __init__(self, adapted_api):
        self.adapted_api = adapted_api
        self.buffer = KeyBuffer([
                                 # Windows special keys
                                 SpecialKey([224,72], GobstonesKeys.ARROW_UP),
                                 SpecialKey([224,80], GobstonesKeys.ARROW_DOWN),
                                 SpecialKey([224,77], GobstonesKeys.ARROW_RIGHT),
                                 SpecialKey([224,75], GobstonesKeys.ARROW_LEFT),
                                 #Linux special keys
                                 SpecialKey([27,91,65], GobstonesKeys.ARROW_UP),
                                 SpecialKey([27,91,66], GobstonesKeys.ARROW_DOWN),
                                 SpecialKey([27,91,67], GobstonesKeys.ARROW_RIGHT),
                                 SpecialKey([27,91,68], GobstonesKeys.ARROW_LEFT),
                                 ])
    def read(self):
        key = self.adapted_api.read();
        self.buffer.add_key(key)
        if self.buffer.matches_special_key():
            key = self.buffer.get_special_key()
            self.buffer.clear();
        return key
    def show(self, board):
        return self.adapted_api.show(board)
    def write(self, str):
        return self.adapted_api.write(str)
    def read_line(self):
        return self.adapted_api.read_line();    
