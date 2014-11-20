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
#---------------------------------------------------------------------
# Author: Ary Pablo Batista <arypbatista@gmail.com>
#---------------------------------------------------------------------

import lang.ast
import lang.bnf_parser

def unpack_definition(def_):
    return def_.children

def is_entrypoint_def(def_):
    return is_program_def(def_) or is_interactive_def(def_)

def is_program_def(def_):
    return is_def(def_) and is_def_keyword(def_, 'entrypoint') and get_def_name(def_).value == 'program'
                                                                   
def is_interactive_def(def_):
    return is_def(def_) and is_def_keyword(def_, 'entrypoint') and get_def_name(def_).value == 'interactive'

def is_def_keyword(def_, keyword):
    return get_def_keyword(def_) == keyword

def is_def(tree):
    return hasattr(tree, "children") and (len(tree.children) == 5) 

def get_def_keyword(def_):
    return def_.children[0]

def get_def_name(def_):
    return def_.children[1]

def set_def_name(def_, nameToken):
    def_.children[1] = nameToken
    
def set_def_token_name(def_, name):
    def_.children[1].value = name
    
def get_def_body(def_):
    return def_.children[3]

def set_def_body(def_, body):
    def_.children[3] = body

def get_def_params(def_):
    return def_.children[2].children

def get_def_type_decl(def_):
    return def_.children[4]

def find_def(defs, satisfies):
    "Searchs for a definition that satisfies some criteria (satisfies is a Function)"
    def_tree = None
    
    for def_ in defs.children:
        if satisfies(def_):
            def_tree = def_
            
    return def_tree

def recursive_find_node(tree, satisfies):
  for node in tree.children:
    if satisfies(node):
      return node
    else:
      if hasattr(node, 'children'):
        recursive_result = recursive_find_node(node, satisfies)
        if recursive_result != None:
          return recursive_result
  return None

def recursive_replace_token(tree, search, replace):
  for node in tree.children:
    if isinstance(node, lang.bnf_parser.Token) and node.value == search:
      node.value = replace;
    else:
      if hasattr(node, 'children'):
        recursive_replace_token(node, search, replace)
    
def is_node(label, node):
  if hasattr(node, 'children') and len(node.children) > 0: 
    return node.children[0] == label
  return False