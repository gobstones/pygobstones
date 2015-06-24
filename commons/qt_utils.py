from PyQt4 import QtGui, QtCore
import commons.paths as paths
from commons.i18n import i18n 
import os

def populateTable(table, rows):
	""" Populates a table with elements. 
		'Rows' is a list of lists """
	if len(rows) > 0 and (isinstance(rows[0], list) or isinstance(rows[0], tuple)):
		table.setRowCount(len(rows))
		table.setColumnCount(len(rows[0]))
	
		for i, row in enumerate(rows):
			for j, col in enumerate(row):
				table.setItem(i, j, QtGui.QTableWidgetItem(repr(col))) 
	return table

def openFileName(parent, extensions):
	filename = QtGui.QFileDialog.getOpenFileName(parent, i18n('Open File'),
                                                 paths.last_location, extensions)
	if not filename == QtCore.QString(''):
		paths.last_location = os.path.dirname(str(filename))
	return filename

def saveFileName(parent, extensions):
	filename = QtGui.QFileDialog.getSaveFileName(parent, i18n('Save as ...'),
                                                 paths.last_location, extensions)
	if not filename == QtCore.QString(''):
		paths.last_location = os.path.dirname(str(filename))
	return filename