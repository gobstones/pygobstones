#
# Copyright (C) 2011-2013 Pablo Barenbaum <foones@gmail.com>,
#                         Ary Pablo Batista <arypbatista@gmail.com>
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

import lang.gbs_def_helper as def_helper
from common.utils import StaticException
import lang.gbs_builtins
from lang.gbs_constructs import BuiltinProcedure
from lang.gbs_type import GbsProcedureType, GbsTypeVar, GbsTupleType
import inspect
import lang.ast
import lang.gbs_parser
import lang.bnf_parser
import lang.gbs_def_helper as def_helper
import copy
import common.i18n as i18n
def parse_part(code):
    program_code = "program { %s }" % (code,)
    program_tree = lang.gbs_parser.parse_string_try_prelude(program_code, '')
    return program_tree.children[2].children[0].children[3].children[0]
    
def map_two_trees_to_dict_list(tree1, tree2, f):
    result = [f(tree1, tree2)]
    for child_i in range(len(tree1.children)):
        if isinstance(tree1.children[child_i], lang.ast.ASTNode) and isinstance(tree2.children[child_i], lang.ast.ASTNode):
            result.extend(map_two_trees_to_dict_list(tree1.children[child_i], tree2.children[child_i], f))
    return result

def tree_matches(tree1, tree2):
    result = isinstance(tree1, tree2.__class__)
    if result:
        try:
            if isinstance(tree1, lang.ast.ASTNode) and tree1.children[0] != 'varName':    
                assert len(tree1.children) == len(tree2.children)
                for child_i in range(len(tree1.children)):                    
                    assert tree_matches(tree1.children[child_i], tree2.children[child_i])
            elif isinstance(tree1, str):
                assert tree1 == tree2
            elif isinstance(tree1, lang.bnf_parser.Token):
                assert tree1.value == tree2.value
                assert tree1.type == tree2.type
        except Exception as e:
            return False
    return result

class Optimization(object):
    def __init__(self, tree, optimized_tree):
        self.tree = tree
        self.optimized_tree = optimized_tree
    def matches(self, other_tree):
        return tree_matches(self.tree, other_tree)
    def optimize(self, other_tree):
        metavars = self.get_metavar_values_from(other_tree)
        optimized_tree = copy.deepcopy(self.optimized_tree)
        def is_metavar(node):
            return (isinstance(node, lang.ast.ASTNode) and isinstance(node.children[0], str)
                    and node.children[0] == 'varName')            
            
        nodes = def_helper.recursive_find_all_nodes(optimized_tree, is_metavar)
        
        for node in nodes:
            node.children = metavars[node.children[1].value].children
        
        other_tree.children = optimized_tree.children
        
    def get_metavar_values_from(self, other_tree):
        def get_metavar_value(node1, node2):
            if isinstance(node1, lang.ast.ASTNode) and isinstance(node1.children[0], str) and node1.children[0] == 'varName':
                return {node1.children[1].value:node2}
            else:
                return {}
        dict_list = map_two_trees_to_dict_list(self.tree, other_tree, get_metavar_value)
        result = {}
        for dic in dict_list:
            result.update(dic)
        return result

REPEAT_OPTIMIZATIONS = []
def repeat_primitives_optimization():
    if len(REPEAT_OPTIMIZATIONS) == 0:
        PRIMITIVES = [i18n.i18n('Move'),
                      i18n.i18n('PutStone'),
                      i18n.i18n('TakeStone')]
        REPEAT_OPTIMIZATIONS = [Optimization(parse_part("""
                                                        repeat i {
                                                            @PrimitiveOperation(x)
                                                        }
                                                        """.replace("@PrimitiveOperation", primitive)),
                                             def_helper.recursive_replace_token(parse_part("@OptimizedPrimitiveOperation(x, i)".replace("@OptimizedPrimitiveOperation", primitive + "N")),
                                                                                 primitive + "N",
                                                                                 "_" + primitive + "N")
                                             ) for primitive in PRIMITIVES]
    return REPEAT_OPTIMIZATIONS



class GbsOptimizerException(StaticException):
    pass

class GbsOptimizer(object):
    def optimize_program(self, tree):
        self.optimize_defs(tree.children[2])
    
    def optimize_defs(self, defs):
        for def_ in def_helper.routine_defs(defs):
            self.optimize_routine_def(def_)
            
    def optimize_routine_def(self, tree):
        prfn, name, params, body, typeDecl = tree.children
        self.optimize_routine_body(prfn, name, params, body)
        
    def optimize_routine_body(self, prfn, name, params, body):
        for cmd in body.children:
            self.optimize_command(cmd)
            

    def optimize_Skip(self, tree):
        pass
    
    
    def optimize_THROW_ERROR(self, tree):
        pass
    

    def optimize_assignVarName(self, tree):
        pass
    
    
    def optimize_assignVarTuple1(self, tree):
        pass
    
    
    def optimize_varDecl(self, tree):
        pass
    
    
    def optimize_if(self, tree):
        pass
    
    
    def optimize_case(self, tree):
        pass
    
    
    def optimize_while(self, tree):
        pass
    
    
    def optimize_repeat(self, tree):
        for optimization in repeat_primitives_optimization():
            if optimization.matches(tree):
               optimization.optimize(tree)
               return
    
    def optimize_repeatWith(self, tree):
        pass
    
    
    def optimize_foreach(self, tree):
        pass
    
    
    def optimize_procCall(self, tree):
        pass
    
        
    def optimize_block(self, tree):
       pass
    
                
    def optimize_return(self, tree):
        pass
    
    
    def optimize_command(self, tree):
        command = tree.children[0]
        dispatch = {
            'Skip': self.optimize_Skip,
            'THROW_ERROR': self.optimize_THROW_ERROR,
            'procCall': self.optimize_procCall,
            'assignVarName': self.optimize_assignVarName,
            'assignVarTuple1': self.optimize_assignVarTuple1,
            'varDecl': self.optimize_varDecl,
            'if': self.optimize_if,
            'case': self.optimize_case,
            'while': self.optimize_while,
            'repeat': self.optimize_repeat,
            'repeatWith': self.optimize_repeatWith,
            'foreach': self.optimize_foreach,
            'block': self.optimize_block,
            'return': self.optimize_return,
        }
        if command in dispatch:
            dispatch[command](tree)
        else:
            msg = i18n.i18n('Unknown command: %s') % (command,)
            area = common.position.ProgramAreaNear(tree)
            raise GbsOptimizerException(msg, area)
        
optimize = GbsOptimizer().optimize_program