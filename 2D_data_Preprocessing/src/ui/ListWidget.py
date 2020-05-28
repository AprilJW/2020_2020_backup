from PyQt5.Qt import *

FONT_SELECTED = QFont("Times", 9, QFont.Bold)
FONT_NORMAL = QFont("Times", 9, QFont.Normal)
        
class ListWidget(QListWidget):
    def __init__(self, parent = None):
        QListWidget.__init__(self, parent)
        
    def setRowSelected(self, row, selected = True):
        if selected:
            self.item(row).setFont(FONT_SELECTED)
        else:
            self.item(row).setFont(FONT_NORMAL)
        
    def setItemSelected(self, item, selected = True):
        if selected:
            item.setFont(FONT_SELECTED)
        else:
            item.setFont(FONT_NORMAL)
        
    def clearSelection(self):
        for i in range(self.count()):
            self.item(i).setFont(FONT_NORMAL)
            
    def getItem(self, text):
        items = self.findItems(text, Qt.MatchExactly)
        if len(items) == 0:
            return None
        else:
            return items[0]