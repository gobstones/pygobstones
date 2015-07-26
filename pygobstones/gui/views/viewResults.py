# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'viewResults.ui'
#
# Created: Tue Jul  9 18:39:15 2013
#      by: PyQt4 UI code generator 4.9.1
#
# WARNING! All changes made in this file will be lost!


from PyQt4 import QtCore, QtGui
from PyQt4 import Qt
import sys
import os
sys.path.append('..')
from commons.i18n import *
from commons.qt_utils import *

try:
    _fromUtf8 = QtCore.QString.fromUtf8
except AttributeError:
    _fromUtf8 = lambda s: s

class Ui_results(object):
    def setupUi(self, results):
        results.setObjectName(_fromUtf8("results"))
        results.resize(600, 600)
        results.setStyleSheet("QLabel{color:blue;}")
        self.gridLayout = QtGui.QGridLayout(results)
        self.gridLayout.setObjectName(_fromUtf8("gridLayout"))
        self.pushButtonSaveResults = QtGui.QPushButton(results)
        self.pushButtonSaveResults.setObjectName(_fromUtf8("pushButtonSaveResults"))
        self.pushButtonSaveResults.setStyleSheet("height:20; background-color:'white'; color:'#4682b4'; border:2px solid #4682b4; font-size:15px")
        self.pushButtonSwitchViews = QtGui.QPushButton(results)
        self.pushButtonSwitchViews.setObjectName(_fromUtf8("pushButtonSwitchViews"))
        self.pushButtonSwitchViews.setStyleSheet("height:20; background-color:'white'; color:'#4682b4'; border:2px solid #4682b4; font-size:15px")
        self.gridLayout.addWidget(self.pushButtonSaveResults, 3, 1, 1, 1)
        self.gridLayout.addWidget(self.pushButtonSwitchViews, 3, 0, 1, 1)
        self.tabWidgetResults = QtGui.QTabWidget(results)
        self.tabWidgetResults.tabBar().setStyleSheet("background-color:'white'; color:'#4682b4'; border:2px solid #4682b4; font-size:15px")
        self.tabWidgetResults.setObjectName(_fromUtf8("tabWidgetResults"))
        self.tabWidgetResults.setStyleSheet("background-color:'white'; border:2px solid #4682b4;")
        self.tabWidgetResults.tabBar().setAttribute(QtCore.Qt.WA_TranslucentBackground)
        


        # Original code
        self.tabFileCode = QtGui.QTextEdit()
        self.tabLibraryCode = QtGui.QTextEdit()
        self.splitter = QtGui.QSplitter(QtCore.Qt.Vertical, results)
        self.splitter.addWidget(self.tabFileCode)
        self.splitter.addWidget(self.tabLibraryCode)
        self.splitter.setObjectName(_fromUtf8("tabCode"))
        self.tabWidgetResults.addTab(self.splitter, _fromUtf8(""))
        
        
        # Return Values         
        self.initializeRetVarsInspector(results)

        self.gridLayout.addWidget(self.tabWidgetResults, 2, 0, 1, 2)

        self.labelResults = QtGui.QLabel(results)
        font = QtGui.QFont()
        font.setPointSize(16)
        font.setBold(True)
        font.setWeight(75)
        self.labelResults.setFont(font)
        self.labelResults.setObjectName(_fromUtf8("labelResults"))
        self.gridLayout.addWidget(self.labelResults, 0,0,1,1)
        self.labelResults.setStyleSheet("color:'#4682b4'; font-size:28px;")


        self.labelViews = QtGui.QLabel(results)
        font = QtGui.QFont()
        font.setPointSize(10)
        font.setWeight(50)
        self.labelViews.setFont(font)
        self.labelViews.setObjectName(_fromUtf8("labelViews"))
        self.labelViews.setStyleSheet("color:'#4682b4'; font-size:16px; padding-top:5px")
        
        self.combo = QtGui.QComboBox(results)
        self.combo.setStyleSheet("background-color:'white'; color:'#4682b4'; border:2px solid #4682b4; font-size:15px")
        #self.combo.setSizeAdjustPolicy(QtGui.QComboBox.AdjustToContents)
        self.combo.setMinimumWidth(120)

        #self.labelViews.setBuddy(self.combo)
        self.labelViews.setAlignment(QtCore.Qt.AlignRight)

        self.selectViews = QtGui.QHBoxLayout()
        self.selectViews.addWidget(self.labelViews)
        self.selectViews.addWidget(self.combo)

        self.gridLayout.addLayout(self.selectViews, 0, 1, 1, 1)

        self.retranslateUi(results)
        QtCore.QMetaObject.connectSlotsByName(results)

    def showRetVars(self, retVars):
        self.retVarsTable.clear()
        if not retVars is None:
            populateTable(self.retVarsTable, retVars)
            self.retVarsTable.update()

    def initializeRetVarsInspector(self, results):            
        # RetVars table
        self.retVarsTable = QtGui.QTableWidget(results)
        self.retVarsTable.setHorizontalHeaderLabels([_fromUtf8('Varname'), _fromUtf8('Value')]) 
        self.retVarsTable.horizontalHeader().hide()       
        self.retVarsTable.verticalHeader().hide()
        self.retVarsTable.setEditTriggers(QtGui.QTableWidget.NoEditTriggers)
        self.retVarsTable.horizontalHeader().setStretchLastSection(True)   
        self.retVarsTable.setSelectionBehavior(QtGui.QAbstractItemView.SelectRows)     
        # RetVars Inspector
        self.retVarsInspector = QtGui.QTextEdit()
        #  RetVars Splitter
        self.retVarsSplitter = QtGui.QSplitter(QtCore.Qt.Vertical, results)
        self.retVarsSplitter.setObjectName(_fromUtf8("tabRetVars"))
        self.retVarsSplitter.addWidget(self.retVarsTable)
        self.retVarsSplitter.addWidget(self.retVarsInspector)
        # Add Splitter
        self.tabWidgetResults.addTab(self.retVarsSplitter, _fromUtf8("labelRetVars"))
        self.tabWidgetResults.setTabText(self.tabWidgetResults.indexOf(self.retVarsSplitter), QtGui.QApplication.translate("results", i18n('Return Values'), None, QtGui.QApplication.UnicodeUTF8))

    def retranslateUi(self, results):
        results.setWindowTitle(QtGui.QApplication.translate("results", i18n('Mode Results'), None, QtGui.QApplication.UnicodeUTF8))
        self.pushButtonSaveResults.setToolTip(QtGui.QApplication.translate("results", i18n('Save in file the final board'), None, QtGui.QApplication.UnicodeUTF8))
        self.pushButtonSaveResults.setText(QtGui.QApplication.translate("results", i18n('Save Final Board'), None, QtGui.QApplication.UnicodeUTF8))
        self.pushButtonSwitchViews.setToolTip(QtGui.QApplication.translate("switchViews", i18n('Switch between Gobstones Standard view and selected custom view'), None, QtGui.QApplication.UnicodeUTF8))
        self.pushButtonSwitchViews.setText(QtGui.QApplication.translate("switchViews", i18n('Switch Views'), None, QtGui.QApplication.UnicodeUTF8))
        #self.tabWidgetResults.setTabText(self.tabWidgetResults.indexOf(self.tabInitialBoard), QtGui.QApplication.translate("results", i18n('Initial Board'), None, QtGui.QApplication.UnicodeUTF8))
        #self.tabWidgetResults.setTabText(self.tabWidgetResults.indexOf(self.tabFinalBoard), QtGui.QApplication.translate("results", i18n('Final Board'), None, QtGui.QApplication.UnicodeUTF8))

        self.tabWidgetResults.setTabText(self.tabWidgetResults.indexOf(self.splitter), QtGui.QApplication.translate("results", i18n('Source Code'), None, QtGui.QApplication.UnicodeUTF8))

        self.labelResults.setText(QtGui.QApplication.translate("results", i18n('Results'), None, QtGui.QApplication.UnicodeUTF8))
        self.labelViews.setText(QtGui.QApplication.translate("results", i18n('Select View'), None, QtGui.QApplication.UnicodeUTF8))


