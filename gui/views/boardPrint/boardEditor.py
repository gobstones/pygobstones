 
#!/usr/local/bin/python

import os, sys
from PyQt4.Qt import *
from PyQt4.QtCore import *
from PyQt4.QtGui import *
from board import *
from parseBoard import *
import resources
import gui

class BoardEditor(QGraphicsView):
    def __init__(self, parent):
        QGraphicsView.__init__(self, parent)
        self.setRenderHint(QPainter.Antialiasing)
    
    def setBoard(self, board):
        self.board = parseABoardString(board)
    
    def getEditedBoard(self):
        return self.board
    
    def populate(self):
        self.scene = QGraphicsScene(self)
        self.drawBoard(self.scene)
        self.setScene(self.scene)
    
    def keyPressEvent(self, e):
        if e.key() == Qt.Key_Left:
            self.board.moveHeadToLeft()
        elif e.key() == Qt.Key_Right:
            self.board.moveHeadToRight()
        elif e.key() == Qt.Key_Up:
            self.board.moveHeadToUp()
        elif e.key() == Qt.Key_Down:
            self.board.moveHeadToDown()
        self.populate()
        
    def save_to_image(self, filename):
        pixmap = QPixmap.grabWidget(self)
        r = pixmap.rect()
        
        reduction_percent = 0
        if not gui.mainWindow.MainWindow.getPreference('cellNumbers'):
            reduction_percent = 0.15
        
        height = r.height() - reduction_percent * r.height()
        width = r.width() - reduction_percent * r.width()
        x = r.x() + (reduction_percent * r.width())/2
        y = r.y() + (reduction_percent * r.height())/2
        if width > height:
            newr = QRect(x + (width - height)/2, y, height, height)
        else:
            newr = QRect(x, y + (height - width)/2, width, width)
        pixmap.copy(newr).save(filename)
        
    def drawBoard(self, scene):
        x = self.board.size[0]
        y = self.board.size[1]

        width = self.width()
        height = self.height()
        
        if (x > y):
            sideX = width / (x + 2)
            sideY = height / (y + 2)
            
            sizeHeight = sideX * (y + 2)
            sizeWidth = sideY * (x + 2)
            
            if (sizeHeight < height):
                newSide = sideX
            else:
                newSide = sideY
        else:
            s = min(width, height)        
            newSide = s / (max(x, y) + 2)
               
        for xs in range(x):
            yLarge = newSide * y
            for ys in range(y):
                if self.board.isCurrentCell((xs, ys)):
                    self.p = (scene, newSide * xs + newSide, yLarge, newSide, self.board, (xs, ys))
                else:
                    self.drawCell(scene, newSide * xs + newSide, yLarge, newSide, self.board, (xs, ys))
                yLarge -= newSide 
        
        if gui.mainWindow.MainWindow.getPreference('cellNumbers'):
            #draw cell numbers on top
            for xs in range(x):
                i = Number(xs, newSide, newSide)
                i.moveBy(newSide * xs + newSide, 0)
                self.scene.addItem(i) 
            
            #draw cell numbers on bottom
            for xs in range(x):
                i = Number(xs, newSide, newSide)
                i.moveBy(newSide * xs + newSide, newSide * y + newSide)
                self.scene.addItem(i) 
    
            #draw cell numbers on left
            zero = newSide * y + newSide
            for ys in range(y):
                i = Number(ys, newSide, newSide)
                zero -= newSide
                i.moveBy(0, zero)
                self.scene.addItem(i) 
                
            #draw cell numbers on right    
            zero = newSide * y + newSide
            for ys in range(y):
                i = Number(ys, newSide, newSide)
                zero -= newSide
                i.moveBy(newSide * x + newSide, zero)
                self.scene.addItem(i)
            
        #draw current cell    
        self.drawCell(self.p[0], self.p[1], self.p[2], self.p[3], self.p[4], self.p[5], True)
            
    def drawCell(self, scene, moveX, moveY, side, board, coord, isHead=False):
        diameter = side / 2
        
        imgName = self.board.getImageName(coord[0], coord[1])
        
        self.container = Cell('container', side, side, imgName, isHead)
        self.container.moveBy(moveX, moveY)
        self.item = StoneEditor('item', diameter, diameter, 'blue', board, coord, self.container)
        self.item.moveBy(0, 0)
        self.item2 = StoneEditor('item', diameter, diameter, 'black', board, coord, self.container)
        self.item2.moveBy(diameter, 0)
        self.item3 = StoneEditor('item', diameter, diameter, 'green', board, coord, self.container)
        self.item3.moveBy(diameter, diameter)
        self.item4 = StoneEditor('item', diameter, diameter, 'red', board, coord, self.container)
        self.item4.moveBy(0, diameter)
        self.scene.addItem(self.container)
        
    def resizeEvent(self, event):
        self.populate()
        self.update()
    
    def getBoardEdited(self):
        return boardToString(self.board)
       
class Cell(QGraphicsItem):
    def __init__(self, name, width, height, imageName, isHead = False, parent = None):
        QGraphicsItem.__init__(self, parent)
        self.name = name
        self.__width = width
        self.__height = height
        self.w=width
        self.isHead = isHead
        self.imgName = imageName
        
    def paint(self, painter, option, widget):
        bgRect = self.boundingRect()
        
        img = QImage(':/' + self.imgName + '.png')
        painter.drawImage(bgRect, img)
        
        if self.isHead:
            pen2 = QPen(QColor("#CC0000"))
            pen2.setWidth(3)
            painter.setPen(pen2)
            painter.drawRect(bgRect)
    

    def boundingRect(self): 
        return QRectF(0, 0, self.__width, self.__height)

class Number(QGraphicsItem):
    def __init__(self, number, width, height, parent = None):
        QGraphicsItem.__init__(self, parent)
        self.number = number
        self.__width = width
        self.__height = height
        
    def paint(self, painter, option, widget):
        bgRect = self.boundingRect()
        painter.drawText(bgRect, Qt.AlignCenter, str(self.number))
        
    def boundingRect(self): 
        return QRectF(0, 0, self.__width, self.__height)


class StoneEditor(QGraphicsItem):
    def __init__(self, name, width, height, color, board, coord, parent=None):
        QGraphicsItem.__init__(self, parent)
        self.hover = False
        self.setAcceptHoverEvents(True)
        self.name = name
        self.color = color
        self.__width = width
        self.__height = height
        self.board = board
        self.coord = coord
        self.updateQuantity()

    def boundingRect(self):
        x = self.__width * 0.1
        y = self.__height * 0.1
        x0 = self.__width * 0.8
        y0 = self.__height * 0.8
        return QRectF(x, y, x0, y0)
    
    def updateQuantity(self):
        self.quantity = self.board.getStonesOfColorOnCell(self.color, self.coord)
    
    def hoverEnterEvent(self, event):
        self.hover = True
        self.update()
        
    def hoverLeaveEvent(self, event):
        self.hover = False
        self.update()

    def mousePressEvent(self, event):
        if (event.button() == 1):
            self.board.putStoneOfColorOnCell(self.color, self.coord)
            self.updateQuantity()
        if(event.button() == 2):
            if self.quantity > 0:
                self.board.quitStoneOfColorOnCell(self.color, self.coord)
                self.updateQuantity()
        
    def mouseReleaseEvent(self, event):
        self.update()

    def paint(self, painter, option, widget):
        bgRect = self.boundingRect()
        if self.hover:
            painter.fillRect(bgRect, QBrush(QColor(self.color), Qt.Dense2Pattern))
        if self.quantity > 0:
            image = ':/' + self.color + '.png'
            img = QImage(image)
            painter.drawImage(bgRect, img)
            painter.setPen(QPen(QColor('white')))
            painter.drawText(bgRect, Qt.AlignCenter, str(self.quantity))
