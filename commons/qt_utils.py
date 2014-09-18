from PyQt4 import QtCore, QtGui
from PyQt4 import Qt

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