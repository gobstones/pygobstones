# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'boardEditor.ui'
#
# Created by: PyQt4 UI code generator 4.9.6
#
# WARNING! All changes made in this file will be lost!

from PyQt4 import QtCore, QtGui
from boardPrint.boardEditor import *
from commons.i18n import i18n

try:
    _fromUtf8 = QtCore.QString.fromUtf8
except AttributeError:
    def _fromUtf8(s):
        return s

try:
    _encoding = QtGui.QApplication.UnicodeUTF8
    def _translate(context, text, disambig):
        return QtGui.QApplication.translate(context, text, disambig, _encoding)
except AttributeError:
    def _translate(context, text, disambig):
        return QtGui.QApplication.translate(context, text, disambig)

class Ui_editor(object):
    def setupUi(self, editor):
        editor.setObjectName(_fromUtf8("editor"))
        editor.resize(640, 480)
        self.verticalLayout = QtGui.QVBoxLayout(editor)
        self.verticalLayout.setObjectName(_fromUtf8("verticalLayout"))
        self.horizontalLayout = QtGui.QHBoxLayout()
        self.horizontalLayout.setObjectName(_fromUtf8("horizontalLayout"))
        self.comboBoxLoad = QtGui.QComboBox(editor)
        self.comboBoxLoad.setObjectName(_fromUtf8("comboBoxLoad"))
        self.horizontalLayout.addWidget(self.comboBoxLoad)
        self.combo_box_persist = QtGui.QComboBox(editor)
        self.combo_box_persist.setObjectName(_fromUtf8("combo_box_persist"))
        self.horizontalLayout.addWidget(self.combo_box_persist)
        self.combo_box_options = QtGui.QComboBox(editor)
        self.combo_box_options.setObjectName(_fromUtf8("combo_box_options"))
        self.horizontalLayout.addWidget(self.combo_box_options)
        self.verticalLayout.addLayout(self.horizontalLayout)
        self.boardEditor = BoardEditor(editor)
        self.boardEditor.setObjectName(_fromUtf8("boardEditor"))
        self.verticalLayout.addWidget(self.boardEditor)

        self.boardEditor.setStyleSheet("border:2px solid #4682b4; border-color:'#4682b4';")
        self.comboBoxLoad.setStyleSheet("background-color:'white'; color:'#4682b4'; border:2px solid #4682b4; font-size:15px")
        self.combo_box_persist.setStyleSheet("background-color:'white'; color:'#4682b4'; border:2px solid #4682b4; font-size:15px")
        self.combo_box_options.setStyleSheet("background-color:'white'; color:'#4682b4'; border:2px solid #4682b4; font-size:15px")

        self.retranslateUi(editor)
        QtCore.QMetaObject.connectSlotsByName(editor)

    def retranslateUi(self, editor):
        editor.setWindowTitle(_translate("editor", i18n("Board Editor"), None))


