from PyQt5.QtGui import *
from PyQt5.QtCore import *
from PyQt5.QtWidgets import *

class AddPointCommand(QUndoCommand):
    def __init__(self, canvas, pos):
        super().__init__()
        self.canvas = canvas
        self.pos = pos
        
    def undo(self):
        if self.canvas.current is not None:
            self.canvas.current.popPoint()    
        else:
            self.canvas.undoLastLine()
            self.canvas.setEditing(False)
            
        if len(self.canvas.line) > 0 and len(self.canvas.current.points) > 0:
            self.canvas.line[0] = self.canvas.current.points[-1]
        self.canvas.update()  
        
    def redo(self):
        self.canvas.current.addPoint(self.pos)
        
        
class AddShapeCommand(QUndoCommand):
    def __init__(self, canvas, shape):
        super().__init__()
        
    def undo(self):
        pass 
        
    def redo(self):
        pass


class AddEraserCommand(QUndoCommand):
    def __init__(self, canvas):
        super().__init__()
        self.canvas = canvas
        self.image_np = canvas.image_np.copy()
        self.points = canvas.erasing_points.copy()

    def undo(self):
        self.canvas.image_np =  self.image_np.copy()
        self.canvas.show_numpy_image()

    def redo(self):
        self.canvas.erasing(self.points)



class AddCropCommand(QUndoCommand):
    def __init__(self, canvas, reverse):
        super().__init__()
        self.canvas = canvas
        self.image_np = canvas.image_np.copy()
        self.reverse = reverse

    def undo(self):
        self.canvas.image_np = self.image_np.copy()
        self.canvas.show_numpy_image()

    def redo(self):
        self.canvas.image_crop(self.reverse)