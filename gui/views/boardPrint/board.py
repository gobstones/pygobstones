# -*- coding: utf-8 -*-

import parseBoard
import random


class Board():

    def __init__(self, size, cells, head):
        # size and head must be a touple x,y
        # cells must be a dictionary [touple x,y : cellObject]
        self.size = size
        self.cells = cells
        self.head = head

    def getX(self):
        return self.size[0]

    def getY(self):
        return self.size[1]

    def getHead(self):
        return self.head

    def getCell(self, x, y):
        return self.cells[(x, y)]

    def isEmptyCell(self, x, y):
        return not (x, y) in self.cells

    def getXCurrentCell(self):
        return self.head[0]

    def getYCurrentCell(self):
        return self.head[1]

    def setHead(self, x, y):
        self.head = (x, y)

    def setSize(self, x, y):
        self.size = (x, y)

    def getHeadPosition(self):
        return self.head

    def addCell(self, position, cell):
        self.cells[(int(position[0])), (int(position[1]))] = cell

    def isCurrentCell(self, coords):
        return self.head == coords

    def getStonesOfColorOnCell(self, color, coord):
        if self.isEmptyCell(coord[0], coord[1]):
            return 0
        else:
            return self.getCell(coord[0], coord[1]).getStones(color)

    def putStoneOfColorOnCell(self, color, coord):
        if self.isEmptyCell(coord[0], coord[1]):
            self.cells[coord] = Cell()
            self.cells[coord].putStone(color)
        else:
            self.cells[coord].putStone(color)

    def quitStoneOfColorOnCell(self, color, coord):
        if not self.isEmptyCell(coord[0], coord[1]):
            self.cells[coord].quitStone(color)

    def canMoveHeadToLeft(self):
        return self.head[0] > 0

    def canMoveHeadToRight(self):
        return self.head[0] < self.size[0] - 1

    def canMoveHeadToUp(self):
        return self.head[1] < self.size[1] - 1

    def canMoveHeadToDown(self):
        return self.head[1] > 0

    def moveHeadToLeft(self):
        if self.canMoveHeadToLeft():
            self.setHead(self.head[0] - 1, self.head[1])

    def moveHeadToRight(self):
        if self.canMoveHeadToRight():
            self.setHead(self.head[0] + 1, self.head[1])

    def moveHeadToUp(self):
        if self.canMoveHeadToUp():
            self.setHead(self.head[0], self.head[1] + 1)

    def moveHeadToDown(self):
        if self.canMoveHeadToDown():
            self.setHead(self.head[0], self.head[1] - 1)

    def getImageName(self, x, y):
        if self.size == (1, 1):
            return 'circle'
        elif self.topOnUniqueColumn(x, y):
            return 'up'
        elif self.downOnUniqueColumn(x, y):
            return 'down'
        elif self.leftOnUniqueRow(x, y):
            return 'left'
        elif self.rightOnUniqueRow(x, y):
            return 'right'
        elif self.isUpLeft(x, y):
            return 'up_left'
        elif self.isUpRight(x, y):
            return 'up_right'
        elif self.isDownLeft(x, y):
            return 'down_left'
        elif self.isDownRight(x, y):
            return 'down_right'
        else:
            return 'cell'

    def getRoundedBorderTranslucentImageName(self, x, y):
        if self.isUpLeft(x, y):
            return 'up_left_translucent'
        elif self.isUpRight(x, y):
            return 'up_right_translucent'
        elif self.isDownLeft(x, y):
            return 'down_left_translucent'
        elif self.isDownRight(x, y):
            return 'down_right_translucent'
        else:
            return 'cell_translucent'
        
    def topOnUniqueColumn(self, x, y):
        return self.getX() == 1 and y == self.getY() - 1 
        
    def downOnUniqueColumn(self, x, y):
        return self.getX() == 1 and y == 0
    
    def leftOnUniqueRow(self, x, y):
        return self.getY() == 1 and x == 0
    
    def rightOnUniqueRow(self, x, y):
        return self.getY() == 1 and x == self.getX() - 1
    
    def isUpLeft(self, x, y):
        return x == 0 and y == self.getY() - 1

    def isUpRight(self, x, y):
        return x == self.getX() - 1 and y == self.getY() - 1
    
    def isDownLeft(self, x, y):
        return x == 0 and y == 0 
    
    def isDownRight(self, x, y):
        return x == self.getX() - 1 and y == 0

class Cell():

    def __init__(self, blues=0, blacks=0, reds=0, greens=0):
        self.stones = {"blue": blues, "black": blacks, "red": reds,
                "green": greens}

    def getStones(self, color):
        return self.stones[color]

    def getAllStones(self):
        return (str(self.stones['blue']),
                str(self.stones['black']),
                str(self.stones['red']),
                str(self.stones['green']),
                )

    def putStone(self, color):
        self.stones[color] += 1

    def quitStone(self, color):
        self.stones[color] -= 1


class InitialBoardGenerator():

    def __init__(self):
        self.board = parseBoard.parseABoardString("GBB/1.0\nsize 8 8\nhead 0 0\n%%\n")
        self.set_nothing_options()
        self.options = [0, 0, 0] # [balls,size,head]

    def set_nothing_options(self):
        self.sizeBoardFunction = self.nothingSize
        self.headPositionFunction = self.nothingHead
        self.ballsFunction = self.nothingBalls

    def getInitialBoard(self):
        self.sizeBoardFunction(self.board)
        self.headPositionFunction(self.board)
        self.ballsFunction(self.board)
        return parseBoard.boardToString(self.board)

    def getStringBoard(self):
        return parseBoard.boardToString(self.board)

    def setInitialBoard(self, boardString):
        self.board = parseBoard.parseABoardString(boardString)

    def nothingBalls(self, board):
        self.options[0] = 0

    def nothingHead(self, board):
        self.options[2] = 0

    def nothingSize(self, board):
        self.options[1] = 0

    def randomCellsBoard(self, board):
        cells = {}
        for x in range(board.getX()):
            for y in range(board.getY()):
                if(random.randint(0,1) == 1):
                    blue = random.randint(0, 30)
                else:
                    blue = 0
                if(random.randint(0, 1) == 1):
                    black = random.randint(0, 30)
                else:
                    black = 0
                if(random.randint(0, 1) == 1):
                    red = random.randint(0, 30)
                else:
                    red = 0
                if(random.randint(0, 1) == 1):
                    green = random.randint(0, 30)
                else:
                    green = 0
                cells[(x, y)] = Cell(blue, black, red, green)
        self.options[0] = 1
        board.cells = cells

    def randomHeadBoard(self, board):
        maxX = board.getX()
        maxY = board.getY()
        if (maxX < 2):
            x = 0
        else:
            x = random.randint(0, maxX - 1)

        if (maxY < 2):
            y = 0
        else:
            y = random.randint(0, maxY - 1)
        board.setHead(x, y)
        self.options[2] = 2

    def randomSizeBoard(self, board):
        x = random.randint(1, 20)
        y = random.randint(1, 20)
        self.options[1] = 2
        board.setSize(x, y)

    def emptyCellsBoard(self, board):
        cells = {}
        for x in range(board.getX()):
            for y in range(board.getY()):
                cells[(x, y)] = Cell(0, 0, 0, 0)
        self.options[0] = 2
        board.cells = cells

    def setSize(self, x, y):
        self.board.setSize(x, y)
        self.options[1] = 1

    def setHead(self, x, y):
        self.board.setHead(x, y)
        self.options[2] = 1
