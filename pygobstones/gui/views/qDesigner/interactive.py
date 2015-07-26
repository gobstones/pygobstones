# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'interactive.ui'
#
# Created: Sun Aug 18 11:55:59 2013
#      by: PyQt4 UI code generator 4.9.1
#
# WARNING! All changes made in this file will be lost!

from PyQt4 import QtCore, QtGui
from commons.i18n import *

try:
    _fromUtf8 = QtCore.QString.fromUtf8
except AttributeError:
    _fromUtf8 = lambda s: s

class Ui_Interactive(object):
    def setupUi(self, Form):
        Form.setObjectName(_fromUtf8("Form"))
        Form.resize(661, 527)
        self.verticalLayout_2 = QtGui.QVBoxLayout(Form)
        self.verticalLayout_2.setObjectName(_fromUtf8("verticalLayout_2"))
        self.verticalLayout = QtGui.QVBoxLayout()
        self.verticalLayout.setObjectName(_fromUtf8("verticalLayout"))
        self.boardViewer = InteractiveTabWidget(Form)
        self.labelViews = QtGui.QLabel(Form)
        font = QtGui.QFont()
        font.setPointSize(10)
        font.setWeight(50)
        self.labelViews.setFont(font)
        self.labelViews.setObjectName(_fromUtf8("labelViews"))
        self.labelViews.setStyleSheet("color:'#4682b4'; font-size:16px; padding-top:5px")
        self.labelViews.setAlignment(QtCore.Qt.AlignRight)
        self.boardViewer.setObjectName(_fromUtf8("boardViewer"))
        self.horizontalLayout_3 = QtGui.QHBoxLayout()
        self.horizontalLayout_3.setObjectName(_fromUtf8("horizontalLayout_3"))
        self.verticalLayout.addLayout(self.horizontalLayout_3)
        self.verticalLayout.addWidget(self.boardViewer)
        self.horizontalLayout_2 = QtGui.QHBoxLayout()
        self.horizontalLayout_2.setObjectName(_fromUtf8("horizontalLayout_2"))
        self.horizontalLayout = QtGui.QHBoxLayout()
        self.horizontalLayout.setObjectName(_fromUtf8("horizontalLayout"))
        self.label = QtGui.QLabel(Form)
        self.label.setObjectName(_fromUtf8("label"))
        self.label.setAlignment(QtCore.Qt.AlignRight)
        self.horizontalLayout.addWidget(self.label)

        self.labelResults = QtGui.QLabel(Form)
        font = QtGui.QFont()
        font.setPointSize(16)
        font.setBold(True)
        font.setWeight(75)
        self.labelResults.setFont(font)
        self.labelResults.setObjectName(_fromUtf8("labelResults"))
        self.horizontalLayout_3.addWidget(self.labelResults)
        self.horizontalLayout_3.addWidget(self.labelViews)
        self.labelResults.setStyleSheet("color:'#4682b4'; font-size:28px;")

        self.pushButton = InteractivePushButton(Form)
        self.pushButton.setMaximumSize(QtCore.QSize(200, 16777215))
        self.pushButton.setObjectName(_fromUtf8("pushButton"))
        self.horizontalLayout_2.addWidget(self.pushButton)
        self.horizontalLayout_2.addLayout(self.horizontalLayout)
        self.combo = InteractiveComboBox(Form)
        self.combo.setStyleSheet("background-color:'white'; color:'#4682b4'; border:2px solid #4682b4; font-size:15px")
        self.combo.setMinimumWidth(120)
        self.horizontalLayout_3.addWidget(self.combo)
        self.verticalLayout.addLayout(self.horizontalLayout_2)
        self.verticalLayout_2.addLayout(self.verticalLayout)

        self.retranslateUi(Form)
        QtCore.QMetaObject.connectSlotsByName(Form)

    def retranslateUi(self, Form):
        Form.setWindowTitle(QtGui.QApplication.translate("Form", i18n("Interactive Mode"), None, QtGui.QApplication.UnicodeUTF8))
        self.label.setText(QtGui.QApplication.translate("Form", '   ' + i18n("Press a key to Continue"), None, QtGui.QApplication.UnicodeUTF8))
        self.pushButton.setText(QtGui.QApplication.translate("Form", i18n('Switch Views'), None, QtGui.QApplication.UnicodeUTF8))
        self.labelViews.setText(QtGui.QApplication.translate("results", i18n('Select View'), None, QtGui.QApplication.UnicodeUTF8))
        self.labelResults.setText(QtGui.QApplication.translate("results", i18n('Interactive'), None, QtGui.QApplication.UnicodeUTF8))

class InteractiveTabWidget(QtGui.QTabWidget):
    def __init__(self, parent):
        super(InteractiveTabWidget, self).__init__(parent)
        tabBar = InteractiveTabBar(self)
        self.setTabBar(tabBar)
        self.setStyleSheet("border:2px solid #4682b4; background-color:'white';")
    
    def keyPressEvent(self, e):
        e.ignore()
        
class InteractivePushButton(QtGui.QPushButton):
    def __init__(self, parent):
        super(InteractivePushButton, self).__init__(parent)
        self.setStyleSheet("background-color:'white'; color:'#4682b4'; border:2px solid #4682b4; font-size:15px")
    
    def keyPressEvent(self, e):
        e.ignore()


class InteractiveComboBox(QtGui.QComboBox):
    def __init__(self, parent):
        super(InteractiveComboBox, self).__init__(parent)
        self.setStyleSheet("background-color:'white'; color:'#4682b4'; border:2px solid #4682b4; font-size:15px")

    def keyPressEvent(self, e):
        e.ignore()
        
class InteractiveTabBar(QtGui.QTabBar):
    def __init__(self, parent):
        super(InteractiveTabBar, self).__init__(parent)
        self.setAttribute(QtCore.Qt.WA_TranslucentBackground)
        self.setStyleSheet("background-color:'white'; color:'#4682b4'; border:2px solid #4682b4; font-size:15px")

    def keyPressEvent(self, e):
        e.ignore()       
        

if __name__ == '__main__':
    import sys
    app = QtGui.QApplication(sys.argv)
    QWidget = QtGui.QWidget()
    ui = Ui_Interactive()
    ui.setupUi(QWidget)
    QWidget.show()
    sys.exit(app.exec_())
