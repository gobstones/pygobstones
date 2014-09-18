# -*- coding: utf-8 -*-
from PyQt4 import QtGui
from commons.i18n import *


class ErrorWindow(QtGui.QDialog):

    def __init__(self, text):
        super(ErrorWindow, self).__init__()
        self.setGeometry(300, 300, 200, 100)
        self.setWindowTitle("ERROR !!!")
        self.initMessageAndAcceptButton(text)
        self.exec_()

    def initMessageAndAcceptButton(self, text):
        hLayoutMessage = QtGui.QHBoxLayout()
        message = QtGui.QLabel(text)
        hLayoutMessage.addWidget(message)

        hLayoutButton = QtGui.QHBoxLayout()
        acceptButton = QtGui.QPushButton(i18n('Accept'), self)
        acceptButton.clicked.connect(self.close)
        hLayoutButton.addStretch(1)
        hLayoutButton.addWidget(acceptButton)

        vLayout = QtGui.QVBoxLayout()
        vLayout.addLayout(hLayoutMessage)
        vLayout.addLayout(hLayoutButton)
        self.setLayout(vLayout)