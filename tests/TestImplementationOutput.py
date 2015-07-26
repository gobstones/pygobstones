# -*- coding: utf-8 -*-

import unittest
import sys
import os
from gui.views.boardPrint import parseBoard
sys.path.append(os.path.join(os.path.dirname(os.path.dirname(__file__)), "language","implementation"))

from language.implementation import GobstonesWorker
from language.implementation.lang.gbs_vm import NullInteractiveAPI
from language.implementation.common.tools import tools
sys.path.append('../gui/views/boardPrint/')


class TestImplementationOutput(unittest.TestCase):
    
    def setUp(self):
        self.gbs = TestProgramWorker(self.fail)
    
    def testGobstonesWorker(self):
        self.gbs.run("program { Poner(Verde) }", language="gobstones", initial_board_string="GBB/1.0\nsize 4 4\nhead 0 0\n%%\n")
        self.gbs.run("type Rec is record { field a } program { Poner(Verde); return(Rec(a<-2)) }", language="xgobstones", initial_board_string="GBB/1.0\nsize 4 4\nhead 0 0\n%%\n")
        
        
    def testFinalBoardParsing(self):
        result = self.gbs.run("program { Poner(Verde) }", initial_board_string="GBB/1.0\nsize 4 4\nhead 0 0\n%%\n")
        parseBoard.parseABoardString(result[0])

    def testFinalBoard(self):
        result = self.gbs.run("program { Poner(Verde) }", initial_board_string="GBB/1.0\nsize 4 4\nhead 0 0\n%%\n")
        board = parseBoard.parseABoardString(result[0])
        self.assertTrue(board.getCell(0,0).getStones("green"), "Board has one green stone in the cell (0,0)")
        
    def tearDown(self):
        pass


class TestProgramWorker(GobstonesWorker):
    
    def __init__(self, failure):
        self.failure = failure
        self.result = None

    def success(self, gbs_run):
        self.result = (tools.board_format.to_string(gbs_run.final_board), gbs_run.result)
        
    def prepare(self):
        self.api = NullInteractiveAPI()
        self.api.log = lambda msg:None
        
    def run(self, program_text, language="xgobstones", initial_board_string="", filename="", run_mode=GobstonesWorker.RunMode.FULL):
        self.prepare()
        self.result = None
        self.start(filename, program_text, initial_board_string, run_mode, language)
        
        return self.result
        
    
if __name__ == '__main__':
    unittest.main()