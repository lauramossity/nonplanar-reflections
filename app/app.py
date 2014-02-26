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
        self.resetMetadata()
        self.zoom = 1.0

    def openImage(self, fileName):
        loadedImage = QtGui.QImage()
        if not loadedImage.load(fileName):
            return False

        #newSize = loadedImage.size().expandedTo(self.size())
        #self.resizeImage(loadedImage, newSize)
        self.resize(loadedImage.size())
        mainWindow = self.parentWidget().parentWidget()
        mainWindow.resize(max(loadedImage.size().width(), mainWindow.sizeHint().width()), mainWindow.sizeHint().height() + loadedImage.size().height())
        self.image = loadedImage
        #self.modified = False
        self.resetMetadata()
        self.zoom = 1.0
        self.update()
        return True

    def resetMetadata(self):
        self.setAnalysisMode(AnalysisMode.SPHERICAL)
        self.setToolMode(ToolMode.POINT_MATCHING)
        self.update()

    def paintEvent(self, event):
        painter = QtGui.QPainter(self)
        painter.scale(self.zoom, self.zoom)

        painter.drawImage(QtCore.QPoint(0, 0), self.image)
        self.analysisObject.draw(painter, self.contentsRect())
        for p in self._points:
            painter.drawEllipse(p, 2, 2)

    def mousePressEvent(self, event):
        if event.button() == QtCore.Qt.LeftButton and not self.image.isNull():
            #event.pos
            if self._analysisMode == AnalysisMode.SPHERICAL and self._toolMode == ToolMode.CIRCLE:
                # make circle

                self._points.append(event.pos() / self.zoom)
                # call analysisObject.addCircle() if there are 9 points saved
                if len(self._points) > 8:
                    self.analysisObject.addCircle(self._points, self.image)
                    self._points = []
            elif self._toolMode == ToolMode.POINT_MATCHING:
                # make lines
                if self._points:
                    # there is another point there, so make a line
                    self.analysisObject.addLine(event.pos() / self.zoom, self._points[-1])
                    self._points = []
                else:
                    self._points.append(event.pos() / self.zoom)
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

        if newMode == AnalysisMode.PLANAR:
            self.analysisObject = ReflectionAnalysis.PlanarAnalysis()
        elif newMode == AnalysisMode.SPHERICAL:
            self.analysisObject = ReflectionAnalysis.SphericalAnalysis()
        else:
            print "Error: Undefined analysis mode"

        self._points = []
        self.update()

    def setToolMode(self, newMode):
        self._toolMode = newMode
        self._points = []

    def startNewLineGroup(self):
        self.analysisObject.startNewLineCollection()

    # Modifies plainTextEdit
    def analyze(self, plainTextEdit):
        self.analysisObject.analyze(plainTextEdit)

    def changeZoom(self, change):
        self.zoom += change
        self.resize(self.image.size()*self.zoom)
        self.update()

    def clearCurrentPoints(self):
        self._points = []
        self.update()

    def reset(self):
        self.clearCurrentPoints()
        self.resetMetadata()
        self.setAnalysisMode(self._analysisMode)

    def undoLine(self):
        self.analysisObject.undoLine()
        self.update()

class MainWindow(QtGui.QMainWindow):
    def __init__(self):
        super(MainWindow, self).__init__()

        self.canvas = Canvas()
        self.scrollarea = QtGui.QScrollArea()
        self.scrollarea.setWidget(self.canvas)
        self.setCentralWidget(self.scrollarea)

        self.plainTextEdit = QtGui.QPlainTextEdit()
        self.plainTextEdit.setReadOnly(True)

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
        self.setPointMatchingToolAct.setChecked(True)

    def setToolMode(self, newMode):
        self.canvas.setToolMode(newMode)

    def changeZoom(self, change):
        self.canvas.changeZoom(change)

    def analyze(self):
        self.canvas.analyze(self.plainTextEdit)
        self.plainTextEdit.show()
        self.plainTextEdit.activateWindow()
        self.plainTextEdit.setFocus()
        self.plainTextEdit.selectAll()

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

        self.analyzeAct = QtGui.QAction("Analyze", self, toolTip="Perform an analysis based on the current information.", triggered=self.analyze)

        self.zoomInAct = QtGui.QAction("+", self, toolTip="Zoom in", triggered=partial(self.changeZoom, .02))
        self.zoomOutAct = QtGui.QAction("-", self, toolTip="Zoom out", triggered=partial(self.changeZoom, -.02))

        self.clearCurrentPointsAct = QtGui.QAction("Clear", self, toolTip="Clear the current set of points that are not yet formed into a shape", triggered=self.canvas.clearCurrentPoints, shortcut='C')
        self.resetAct = QtGui.QAction("Reset", self, toolTip="Reset the analysis for the opened image.", triggered=self.canvas.reset)

        self.undoLineAct = QtGui.QAction("Undo Last Line", self, toolTip="Remove the last line created", triggered=self.canvas.undoLine, shortcut='Ctrl+Z')

        # set up initial configuration
        self.setSphereAct.setChecked(True)
        self.setAnalysisMode(AnalysisMode.SPHERICAL)
        self.setPointMatchingToolAct.setChecked(True)
        self.setToolMode(ToolMode.POINT_MATCHING)

    def createMenus(self):
        fileMenu = QtGui.QMenu("&File", self)
        fileMenu.addAction(self.openAct)
        fileMenu.addAction(self.undoLineAct)

        self.menuBar().addMenu(fileMenu)

        toolBar = self.addToolBar("Toolbar")
        toolBar.setMovable(False)

        #for action in self.modeActGrp.actions():
         #   toolBar.addAction(action)

        #toolBar.addSeparator()

        for action in self.mouseToolActGrp.actions():
            toolBar.addAction(action)
        toolBar.addAction(self.newLineGroupAct)

        toolBar.addSeparator()

        toolBar.addAction(self.analyzeAct)

        toolBar.addSeparator()

        toolBar.addAction(self.zoomInAct)
        toolBar.addAction(self.zoomOutAct)

        toolBar.addSeparator()

        toolBar.addAction(self.clearCurrentPointsAct)
        toolBar.addAction(self.resetAct)

def main():
    app = QtGui.QApplication(argv)
    window = MainWindow()
    window.show()
    exit(app.exec_())
    

#------------------------------------------------------------------------
# If this module is running at the top level (as opposed to being
# imported by another module), then call the 'main' function.
#------------------------------------------------------------------------
if __name__ == '__main__':
    main()
