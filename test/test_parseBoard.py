# -*- coding: utf-8 -*-

import unittest
import sys
sys.path.append('../gui/views/boardPrint/')
from parseBoard import *


class TestParseBoard(unittest.TestCase):

    ## Test of parseABoardString

    def test_parseABoardString_GivenAEmptyBoard_andSetTheSize(self):
        '''Given a "size 6 6head 4 2%%" should return a board whith size 6,6'''
        board = parseABoardString('size 6 6\nhead 4 2\n%%\n')
        self.assertEquals(board.getX(), 6)
        self.assertEquals(board.getY(), 6)
    
    def test_parseABoardString_GivenAEmptyBoard_andSetTheHead(self):
        '''Given a "size 6 6head 4 2%%" should return a board whith head 4,2'''
        board = parseABoardString('size 6 6\nhead 4 2\n%%\n')
        self.assertEquals(board.getHeadPosition(), (4, 2))

    def test_parseABoardString_GivenABoardWithCells_andSetTheCellsBlues(self):
        '''Given a "size 6 6cell 0 4 Azul 1 Negro 3 Verde 1head 4 2%%" should
        return a board with the cell that contains the quantity of this
        colors'''
        board = parseABoardString(
            'size 6 6\ncell 0 4 Azul 1 Negro 3 Verde 1\ncell 1 4 Azul 1 Negro 3 Verde 1\nhead 4 2\n%%\n')
        self.assertEquals(board.getCell(0, 4).getStones("blue"), 1)
        self.assertEquals(board.getCell(0, 4).getStones("black"), 3)
        self.assertEquals(board.getCell(0, 4).getStones("green"), 1)
        self.assertEquals(board.getCell(0, 4).getStones("red"), 0)

        self.assertEquals(board.getCell(1, 4).getStones("blue"), 1)
        self.assertEquals(board.getCell(1, 4).getStones("black"), 3)
        self.assertEquals(board.getCell(1, 4).getStones("green"), 1)
        self.assertEquals(board.getCell(1, 4).getStones("red"), 0)

        self.assertEquals(board.getHeadPosition(), (4, 2))

    def test_parseABoardString_GivenABoardWithCells_andSetTheCellsGreens(self):
        '''Given a "size 6 6cell 0 4 Azul 1 Negro 3 Verde 1head 4 2%%" should
        return a board with the cell that contains the quantity of this
        colors'''
        board = parseABoardString(
            'size 6 6\ncell 0 4 Azul 1 Negro 3 Verde 1\nhead 4 2\n%%\n')
        self.assertEquals(board.getCell(0, 4).getStones("green"), 1)

    def test_parseABoardString_GivenABoardWithCells_andSetTheCellsBlacks(self):
        '''Given a "size 6 6cell 0 4 Azul 1 Negro 3 Verde 1head 4 2%%" should
        return a board with the cell that contains the quantity of this
        colors'''
        board = parseABoardString(
            'size 6 6\ncell 0 4 Azul 1 Negro 3 Verde 1\nhead 4 2\n%%\n')
        self.assertEquals(board.getCell(0, 4).getStones("black"), 3)

    def test_parseABoardString_GivenABoardWithCells_andSetTheCellsReds(self):
        '''Given a "size 6 6cell 0 4 Azul 1 Negro 3 Verde 1head 4 2%%" should
        return a board with the cell that contains the quantity of this
        colors'''
        board = parseABoardString(
            'size 6 6\ncell 0 4 Azul 1 Negro 3 Verde 1\nhead 4 2\n%%\n')
        self.assertEquals(board.getCell(0, 4).getStones("red"), 0)

    def test_parseABoardString_GivenABoardWithoutCells_andNotSetTheCells(self):
        '''Given a "size 6 6head 4 2%%" should
        return a board with the cell that contains the quantity of this
        colors'''
        board = parseABoardString('size 6 6\nhead 4 2\n%%\n')
        self.assertEquals(board.cells, {})

    ## Tests of evaluate

    def test_evaluate_GivenSize_30_4_andSetTheSize(self):
        '''Given a string "size 30 4head 4 2%%" should set in the board
        the size 30,3'''
        board = Board(None, None, {})
        line = 'size 30 4\nhead 4 2\n%%\n\n'
        evaluate(line, board)
        self.assertEquals(board.getX(), 30)
        self.assertEquals(board.getY(), 4)

    def test_evaluate_GivenHead_10_2_andSetTheHead(self):
        '''Given a string "head 10 2%%" should set in the board the
        head 10,2'''
        board = Board(None, None, {})
        line = 'head 10 2\n%%\n'
        evaluate(line, board)
        self.assertEquals(board.getHeadPosition(), (10, 2))

    # Tests of generateStones

    def test_generateStones_GivenAzul5_andReturnAListWith_5_0_0_0(self):
        '''Given a line "Azul 5head 4 2%%" should return a list [5,0,0,0]'''
        result = generateStones('Azul 5')
        self.assertEquals(result, [5, 0, 0, 0])

    def test_generateStones_GivenAzul15_andReturnAListWith_15_0_0_0(self):
        '''Given a line "Azul 15head 4 2%%" should return a list [15,0,0,0]'''
        result = generateStones('Azul 15')
        self.assertEquals(result, [15, 0, 0, 0])

    def test_generateStones_GivenAzul999_andReturnAListWith_999_0_0_0(self):
        '''Given a line "Azul 999head 4 2%%" should return a list [999,0,0,0]'''
        result = generateStones('Azul 999')
        self.assertEquals(result, [999, 0, 0, 0])

    def test_generateStones_GivenNegro5_andReturnAListWith_0_5_0_0(self):
        '''Given a line "Negro 5head 4 2%%" should return a list [0,5,0,0]'''
        result = generateStones('Negro 5')
        self.assertEquals(result, [0, 5, 0, 0])

    def test_generateStones_GivenAzul15Negro20(self):
        '''Given a line "Azul 15 Negro 20head 4 2%%" should return a list
        [15,20,0,0]'''
        result = generateStones('Azul 15 Negro 20')
        self.assertEquals(result, [15, 20, 0, 0])

    def test_generateStones_GivenRojo30_andReturnAListWith_0_0_30_0(self):
        '''Given a line "Rojo 30head 4 2%%" should return a list [0,0,30,0]'''
        result = generateStones('Rojo 30')
        self.assertEquals(result, [0, 0, 30, 0])

    def test_generateStones_GivenAzul15Negro20Rojo500(self):
        '''Given a line "Azul 15 Negro 20 Rojo 500head 4 2%%" should return a
        list [15,20,500,0]'''
        result = generateStones('Azul 15 Negro 20 Rojo 500')
        self.assertEquals(result, [15, 20, 500, 0])

    def test_generateStones_GivenVerde20_andReturnAListWith_0_0_0_30(self):
        '''Given a line "Verde 20head 4 2%%" should returna list
        [0, 0, 0, 20]'''
        result = generateStones('Verde 20')
        self.assertEquals(result, [0, 0, 0, 20])

    def test_generateStones_GivenAzul20Negro30Rojo40Verde50(self):
            '''Given a line "Azul 20 Negro 30 Rojo 40 Verde 50head 4 2%%"
            should return a list [20, 30, 40, 50]'''
            res = generateStones('Azul 20 Negro 30 Rojo 40 Verde 50')
            self.assertEquals(res, [20, 30, 40, 50])

if __name__ == '__main__':
    unittest.main()
