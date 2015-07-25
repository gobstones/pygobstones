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

import ast
from parser.Token import Token

def unpack_definition(def_):
    return def_.children

def get_routine_names(defs):
    names = []
    for def_ in defs.children:
        if not is_type_def(def_) and not is_entrypoint_def(def_):
            names.append(def_.children[1].value)
    return names

def is_type_def(def_):
    return is_def_keyword(def_, 'typedef')

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

def recursive_find_all_nodes(node, satisfies):
  result = []
  if satisfies(node):
      result.append(node)
  for child in node.children:
      if isinstance(child, ast.ASTNode):
          result.extend(recursive_find_all_nodes(child, satisfies))
  return result

def recursive_replace_token(tree, search, replace, soft_mode=False):
  for node in tree.children:
    if isinstance(node, Token) and (node.value == search or soft_mode):
      node.value = node.value.replace(search, replace);
    else:
      if hasattr(node, 'children'):
        recursive_replace_token(node, search, replace)
  return tree

def is_node(label, node):
  if hasattr(node, 'children') and len(node.children) > 0:
    return node.children[0] == label
  return False

def type_defs(tree):
    return filter(is_type_def, tree.children)

def routine_defs(tree):
    return filter(lambda def_: not is_type_def(def_), tree.children)

def is_token(node):
    return isinstance(node, Token)

def ffalse(node):
    return False

def collect_nodes_with_stop(root, tree, satisfies, stop_search=ffalse):
    collected = []
    if isinstance(tree, ast.ASTNode) and (root == tree or not stop_search(tree)):
        if satisfies(tree):
            collected.append(tree)
        for child in tree.children:
            collected.extend(collect_nodes_with_stop(root, child, satisfies, stop_search))
    return collected

def collect_nodes(tree, satisfies):
    collected = []
    if isinstance(tree, ast.ASTNode):
        if satisfies(tree):
            collected.append(tree)
        for child in tree.children:
            collected.extend(collect_nodes(child, satisfies))
    return collected

def is_field_gen(node):
    if not len(node.children) > 0:
        return False
    if not (isinstance(node.children[0], str) and node.children[0] == 'funcCall'):
        return False
    return (isinstance(node.children[1], Token)
            and node.children[1].value == '_mk_field')

def collect_nodes_until_found(tree, satisfies):
    "Stop branch search if found"
    collected = []
    if isinstance(tree, ast.ASTNode):
        if satisfies(tree):
            collected.append(tree)
        else:
            for child in tree.children:
                collected.extend(collect_nodes_until_found(child, satisfies))
    return collected
