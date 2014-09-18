# -*- coding: utf-8 -*-
import os
import sys
import random
from PyQt4 import QtGui
from PyQt4 import QtCore
from PyQt4.QtGui import QMessageBox
import PyQt4
import views.resources
from errorWindow import *
from views.boardOption import *
sys.path.append('..')
from commons.i18n import *
from commons.utils import root_path
from views.boardPrint.parseBoard import *
from editor import *
from views.viewEditor import *
from views.boardPrint.boardEditor import *


class BoardOptionsWindow(QtGui.QDialog):

    def __init__(self, parent, generator):
        super(BoardOptionsWindow, self).__init__(parent)
        self.ui = Ui_BoardOptions()
        self.ui.setupUi(self)
        self.initialBoardGenerator = generator
        self.initActions()
        self.dictionary= self.initDictionary()
        self.setStyleSheet("QDialog {background-color:'white'; border:2px solid #4682b4; border-color:'#4682b4';}")

    def initDictionary(self):
        dictionary = {
            'current conservation balls': 'currentConservationBalls',
            'current conservation dimensions': 'currentConservationDimensions',
            'current conservation coordinate': 'currentConservationCoordinate',
            'enter dimensions': 'enterSizeBoard',
            'enter coordinate': 'enterHeadPosition',
            'head random': 'randomHeadBoard',
            'dimensions random': 'randomSizeBoard',
            'balls random': 'randomCellsBoard',
            'without balls': 'emptyCellsBoard',
            }
        return dictionary

    def initActions(self):
        self.initCombo1Balls()
        self.initCombo2SizeDimensions()
        self.initCombo3HeadPosition()
        self.connect(self.ui.comboBox, QtCore.SIGNAL('activated(QString)'), self.comboBox_chosen)
        self.connect(self.ui.comboBox_2, QtCore.SIGNAL('activated(QString)'), self.comboBox_chosen)
        self.connect(self.ui.comboBox_3, QtCore.SIGNAL('activated(QString)'), self.comboBox_chosen)

    def initCombo1Balls(self):
        self.ui.comboBox.addItem(i18n('current conservation balls'))
        self.ui.comboBox.addItem(i18n('balls random'))
        self.ui.comboBox.addItem(i18n('without balls'))
        self.ui.comboBox.setCurrentIndex(self.initialBoardGenerator.options[0])

    def initCombo2SizeDimensions(self):
        self.ui.comboBox_2.addItem(i18n('current conservation dimensions'))
        self.ui.comboBox_2.addItem(i18n('enter dimensions'))
        self.ui.comboBox_2.addItem(i18n('dimensions random'))
        self.ui.comboBox_2.setCurrentIndex(self.initialBoardGenerator.options[1])

    def initCombo3HeadPosition(self):
        self.ui.comboBox_3.addItem(i18n('current conservation coordinate'))
        self.ui.comboBox_3.addItem(i18n('enter coordinate'))
        self.ui.comboBox_3.addItem(i18n('head random'))
        self.ui.comboBox_3.setCurrentIndex(self.initialBoardGenerator.options[2])

    def makeRelationshipBetweenHeadAndSize(self, s):
        if(s == 'enter coordinate' or s == 'current conservation coordinate'):
            self.ui.comboBox_2.clear()
            self.ui.comboBox_2.addItem(i18n('current conservation dimensions'))
        if(s == 'head random'):
            self.ui.comboBox_2.clear()
            self.initCombo2SizeDimensions()
        self.ui.comboBox_2.update()

    def makeRelationshipBetweenSizeAndHead(self, s):
        if(s == 'dimensions random'):
            self.ui.comboBox_3.clear()
            self.ui.comboBox_3.addItem(i18n('head random'))
        if(s == 'enter dimensions' or s == 'current conservation dimensions'):
            self.ui.comboBox_3.clear()
            self.initCombo3HeadPosition()
        self.ui.comboBox_3.update()

    def comboBox_chosen(self, string):
        s = getEnglishTraduction(string)
        self.makeRelationshipBetweenSizeAndHead(s)
        self.makeRelationshipBetweenHeadAndSize(s)
        function = 'self.' + self.dictionary[s] + '()'
        exec(function)

    def currentConservationBalls(self):
        self.initialBoardGenerator.ballsFunction = self.initialBoardGenerator.nothingBalls

    def currentConservationDimensions(self):
        self.initialBoardGenerator.sizeBoardFunction = self.initialBoardGenerator.nothingSize

    def currentConservationCoordinate(self):
        self.initialBoardGenerator.headPositionFunction = self.initialBoardGenerator.nothingHead

    def enterSizeBoard(self):
        self.openSelectBoardSizeWindow(self.acceptBoardSize, 'Board Dimensions')

    def enterHeadPosition(self):
        self.openSelectBoardSizeWindow(self.acceptHeadPosition, 'Head Coordinate')

    def accept(self):
        self.parentWidget().initialBoardGenerator = self.initialBoardGenerator
        self.parentWidget().update()
        self.close()

    def openSelectBoardSizeWindow(self, function, title):

        self.widgetSize = QtGui.QDialog(self)
        self.widgetSize.setWindowTitle(i18n(title))
        self.widgetSize.setGeometry(500, 300, 180, 180)
        self.widgetSize.setMaximumSize(280, 200)
        self.setStyleSheet("background-color:'white'")

        widthL = QtGui.QLabel(self.widgetSize)
        widthL.setText(i18n('input') + ' x')
        widthL.move(20, 20)
        self.widthLE = QtGui.QLineEdit(self.widgetSize)
        self.widthLE.setGeometry(20, 45, 80, 30)
        
        heightL = QtGui.QLabel(self.widgetSize)
        heightL.setText(i18n('input')+ ' y')
        heightL.move(20, 70)
        self.heightLE = QtGui.QLineEdit(self.widgetSize)
        self.heightLE.setGeometry(20, 95, 80, 30)

        hLayout = QtGui.QHBoxLayout()
        hLayout.addStretch(1)
        acceptButton = QtGui.QPushButton(i18n('Accept'))
        acceptButton.clicked.connect(function)
        hLayout.addWidget(acceptButton)

        vLayout = QtGui.QVBoxLayout()
        vLayout.addStretch(1)
        vLayout.addLayout(hLayout)

        self.widgetSize.setLayout(vLayout)

        self.widgetSize.exec_()


    def acceptBoardSize(self):
        y = self.heightLE.text()
        x = self.widthLE.text()
        if (self.isValidInt(x, 1) and self.isValidInt(y, 1)):
            self.setBoardSize(int(self.widthLE.text()), int(self.heightLE.text()))
            self.widgetSize.close()
        else:
            ErrorWindow(i18n("You must enter integers greater than zero!"))

    def acceptHeadPosition(self):
        y = self.heightLE.text()
        x = self.widthLE.text()
        if (self.isValidIntAndPosition(x,y)):
            self.initialBoardGenerator.setHead(int(self.widthLE.text()), int(self.heightLE.text()))
            self.widgetSize.close()
        else:
            ErrorWindow(i18n("You must enter integers less or equal than ({0},{1})").
            format(self.initialBoardGenerator.board.getX()-1,self.initialBoardGenerator.board.getY()-1))

    def isValidIntAndPosition(self, posX, posY):
        return self.isValidInt(posX, 0) and self.isValidInt(posY, 0) and self.isValidPosition(posX, posY)

    def isValidPosition(self, posX, posY):
        return self.initialBoardGenerator.board.getX() > int(posX) and self.initialBoardGenerator.board.getY() > int(posY)

    def isValidInt(self, n, minNum):
        try:
            int(n)
            if (int(n) >= minNum):
                return True
            else:
                return False
        except:
            return False

    def setBoardSize(self, width, height):
        newBoard = self.fitBoard(self.initialBoardGenerator.board, width, height)
        self.initialBoardGenerator.sizeBoardFunction = self.initialBoardGenerator.nothingSize
        self.initialBoardGenerator.board = newBoard

    def fitBoard(self, board, x, y):
        if(board.size[0] > x or board.size[1] > y):
            newBoard = Board(None, {}, None)
            newBoard.setHead(0, 0)
            for k, v in board.cells:
                if(k < x and v < y):
                    newBoard.addCell((k, v), board.cells[(k, v)])
            newBoard.setSize(x, y)
            return newBoard
        else:
            board.setSize(x, y)
            return board

    def randomCellsBoard(self):
        self.initialBoardGenerator.ballsFunction = self.initialBoardGenerator.randomCellsBoard

    def emptyCellsBoard(self):
        self.initialBoardGenerator.ballsFunction = self.initialBoardGenerator.emptyCellsBoard

    def randomSizeBoard(self):
        self.initialBoardGenerator.sizeBoardFunction = self.initialBoardGenerator.randomSizeBoard

    def randomHeadBoard(self):
        self.initialBoardGenerator.headPositionFunction = self.initialBoardGenerator.randomHeadBoard


class BoardOption(object):

    def __init__(self, parent):
        self.parent = parent
        self.boardEditor = None

    def loadBoard(self):
        filename = QtGui.QFileDialog.getOpenFileName(self.parent, i18n('Open File'),
        root_path(), '*.gbb')
        if not filename == PyQt4.QtCore.QString(''):
            fname = open(filename)
            data = fname.read()
            self.parent.setInitialBoard(data)
            fname.close()

    def openBoardOptionWindow(self, generator):
        bw = BoardOptionsWindow(self.parent, generator)
        bw.show()

    def openBoardEditor(self, generator):
        if self.boardEditor is None:
            self.boardEditor = Editor(self.parent, generator)
        self.boardEditor.show()
