from sys import maxint, argv, exit
from functools import partial
from PySide import QtCore, QtGui

import ReflectionAnalysis

class AnalysisMode:
    PLANAR = 1
    SPHERICAL = 2

class ToolMode:
    POINT_MATCHING = 1
    CIRCLE = 2

class Canvas(QtGui.QWidget):
    def __init__(self, parent=None):
        super(Canvas, self).__init__(parent)

        self.image = QtGui.QImage()
        self._analysisMode = 0
        self._toolMode = 0
        self._points = []

        self.analysisObject = ReflectionAnalysis.PlanarAnalysis()

    def openImage(self, fileName):
        loadedImage = QtGui.QImage()
        if not loadedImage.load(fileName):
            return False

        newSize = loadedImage.size().expandedTo(self.size())
        self.resizeImage(loadedImage, newSize)
        self.image = loadedImage
        #self.modified = Fal
        self.update()
        return True

    def paintEvent(self, event):
        painter = QtGui.QPainter(self)
        painter.drawImage(QtCore.QPoint(0, 0), self.image)
        self.analysisObject.draw(painter)

    def mousePressEvent(self, event):
        if event.button() == QtCore.Qt.LeftButton and not self.image.isNull():
            #event.pos
            if self._analysisMode == AnalysisMode.SPHERICAL and self._toolMode == ToolMode.CIRCLE:
                # make circle
                print "Circle: Not yet iimplemented"
            elif self._toolMode == ToolMode.POINT_MATCHING:
                # make lines
                if self._points:
                    # there is another point there, so make a line
                    self.analysisObject.addLine(event.pos(), self._points[-1])
                    self._points = []
                else:
                    self._points.append(event.pos())
                print "appending", event.pos()
            else:
                print "Invalid input configuration"

            self.update()

    def resizeImage(self, image, newSize):
        if image.size() == newSize:
            return

        newImage = QtGui.QImage(newSize, QtGui.QImage.Format_RGB32)
        newImage.fill(QtGui.qRgb(255, 255, 255))
        painter = QtGui.QPainter(newImage)
        painter.drawImage(QtCore.QPoint(0, 0), image)
        self.image = newImage

    def setAnalysisMode(self, newMode):
        self._analysisMode = newMode
        self._points = []

    def setToolMode(self, newMode):
        self._toolMode = newMode
        self._points = []

    def startNewLineGroup(self):
        self.analysisObject.startNewLineCollection()

class MainWindow(QtGui.QMainWindow):
    def __init__(self):
        super(MainWindow, self).__init__()

        self.canvas = Canvas()
        self.setCentralWidget(self.canvas)

        self.createActions()
        self.createMenus()

        self.setWindowTitle("Image Reflection Analyzer")

    def open(self):
        fileName, filters = QtGui.QFileDialog.getOpenFileName(self, "Open File",
                QtCore.QDir.currentPath())
        if fileName:
            self.canvas.openImage(fileName)

    # can only be called after initializing actions in createActions
    def setAnalysisMode(self, newMode):
        self.canvas.setAnalysisMode(newMode)

        if newMode == AnalysisMode.SPHERICAL:
            self.setCircleToolAct.setEnabled(True)
        else:
            self.setCircleToolAct.setEnabled(False)
        
        self.canvas.setToolMode(ToolMode.POINT_MATCHING)

    def setToolMode(self, newMode):
        self.canvas.setToolMode(newMode)

    def createActions(self):
        self.openAct = QtGui.QAction("&Open...", self, shortcut="Ctrl+O",
                triggered=self.open)

        # create analysis mode switching actions
        self.modeActGrp = QtGui.QActionGroup(self)
        self.setPlanarAct = QtGui.QAction("Planar", self.modeActGrp, toolTip="Set Planar Mirror Mode", checkable=True, triggered=partial(self.setAnalysisMode, AnalysisMode.PLANAR))
        self.setSphereAct = QtGui.QAction("Spherical", self.modeActGrp, toolTip="Set Spherical Mirror Mode", checkable=True, triggered=partial(self.setAnalysisMode, AnalysisMode.SPHERICAL))

        # create tool switching actions
        self.mouseToolActGrp = QtGui.QActionGroup(self)
        self.setPointMatchingToolAct = QtGui.QAction("Match Points", self.mouseToolActGrp, toolTip="Set Point Matching Mode", checkable=True, triggered=partial(self.setToolMode, ToolMode.POINT_MATCHING))
        self.setCircleToolAct = QtGui.QAction("Find Circle", self.mouseToolActGrp, toolTip="Set Circle Finding Mode", checkable=True, triggered=partial(self.setToolMode, ToolMode.CIRCLE))

        self.newLineGroupAct = QtGui.QAction("New Line Group", self, toolTip="Start a new group of lines. Use this when starting to analyze another object in the scene.", triggered=self.canvas.startNewLineGroup)

        # set up initial configuration
        self.setPlanarAct.setChecked(True)
        self.setAnalysisMode(AnalysisMode.PLANAR)
        self.setPointMatchingToolAct.setChecked(True)
        self.setToolMode(ToolMode.POINT_MATCHING)

    def createMenus(self):
        fileMenu = QtGui.QMenu("&File", self)
        fileMenu.addAction(self.openAct)

        self.menuBar().addMenu(fileMenu)

        toolBar = self.addToolBar("Toolbar")
        toolBar.setMovable(False)

        for action in self.modeActGrp.actions():
            toolBar.addAction(action)

        toolBar.addSeparator()

        for action in self.mouseToolActGrp.actions():
            toolBar.addAction(action)
        toolBar.addAction(self.newLineGroupAct)

def main():
    app = QtGui.QApplication(argv)
    window = MainWindow()
    window.show()
    exit(app.exec_())

    #root = Tkinter.Tk()
    #root.withdraw()

    #filename = tkFileDialog.askopenfilename()
    

#------------------------------------------------------------------------
# If this module is running at the top level (as opposed to being
# imported by another module), then call the 'main' function.
#------------------------------------------------------------------------
if __name__ == '__main__':
    main()
