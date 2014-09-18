# -*- coding: utf-8 -*-

from PyQt4 import QtGui
from PyQt4 import QtCore
from commons.i18n import *
import gui


class PreferencesWindow(QtGui.QDialog):

    def __init__(self, mainW):
        super(PreferencesWindow, self).__init__()
        self.mainW = mainW
        self.setGeometry(300, 300, 300, 150)
        self.setMaximumSize(300,150)
        self.setWindowTitle(i18n('Preferences'))
        self.setStyleSheet("QDialog {background-color:'white'; border:2px solid #4682b4; border-color:'#4682b4';}")
        self.initActions()
        self.exec_()

    def initActions(self):

        logger = QtGui.QCheckBox(i18n('show logger'), self)
        logger.move(20, 20)
        if gui.mainWindow.MainWindow.getPreference('logger'):
            logger.toggle()
        logger.stateChanged.connect(self.activateLogger)

        roseOfWinds = QtGui.QCheckBox(i18n('show rose of winds image'), self)
        roseOfWinds.move(20, 40)
        if gui.mainWindow.MainWindow.getPreference('roseOfWinds'):
            roseOfWinds.toggle()
        roseOfWinds.stateChanged.connect(self.activateRoseOfWinds)

        cellNumbers = QtGui.QCheckBox(i18n('show cell numbers'), self)
        cellNumbers.move(20, 60)
        if gui.mainWindow.MainWindow.getPreference('cellNumbers'):
            cellNumbers.toggle()
        cellNumbers.stateChanged.connect(self.activateCellNumbers)

        lineNumbers = QtGui.QCheckBox(i18n('show line numbers'), self)
        lineNumbers.move(20, 80)
        if gui.mainWindow.MainWindow.getPreference('lineNumbers'):
            lineNumbers.toggle()
        lineNumbers.stateChanged.connect(self.activateLineNumbers)
        
        autoIndentation = QtGui.QCheckBox(i18n('enable auto indentation'), self)
        autoIndentation.move(20, 100)
        if gui.mainWindow.MainWindow.getPreference('autoIndentation'):
            autoIndentation.toggle()
        autoIndentation.stateChanged.connect(self.activateAutoIndentation)

        vLayout = QtGui.QVBoxLayout()
        hLayout = QtGui.QHBoxLayout()
        hLayout.addStretch(1)
        vCheckLayout = QtGui.QVBoxLayout()

        acceptButton = QtGui.QPushButton(i18n('Accept'), self)
        acceptButton.clicked.connect(self.accept)

        vCheckLayout.addWidget(logger)
        vCheckLayout.addWidget(roseOfWinds)
        vCheckLayout.addWidget(cellNumbers)
        vCheckLayout.addWidget(lineNumbers)
        vCheckLayout.addWidget(autoIndentation)

        hLayout.addWidget(acceptButton)
        vLayout.addLayout(vCheckLayout)
        vLayout.addLayout(hLayout)
        self.setLayout(vLayout)

    def activateLogger(self, state):
        if state == QtCore.Qt.Checked:
            self.mainW.setPreference('logger', True)
            self.mainW.initLoggerSize()
        else:
            self.mainW.setPreference('logger', False)
            self.mainW.initLoggerSize()

    def activateRoseOfWinds(self, state):
        if state == QtCore.Qt.Checked:
            self.mainW.setPreference('roseOfWinds', True)
        else:
            self.mainW.setPreference('roseOfWinds', False)

    def activateCellNumbers(self, state):
        if state == QtCore.Qt.Checked:
            self.mainW.setPreference('cellNumbers', True)
        else:
            self.mainW.setPreference('cellNumbers', False)

    def activateLineNumbers(self, state):
        if state == QtCore.Qt.Checked:
            self.mainW.setPreference('lineNumbers', True)
            self.mainW.editOption.activateLineNumbers(True)
        else:
            self.mainW.setPreference('lineNumbers', False)
            self.mainW.editOption.activateLineNumbers(False)
            
    def activateAutoIndentation(self, state):
        if state == QtCore.Qt.Checked:
            self.mainW.setPreference('autoIndentation', True)
            self.mainW.editOption.activateAutoIndentation(True)
        else:
            self.mainW.setPreference('autoIndentation', False)
            self.mainW.editOption.activateAutoIndentation(False)

    def accept(self):
        self.mainW.initLoggerSize()
        self.close()
