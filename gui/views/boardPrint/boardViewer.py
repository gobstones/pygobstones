from PyQt4 import QtGui
from PyQt4 import QtCore
from board import *
import sys
import os
import resources
from parseXML import ParseXML
import gui
from gui.errorWindow import *
from xml.etree.ElementTree import ParseError
from commons.utils import root_path, clothing_for_file_exists, clothing_dir_for_file

class BoardViewer(QtGui.QWidget):

    def __init__(self, mainW, board, clothing):
        super(BoardViewer, self).__init__()
        self.setMinimumSize(320, 320)
        self.lastBoard = None
        self.board = board
        self.lastClothing = None
        self.clothing = clothing
        self.mainW = mainW
        self.show()
        self.lastDimensions = (0,0)
        self.surface = None

    def getBoard(self):
        return self.board

    def setParent(self, parent):
        self.parent = parent

    def is_board_error(self):
        return False

    def createPainter(self):
        if self.clothing == "Gobstones.xml":
            return GobstonesStandard()
        elif "PixelBoard.xml" in self.clothing:
            return GobstonesPixelBoard()
        else:
            return GobstonesClothing(self.clothing)

    def getClothing(self):
        return self.clothing

    def setClothing(self, clothing):
        self.clothing = clothing

    def dimensionsChanged(self):
        return self.lastDimensions != (self.parent.width(), self.parent.height())
            
    def clothingChanged(self):
        return id(self.lastClothing) != id(self.clothing)
    
    def boardChanged(self):
        return id(self.lastBoard) != id(self.board)
    
    def contentChanged(self):
        return self.clothingChanged() or self.dimensionsChanged() or self.boardChanged()

    def updateState(self):
        self.lastDimensions = (self.parent.width(), self.parent.height())
        self.lastClothing = self.clothing
        self.lastBoard = self.board

    def paintEvent(self, event):
        if self.contentChanged():
            self.surface = QtGui.QPixmap(self.parent.width(), self.parent.height()) 
            self.updateState()
            
            width = self.parent.width()
            height = self.parent.height() - self.parent.tabBar().height()
            self.size().setWidth(width)
            self.size().setHeight(height)
            
            x = self.board.size[0]
            y = self.board.size[1]
            
            if (x > y):
                sideX = width / (x + 2)
                sideY = height / (y + 2)
                
                sizeHeight = sideX * (y + 2)
                sizeWidth = sideY * (x + 2)
                
                if (sizeHeight < height):
                    self.newSide = sideX
                else:
                    self.newSide = sideY
            else:
                side = min(width, height)        
                self.newSide = side / (max(x, y) + 2)
            
            self.offset = (width - ((self.board.getX() + 2) * self.newSide)) / 2
            
            try:
                self.painter = self.createPainter()
                painter = QtGui.QPainter()
                painter.begin(self.surface)
                painter.fillRect(QtCore.QRect(0,0, self.parent.width(), self.parent.height()), QtGui.QColor(255, 255, 255))
                painter.setRenderHint(QtGui.QPainter.Antialiasing)
                pen = QtGui.QPen(QtGui.QColor(200, 50, 50))
                pen.setWidth(1)
                painter.setPen(pen)
                y0 = self.newSide * self.board.getY() + self.newSide
                for y in range(self.board.getY()):
                    x0 = self.offset
                    y0 = y0 - self.newSide
                    for x in range(self.board.getX()):
                        pen = QtGui.QPen(QtGui.QColor(200, 50, 50))
                        pen.setWidth(1)
                        painter.setPen(pen)
                        painter.setBrush(QtGui.QColor(255, 255, 255))
                        x0 = x0 + self.newSide
                        rect = QtCore.QRect(x0, y0, self.newSide, self.newSide)
                        '''
                        painter.drawRect(rect)
                        '''
                        
                        imgName = self.board.getImageName(x, y)
                        img = QtGui.QImage(':/' + imgName + '.png')
                        painter.drawImage(rect, img)
                        
                        if(not self.board.isEmptyCell(x, y)):
                            self.painter.draw(painter, rect, self.board.getCell(x, y))
                        else:
                            self.painter.draw(painter, rect, Cell(0, 0, 0, 0))
    
                        self.roundCellBordersOnClothing(x, y, rect, painter)
    
                x0 = self.offset + self.newSide + self.newSide * self.board.getXCurrentCell()
                y0 = (self.newSide * self.board.getY()) - (self.newSide * self.board.getYCurrentCell())
                self.painter.markCurrentCell(QtCore.QRect(x0, y0, self.newSide, self.newSide), painter)
                self.drawRoseOfWinds(painter)
                self.drawCellNumbers(painter)
                painter.end()
                painter = QtGui.QPainter()
                painter.begin(self)
                painter.drawPixmap(0, 0, self.surface) #load graph from Bitmap
                painter.end()
            except ParseError as e:
                self.closeResultsAndShowTheXMLError(e.position)
        else:
            try:
                painter = QtGui.QPainter()
                painter.begin(self)
                painter.drawPixmap(0, 0, self.surface) #load graph from Bitmap
                painter.end()
            except ParseError as e:
                self.closeResultsAndShowTheXMLError(e.position)

    def roundCellBordersOnClothing(self, x, y, rect, painter):
        if not self.clothing.startswith('Gobstones') and "PixelBoard" in self.clothing:
            imgName = self.board.getRoundedBorderTranslucentImageName(x, y)
            img = QtGui.QImage(':/' + imgName + '.png')
            painter.drawImage(rect, img)

    def closeResultsAndShowTheXMLError(self, lineColumn):
        self.mainW.results.close()
        (filepath, filename) = os.path.split(str(self.clothing))
        ErrorWindow(i18n('The file <{0}> has an error\n in line: {1} - column: {2}').
            format(unicode(filename),lineColumn[0],lineColumn[1]))

    def drawRoseOfWinds(self, painter):
        if gui.mainWindow.MainWindow.getPreference('roseOfWinds'):
            rect = QtCore.QRect(self.offset + (self.newSide + self.board.getX() * self.newSide), 10, self.newSide, self.newSide)
            img = QtGui.QImage(':/rosa_vientos_sobria.png')
            painter.drawImage(rect, img)

    def drawCellNumbers(self, painter):
        if gui.mainWindow.MainWindow.getPreference('cellNumbers'):
            pen = QtGui.QPen(QtGui.QColor(0, 0, 0))
            pen.setWidthF(20)
            pen.setColor(QtGui.QColor("#2f4f4f"))
            painter.setPen(pen)

            self.drawCellNumbersOnTop(painter)
            self.drawCellNumbersOnBottom(painter)
            self.drawCellNumbersOnLeft(painter)
            self.drawCellNumbersOnRight(painter)


    def drawCellNumbersOnTop(self, painter):

        y0 = self.newSide/2
        x0 = self.newSide + self.offset
        for x in range (self.board.getX()):
            area = QtCore.QRect(x0, y0, self.newSide, self.newSide/2)
            painter.drawText(area, QtCore.Qt.AlignCenter, str(x))
            x0 = x0 + self.newSide

    def drawCellNumbersOnBottom(self, painter):

        y0 = self.newSide * self.board.getY() + self.newSide
        x0 = self.newSide + self.offset
        for x in range (self.board.getX()):
            area = QtCore.QRect(x0, y0, self.newSide, self.newSide/2)
            painter.drawText(area, QtCore.Qt.AlignCenter, str(x))
            x0 = x0 + self.newSide

    def drawCellNumbersOnLeft(self, painter):

        y0 = self.newSide * self.board.getY()
        x0 = self.newSide/2 + self.offset
        for x in range (self.board.getY()):
            area = QtCore.QRect(x0, y0, self.newSide/2, self.newSide)
            painter.drawText(area, QtCore.Qt.AlignCenter, str(x))
            y0 = y0 - self.newSide

    def drawCellNumbersOnRight(self, painter):

        y0 = self.newSide * self.board.getY()
        x0 = (self.newSide * self.board.getX() + self.newSide) + self.offset
        for x in range (self.board.getY()):
            area = QtCore.QRect(x0, y0, self.newSide/2, self.newSide)
            painter.drawText(area, QtCore.Qt.AlignCenter, str(x))
            y0 = y0 - self.newSide

    def keyPressEvent(self, e):
        print("viewer")
        e.ignore()


class GobstonesBoardPainter(object):
    
    def __init__(self):
        pass
    
    def draw(self, painter, rect, cell):
        pass
    
    def markCurrentCell(self, rect, painter):
        pen = QtGui.QPen(QtGui.QColor("#CC0000"))
        pen.setWidth(3)
        painter.setPen(pen)
        
        painter.drawRect(QtCore.QRect(rect.left(), rect.top(), rect.width(), 0))
        painter.drawRect(QtCore.QRect(rect.left() + rect.width(), rect.top(), 0, rect.height()))
        painter.drawRect(QtCore.QRect(rect.left(), rect.top() + rect.height(), rect.width(), 0))
        painter.drawRect(QtCore.QRect(rect.left(), rect.top(), 0, rect.height()))
        
        
class GobstonesPixelBoard(GobstonesBoardPainter):    
    
    def draw(self, painter, rect, cell):
        painter.fillRect(rect, self.cellToColor(cell))

    def cellToColor(self, cell):
        return QtGui.QColor(cell.getStones("red") * 10, 
                            cell.getStones("green") * 10, 
                            cell.getStones("blue") * 10, 
                            cell.getStones("black") * 10)
    
    def markCurrentCell(self, rect, painter):
        pass
    

class GobstonesClothing(GobstonesBoardPainter):

    def __init__(self, clothing):
        self.parser = ParseXML()
        self.gobstonesStandard = GobstonesStandard()
        self.clothing = clothing
        self.images = self.getDictFromXML(self.clothing)

    def draw(self, painter, rect, cell):
        stones = cell.getAllStones()
        if self.isIn(stones, self.images):
            if os.path.exists(self.imageLocation):
                img = QtGui.QImage(self.imageLocation)
                painter.drawImage(rect, img)
            else:
                self.gobstonesStandard.draw(painter, rect, cell)
        else:
            self.gobstonesStandard.draw(painter, rect, cell)

    def getDictFromXML(self, clothing):
        d = self.parser.getDictFromXML(clothing)
        return d

    def isIn(self, tupleStones, dictImages):
        '''Return if isIn and set the image location in 
           imageLocation attribute <-- Black Programming :'( '''
        images_dir = os.path.join(os.path.dirname(self.clothing), 'Imagenes')
        for key in dictImages:
            if(self.containsSymbols(key)):
                resOfKey = [False,False,False,False]
                for i in range(0,4):
                    if(self.isASymbol(key[i])):
                        if (key[i] == '*') and (int(tupleStones[i]) >= 0):
                            resOfKey[i] = True
                        elif (key[i] == '+') and (int(tupleStones[i]) > 0):
                            resOfKey[i] = True
                    else:
                        resOfKey[i] = tupleStones[i] == key[i]
                if resOfKey[0] and resOfKey[1] and resOfKey[2] and resOfKey[3]:
                    self.imageLocation = os.path.join(images_dir, self.images[key])
                    return True
            else:
                if tupleStones in dictImages:
                    self.imageLocation = os.path.join(images_dir, self.images[tupleStones])
                    return True
        return False

    def containsSymbols(self, tupleStones):
        res = False
        for i in range(0, 4):
            res = res or self.isASymbol(tupleStones[i])
        return res

    def isASymbol(self, char):
        return (char == '*') or (char == '+')


class GobstonesStandard(GobstonesBoardPainter):

    def __init__(self):
        self.complementaryColors = {"blue": QtGui.QColor(255, 255, 0),
                                    "green": QtGui.QColor(255, 0, 0),
                                    "black": QtGui.QColor(255, 255, 255),
                                     "red": QtGui.QColor(50, 250, 100)}
        self.colors = {"blue": QtGui.QColor(0, 0, 255),
                       "green": QtGui.QColor(0, 255, 0),
                       "black": QtGui.QColor(0, 0, 0),
                       "red": QtGui.QColor(255, 0, 0)}

    def draw(self, painter, rect, cell):
        x0, y0, x1, y1 = rect.getRect()
        self.newSide = x1/2
        self.offset = x1/2
        
        x0 = x0 + (self.newSide * 0.1)
        y0 = y0 + (self.newSide * 0.1)
        self.newSide = self.newSide * 0.8
        
        blueStone = QtCore.QRectF(x0, y0, self.newSide, self.newSide)
        blackStone = QtCore.QRectF(x0 + self.offset, y0, self.newSide, self.newSide)
        greenStone = QtCore.QRectF(x0 + self.offset, y0 + self.offset, self.newSide, self.newSide)
        redStone = QtCore.QRectF(x0, y0 + self.offset, self.newSide, self.newSide)
        
        self.drawSingleStone(painter, blueStone, "blue", cell)
        self.drawSingleStone(painter, blackStone, "black", cell)
        self.drawSingleStone(painter, greenStone, "green", cell)
        self.drawSingleStone(painter, redStone, "red", cell)

        pen = QtGui.QPen(QtGui.QColor(200, 50, 50))
        pen.setWidth(1)
        painter.setPen(pen)

        painter.setBrush(QtGui.QColor(255, 255, 255))

    def drawSingleStone(self, painter, stoneArea, colorName, cell):
        quantity = cell.getStones(colorName)
        if quantity > 0:
            pen = QtGui.QPen(QtGui.QColor(0, 0, 0))
            pen.setWidth(1)
            painter.setPen(pen)

            x0, y0, x1, y1 = stoneArea.getRect()

            x0 = x0 + 2
            y0 = y0 + 2
            x1 = x1 * 0.8
            y1 = y1 * 0.8

            painter.setBrush(self.colors[colorName])
            '''
            painter.drawEllipse(x0, y0, x1, y1)
            '''
            color = ':/' + colorName + '.png'
            img = QtGui.QImage(color)
            painter.drawImage(stoneArea, img)
            self.drawQuantity(painter, colorName, stoneArea, quantity)

    def drawQuantity(self, painter, colorName, stoneArea, quantity):
            pen = QtGui.QPen(QtGui.QColor("white"))
            pen.setWidth(2)
            painter.setPen(pen)

            painter.drawText(stoneArea, QtCore.Qt.AlignCenter, str(quantity))


class BoardViewerError(QtGui.QWidget):

    def __init__(self):
        super(BoardViewerError, self).__init__()
        self.setGeometry(0, 0, 560, 521)
        self.show()

    def paintEvent(self, event):
        painter = QtGui.QPainter()
        painter.Antialiasing
        painter.begin(self)
        rect = QtCore.QRect(0, 0, 560, 521)
        img = QtGui.QImage(':/boom.png')
        painter.drawImage(rect, img)
        painter.end()

    def is_board_error(self):
        return True
