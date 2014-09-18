# -*- coding: utf-8 -*-

from board import *
import re


# String to Board
#----------------

def readAFileAndTransformToStringInterpreter(nameFile):
    '''Read a file and return a only string with /n'''
    return '/n'.join([line.strip() for line in open(nameFile)])


def transformInterpreterStringToUseInBoardViewer(lines):
    '''Given a string without the GBB/1.0 '''
    return lines.replace('GBB/1.0', '')


def parseABoardString(lines):
    ''' Return a Board created with the string. The string must respect
    the format of board'''
    string = transformInterpreterStringToUseInBoardViewer(lines)
    stringBoard = string.split('\n')
    board = Board(None, {}, None)
    for line in stringBoard:
        evaluate(line, board)

    return board


def evaluate(line, board):
    '''Given a line, process the first element of the list and return the
    portion of the list that not been processed'''
    first4ofLine = line[:4]
    if first4ofLine == "size":
        setSize(line, board)
    elif first4ofLine == "head":
        setHead(line, board)
    elif first4ofLine == "cell":
        setCells(line, board)
    else:
        pass


def setSize(line, board):
    toupleProcessXCoord = processQuantity(line[5:])
    toupleProcessYCoord = processQuantity(line[(6 + toupleProcessXCoord[0]):])
    board.setSize(toupleProcessXCoord[1], toupleProcessYCoord[1])
    return board


def setHead(line, board):
    toupleProcessXCoord = processQuantity(line[5:])
    toupleProcessYCoord = processQuantity(line[(6 + toupleProcessXCoord[0]):])
    board.setHead(toupleProcessXCoord[1], toupleProcessYCoord[1])
    return board


def setCells(line, board):
    toupleProcessXCoord = processQuantity(line[5:])
    toupleProcessYCoord = processQuantity(line[(6 + toupleProcessXCoord[0]):])
    position = (toupleProcessXCoord[1], toupleProcessYCoord[1])
    listStones = generateStones(line[(6 + toupleProcessXCoord[0] + 1
                                        + toupleProcessYCoord[0]):])
    cell = Cell(listStones[0], listStones[1], listStones[2], listStones[3])
    board.addCell(position, cell)
    return board


def generateStones(line):
    '''Given a line (without the string 'cell x y') return a list of stones
    quantities in orden '''
    blues = 0
    blacks = 0
    greens = 0
    reds = 0
    while len(line) > 5:
        if line[0] == 'A':
            processTouple = processQuantity(line[5:])
            blues = processTouple[1]
            line = line[6 + processTouple[0]:]

        elif line[0] == 'N':
            processTouple = processQuantity(line[6:])
            blacks = processTouple[1]
            line = line[7 + processTouple[0]:]
        elif line[0] == 'R':
            processTouple = processQuantity(line[5:])
            reds = processTouple[1]
            line = line[6 + processTouple[0]:]
        elif line[0] == 'V':
            processTouple = processQuantity(line[6:])
            greens = processTouple[1]
            line = line[7 + processTouple[0]:]
    return [blues, blacks, reds, greens]


def processQuantity(line):
    ''' Given a line, return a touple with (length, number) for the number
        in the string
        Precondition: The string must start with a number'''
    res = ''
    currentIndex = 0
    while (currentIndex < len(line)) and (not (line[currentIndex] == ' ')):
        if not (re.match('[0-9]', line[currentIndex]) is None):
            res = res + line[currentIndex]
        currentIndex = currentIndex + 1
    return (len(res), int(res))


def removeTextProcessedOfCell(line):
    '''Given a line that start with "cell ...." remove the text that has been
    processed and return the result'''
    line = line[1:]
    while (len(line) > 0) and (not line[0] == 'c') and (not line[0] == 'h'):
        line = line[1:]
    return line


# Board to String
#----------------

def boardToString(board):
    text = 'GBB/1.0\n'
    text = text + getSizeString(board) + getCellsStrings(board) + getHeadString(board)
    return text


def getSizeString(board):
    return 'size ' + str(board.size[0]) + ' ' + str(board.size[1]) + '\n'


def getHeadString(board):
    return 'head ' + str(board.head[0]) + ' ' + str(board.head[1]) + '\n'


def getCellsStrings(board):
    text = ''
    for pos in board.cells.keys():
        text = text + 'cell ' + str(pos[0]) + ' ' + str(pos[1]) + ' ' + getQuantities(board.cells[pos].stones)
    return text


def getQuantities(dict_colours):
    text = ''
    for c in ['blue', 'black', 'red', 'green']:
        if c == 'blue':
            text = text + 'Azul ' + str(dict_colours[c]) + ' '
        elif c == 'black':
            text = text + 'Negro ' + str(dict_colours[c]) + ' '
        elif c == 'red':
            text = text + 'Rojo ' + str(dict_colours[c]) + ' '
        elif c == 'green':
            text = text + 'Verde ' + str(dict_colours[c]) + '\n'
    return text