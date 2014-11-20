from PyQt4 import QtCore, QtGui
import sys

class GobstonesTextEditor(QtGui.QFrame):
 
    class NumberBar(QtGui.QWidget):
 
        def __init__(self, edit):
            QtGui.QWidget.__init__(self, edit)
 
            self.edit = edit
            self.adjustWidth(2)
 
        def paintEvent(self, event):
            if self.edit.drawLineNumbers:
                self.edit.numberbarPaint(self, event)       
            QtGui.QWidget.paintEvent(self, event)
 
        def adjustWidth(self, count):
            width = self.fontMetrics().width(unicode(9999))
            #width = self.fontMetrics().width(unicode(count))
            if self.width() != width:
                self.setFixedWidth(width)
 
        def updateContents(self, rect, scroll):
            if scroll:
                self.scroll(0, scroll)
            else:
                self.update()
 
 
    class PlainTextEdit(QtGui.QPlainTextEdit):
 
        def __init__(self, gbseditor, *args):
            QtGui.QPlainTextEdit.__init__(self, *args)
 
            self.gbseditor = gbseditor
            self.drawLineNumbers = True
            self.setFrameStyle(QtGui.QFrame.NoFrame)
            self.highlight()
            #self.setLineWrapMode(QPlainTextEdit.NoWrap)
 
            self.cursorPositionChanged.connect(self.highlight)
            self.setStyleSheet("font-family: Monospace, Consolas, 'Courier New'; font-weight: 100")


        def setTabWidth(self, font, width = 4):
            metrics = QtGui.QFontMetrics(font)
            self.setTabStopWidth(width * metrics.width(' '))
            self.setTabStopWidth(width * metrics.width(' '))

        def indentSelection(self):
            tab = "\t"
            cursor = self.textCursor()
            # backup selection
            begin, end = cursor.selectionStart(), cursor.selectionEnd()
            # Add one indentation per line
            cursor.setPosition(begin)                                                       
            cursor.movePosition(cursor.StartOfLine) 
            while cursor.position() < end:                    
                cursor.movePosition(cursor.StartOfLine)
                cursor.insertText(tab)
                end += 1
                cursor.movePosition(cursor.Down)
                cursor.movePosition(cursor.EndOfLine)
            # Indent last line
            cursor.movePosition(cursor.StartOfLine)
            cursor.insertText(tab)
            end += 1
            # Restore selection
            self.setSelection(begin, end)
            
        def unindentSelection(self):
            tab = "\t"
            cursor = self.textCursor()
            # backup selection
            begin, end = cursor.selectionStart(), cursor.selectionEnd()                                                       
            # Delete one indentation per line
            cursor.setPosition(begin)
            cursor.movePosition(cursor.StartOfLine) 
            while cursor.position() < end:                    
                cursor.movePosition(cursor.StartOfLine)
                cursor.setPosition(cursor.position()+1,QtGui.QTextCursor.KeepAnchor)
                if cursor.hasSelection() and cursor.selectedText() == tab:
                    cursor.removeSelectedText()
                    end -= 1                    
                cursor.movePosition(cursor.Down)
                cursor.movePosition(cursor.EndOfLine)
            # Unindent last line   
            cursor.movePosition(cursor.StartOfLine)
            cursor.setPosition(cursor.position()+1,QtGui.QTextCursor.KeepAnchor)
            if cursor.hasSelection() and cursor.selectedText() == tab:
                cursor.removeSelectedText()
                end -= 1                    
            # Restore selection
            self.setSelection(begin, end)

        def setSelection(self, start, end, cursor=None):
            if cursor is None:
                cursor = self.textCursor()
            cursor.clearSelection()
            cursor.movePosition(start, QtGui.QTextCursor.MoveAnchor)
            cursor.setPosition(end, QtGui.QTextCursor.KeepAnchor)

        def lineIndentation(self, cursor):
            tab = "\t"
            # Backup cursor
            begin, end = cursor.selectionStart(), cursor.selectionEnd()
            cursor.movePosition(cursor.EndOfLine)
            lineEnd = cursor.position()
            cursor.movePosition(cursor.StartOfLine)
            cursor.movePosition(cursor.Right, cursor.KeepAnchor)
            tabs = 0
            while cursor.selectedText() == tab and cursor.position() < lineEnd:
                tabs += 1                        
                cursor.movePosition(cursor.Right)
                cursor.movePosition(cursor.Left)
                cursor.movePosition(cursor.Right, cursor.KeepAnchor)
            if cursor.selectedText() == tab:
                tabs += 1
            # Restore cursor
            self.setSelection(begin, end)
            return tabs
            

        def copyPreviousLineIndentation(self):
            cursor = self.textCursor()
            # Backup cursor
            begin, end = cursor.selectionStart(), cursor.selectionEnd()
            # Previous line indentation
            cursor.movePosition(cursor.Up)
            indentation = self.lineIndentation(cursor)
            cursor.movePosition(cursor.Down)
            cursor.movePosition(cursor.StartOfLine)
            # Indent
            cursor.insertText('\t'*indentation)
            # Restore cursor
            self.setSelection(begin, end)
            

        def keyPressEvent(self, event):
            """ Handles custom keyPressEvents or calls default event handler """
            cursor = self.textCursor()
            if event.key() == QtCore.Qt.Key_Tab and cursor.hasSelection():
                self.indentSelection()
            elif event.key() == QtCore.Qt.Key_Backtab and cursor.hasSelection():
                self.unindentSelection()
            elif event.key() in [QtCore.Qt.Key_Enter, QtCore.Qt.Key_Return]:
                super(GobstonesTextEditor.PlainTextEdit, self).keyPressEvent(event)
                if self.gbseditor.autoIndentation:
                    self.copyPreviousLineIndentation()
            else:
                return super(GobstonesTextEditor.PlainTextEdit, self).keyPressEvent(event)

        def highlight(self):
            hi_selection = QtGui.QTextEdit.ExtraSelection()
 
            hi_selection.format.setBackground(self.palette().alternateBase())
            hi_selection.format.setProperty(QtGui.QTextFormat.FullWidthSelection, QtCore.QVariant(True))
            hi_selection.cursor = self.textCursor()
            hi_selection.cursor.clearSelection()
 
            self.setExtraSelections([hi_selection])
 
        def numberbarPaint(self, number_bar, event):

            font_metrics = self.fontMetrics()
            current_line = self.document().findBlock(self.textCursor().position()).blockNumber() + 1
 
            block = self.firstVisibleBlock()
            line_count = block.blockNumber()
            painter = QtGui.QPainter(number_bar)
            painter.fillRect(event.rect(), self.palette().base())
 
            # Iterate over all visible text blocks in the document.

            while block.isValid():
                line_count += 1
                block_top = self.blockBoundingGeometry(block).translated(self.contentOffset()).top()
 
                # Check if the position of the block is out side of the visible
                # area.
                if not block.isVisible():
                    break
 
                # We want the line number for the selected line to be bold.
                if line_count == current_line:
                    font = painter.font()
                    font.setBold(True)
                    painter.setFont(font)
                else:
                    font = painter.font()
                    font.setBold(False)
                    painter.setFont(font)
                
                # Draw the line number right justified at the position of the line.
                paint_rect = QtCore.QRect(0, block_top, number_bar.width(), font_metrics.height())
                painter.fillRect(paint_rect, QtGui.QColor('#F0F0F0'))
                pen = QtGui.QPen(QtGui.QColor('#777777'))
                painter.setPen(pen)
                painter.drawText(paint_rect, QtCore.Qt.AlignRight, unicode(line_count))
                block = block.next()
            painter.end()
 
    def __init__(self, mainw, *args):
        QtGui.QFrame.__init__(self, *args)
        self.drawLineNumbers = True
        self.mainw = mainw
    
        self.setFrameStyle(QtGui.QFrame.StyledPanel |QtGui.QFrame.Sunken)
        self.edit = self.PlainTextEdit(self)        
        self.number_bar = self.NumberBar(self.edit)

        self.autoIndentation = False
        
        hbox = QtGui.QHBoxLayout(self)
        hbox.setSpacing(0)
        hbox.setMargin(0)
        hbox.addWidget(self.number_bar)
        hbox.addWidget(self.edit)

        self.edit.blockCountChanged.connect(self.number_bar.adjustWidth)
        self.edit.updateRequest.connect(self.number_bar.updateContents)

        self.showEditor()
    
    def showEditor(self):

        if self.drawLineNumbers:
            self.number_bar.setVisible(True)
            self.edit.blockCountChanged.connect(self.number_bar.adjustWidth)
            self.edit.updateRequest.connect(self.number_bar.updateContents)
        else:
            self.number_bar.setVisible(False)
            self.edit.blockCountChanged.disconnect(self.number_bar.adjustWidth)
            self.edit.updateRequest.disconnect(self.number_bar.updateContents)
        
        self.update()

    def activateLineNumbers(self, boolean):
        self.drawLineNumbers = boolean
        self.edit.drawLineNumbers = boolean
        self.showEditor()
        
    def activateAutoIndentation(self, boolean):
        self.autoIndentation = boolean
 
    def getText(self):
        return unicode(self.edit.toPlainText())
 
    def setText(self, text):
        self.edit.setPlainText(text)
 
    def isModified(self):
        return self.edit.document().isModified()
 
    def setModified(self, modified):
        self.edit.document().setModified(modified)
 
    def setLineWrapMode(self, mode):
        self.edit.setLineWrapMode(mode)

    def setTabStopWidth(self, font):
        self.edit.setTabStopWidth(font)

    def document(self):
        return self.edit.document()

    def toPlainText(self):
        return self.edit.toPlainText()

    def setPlainText(self, data):
        self.edit.setPlainText(data)

    def clear(self):
        self.edit.clear()

    def moveCursor(self, option):
        self.edit.moveCursor(option)

    def textCursor(self):
        return self.edit.textCursor()

    def moveCursor(self, flag):
        self.edit.moveCursor(flag)

    def undo(self):
        self.edit.undo()

    def redo(self):
        self.edit.redo()

    def cut(self):
        self.edit.cut()

    def copy(self):
        self.edit.copy()

    def paste(self):
        self.edit.paste()

    def selectAll(self):
        self.edit.selectAll()

    def setFont(self, font):
        self.edit.setFont(font)


class HighlightingRule(object):
    
    def __init__(self, format):
        self.format = format


class HighlightingBasicRule(HighlightingRule):
    
    def __init__(self, text, format):
        super(HighlightingBasicRule, self).__init__(format)
        self.text = text
        
    def __repr__(self):
        return text


class HighlightingBlockRule(HighlightingRule):

    def __init__(self, begin, end, format, expected_state = None):
        super(HighlightingBlockRule, self).__init__(format)
        self.begin = begin
        self.end = end
        self.expected_state = expected_state

    def __repr__(self):
        return self.begin + "<block>" + self.end
     
    
class HighlightingRegExpRule(HighlightingRule):
  
    def __init__( self, pattern, format ):
        super(HighlightingRegExpRule, self).__init__(format)
        if isinstance(pattern, QtCore.QRegExp):
            self.pattern = pattern
        else:
            self.pattern = QtCore.QRegExp(pattern)
            
    def __repr__(self):
        return unicode(self.pattern.pattern())


class BlockState:
    UNSET = -1
    NONE = 0 
    IN_PYCOMMENT = 1
    IN_CCOMMENT = 2
    IN_HSCOMMENT = 3   
    
    
def map_regexp(patterns):
    f = lambda w: QtCore.QRegExp("\\b" + w + "\\b")
    return map(f, patterns)


def gen_highlighting_rules(xs, format, highlighting_class=HighlightingBasicRule):
    return [highlighting_class(x, format) for x in xs]


class GobstonesHighlighter( QtGui.QSyntaxHighlighter ):

    def __init__( self, parent ):
        super(GobstonesHighlighter, self).__init__(parent)
        self.parent = parent
        self.create_rules()
      
    def create_rules(self):
        keyword_format = QtGui.QTextCharFormat()
        operators_format = QtGui.QTextCharFormat()
        nativeCommand_format = QtGui.QTextCharFormat()
        delimiter = QtGui.QTextCharFormat()
        definitions_format = QtGui.QTextCharFormat()
        nativeExpression_format = QtGui.QTextCharFormat()
        number = QtGui.QTextCharFormat()
        comment = QtGui.QTextCharFormat()
        value = QtGui.QTextCharFormat()
        self.highlightingRules = []
        
        # number
        brush = QtGui.QBrush( QtGui.QColor("#e69138"), QtCore.Qt.SolidPattern )
        number.setForeground( brush )
        rule = HighlightingRegExpRule( "\\b[0-9]+\\b", number )
        self.highlightingRules.append( rule )
        
        #values
        brush = QtGui.QBrush( QtGui.QColor("#e69138"), QtCore.Qt.SolidPattern )
        value.setForeground( brush )
        values = QtCore.QStringList( [ "Norte", "Sur", "Este", "Oeste"
                                      , "Negro", "Azul", "Verde", "Rojo"
                                      , "True", "False" ] )
        for word in values:
          pattern = QtCore.QRegExp("\\b" + word + "\\b")
          rule = HighlightingRegExpRule( pattern, value )
          self.highlightingRules.append( rule )
        
        #nativeExpressions
        brush = QtGui.QBrush( QtGui.QColor("#a61c00"), QtCore.Qt.SolidPattern )
        nativeExpression_format.setForeground( brush )
        nativeExpressions = QtCore.QStringList( [ "nroBolitas", "hayBolitas", "puedeMover",
                                                  "minBool", "maxBool", "minDir", "maxDir", "minColor",
                                                  "maxColor", "siguiente", "previo", "opuesto", 
                                                  "div", "mod", "not"] )
        
        self.highlightingRules.extend(gen_highlighting_rules(map_regexp(nativeExpressions) + ["&&", "\|\|", "\+", "\-", "\*", "\^",
                                                  "<", ">", "==", "<=", ">=", "/=", "\.\."], nativeExpression_format, HighlightingRegExpRule))
        
        # keyword
        brush = QtGui.QBrush( QtGui.QColor("#3c78d8"), QtCore.Qt.SolidPattern )
        keyword_format.setForeground( brush )
        keyword_format.setFontWeight(QtGui.QFont.Bold)
        keywords = QtCore.QStringList( [ "foreach", "else", "repeat", "if", "then", "in",
                                  "return", "while", "Skip", "from",
                                  "import", "switch", "to"] )
        
        self.highlightingRules.extend(gen_highlighting_rules(map_regexp(keywords) + [":="], keyword_format, HighlightingRegExpRule))
        
        # nativeCommands
        brush = QtGui.QBrush( QtGui.QColor("#3c78d8"), QtCore.Qt.SolidPattern )
        nativeCommand_format.setForeground( brush )
        nativeCommands = QtCore.QStringList( [ "Poner", "Sacar", "Mover",
                                               "IrAlBorde", "VaciarTablero" ] )
        
        self.highlightingRules.extend(gen_highlighting_rules(map_regexp(nativeCommands), nativeCommand_format, HighlightingRegExpRule))
        
        # definitions
        brush = QtGui.QBrush( QtGui.QColor("#7029B5"), QtCore.Qt.SolidPattern )
        definitions_format.setForeground( brush )
        definitions_format.setFontWeight(QtGui.QFont.Bold)
        definitions = QtCore.QStringList( [ "interactive", "program", "procedure", "function" ] )
        
        self.highlightingRules.extend(gen_highlighting_rules(map_regexp(definitions), definitions_format, HighlightingRegExpRule))
        
        # delimiter
        brush = QtGui.QBrush( QtCore.Qt.black, QtCore.Qt.SolidPattern )
        pattern = QtCore.QRegExp( "[\)\(]+|[\{\}]+|[][]+" )
        delimiter.setForeground( brush )
        rule = HighlightingRegExpRule( pattern, delimiter )
        self.highlightingRules.append( rule )
        
        # comments      
        brush = QtGui.QBrush(QtGui.QColor("#6aa84f"), QtCore.Qt.SolidPattern)
        comment.setForeground(brush)
        self.highlightingRules.extend([HighlightingRegExpRule("--[^\n]*", comment),
                                       HighlightingRegExpRule("//[^\n]*", comment),
                                       HighlightingRegExpRule("#[^\n]*", comment),])
        
        # Block comments
        self.highlightingRules.extend([HighlightingBlockRule('{-', '-}', comment, BlockState.IN_HSCOMMENT),
                                       HighlightingBlockRule('/*', '*/', comment, BlockState.IN_CCOMMENT),
                                       HighlightingBlockRule('"""', '"""', comment, BlockState.IN_PYCOMMENT),
                                       ])

    def highlightBlock( self, text ):
        prev_block_state = self.previousBlockState()
        block_state = BlockState.NONE
        begin_comment_index = len(text)
        end_comment_index = None
        comment_format = None
        
        for rule in self.highlightingRules:
            if isinstance(rule, HighlightingBlockRule):
                if prev_block_state == rule.expected_state:
                    begin_comment_index = 0
                    if text.lastIndexOf(rule.end) == -1:
                        end_comment_index = len(text)
                        block_state = rule.expected_state
                    else:
                        block_state = BlockState.NONE
                        end_comment_index = text.lastIndexOf(rule.end) + len(rule.end)  
                    comment_format = rule.format
                elif prev_block_state <= BlockState.NONE and text.indexOf(rule.begin) != -1 and text.indexOf(rule.begin) < begin_comment_index:
                    begin_comment_index = text.indexOf(rule.begin)
                    if text.lastIndexOf(rule.end) == -1 or (text.lastIndexOf(rule.end) == text.indexOf(rule.begin) and text.lastIndexOf(rule.end) != -1):
                        end_comment_index = len(text)
                        block_state = rule.expected_state
                    else:
                        end_comment_index = text.lastIndexOf(rule.end) + len(rule.end)
                        block_state = BlockState.NONE        
                    comment_format = rule.format
                else:
                    pass
            elif isinstance(rule, HighlightingRegExpRule):
                expression = QtCore.QRegExp( rule.pattern )
                index = expression.indexIn( text )
                while index >= 0:
                    length = expression.matchedLength()
                    self.setFormat( index, length, rule.format )
                    index = expression.indexIn( text, index + length )
            elif isinstance(rule, HighlightingBasicRule):
                s = rule.text
                index = text.indexOf(s)
                while index >= 0:
                    length = len(s)
                    self.setFormat( index, length, rule.format )
                    index = text.indexOf(s, index + length )
            else:
                assert False
                
        if not comment_format is None:
            self.setFormat(begin_comment_index, end_comment_index, comment_format)
        
        if prev_block_state > BlockState.NONE and block_state <= BlockState.NONE and comment_format is None:
            block_state = prev_block_state
            comment_rule = filter(lambda r: isinstance(r, HighlightingBlockRule) and r.expected_state == block_state, self.highlightingRules)[0]
            self.setFormat(0, len(text), comment_rule.format)
            
        self.setCurrentBlockState(block_state)



class XGobstonesHighlighter(GobstonesHighlighter):
    
    def create_rules(self):
        super(XGobstonesHighlighter, self).create_rules()
        
        # keyword
        brush = QtGui.QBrush( QtGui.QColor("#3c78d8"), QtCore.Qt.SolidPattern )
        keyword_format = QtGui.QTextCharFormat()
        keyword_format.setForeground( brush )
        keyword_format.setFontWeight(QtGui.QFont.Bold)
        keywords = QtCore.QStringList( [ "type", "record", "is", "field", "variant", "case"] )
        
        self.highlightingRules.extend(gen_highlighting_rules(map_regexp(keywords) + ["<-"], keyword_format, HighlightingRegExpRule))
        
        #nativeExpressions
        brush = QtGui.QBrush( QtGui.QColor("#a61c00"), QtCore.Qt.SolidPattern )
        nativeExpression_format = QtGui.QTextCharFormat()
        nativeExpression_format.setForeground( brush )
        nativeExpressions = QtCore.QStringList( [ "head", "tail", "init", "last", "concat", "isEmpty"] )
        
        self.highlightingRules.extend(gen_highlighting_rules(map_regexp(nativeExpressions) + ["\+\+", "\[", "\]"], nativeExpression_format, HighlightingRegExpRule))
    
        