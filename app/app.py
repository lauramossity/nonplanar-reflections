from sys import maxint, argv, exit

from PySide import QtCore, QtGui


class Canvas(QtGui.QWidget):
    def __init__(self, parent=None):
        super(Canvas, self).__init__(parent)

        self.image = QtGui.QImage()

    def openImage(self, fileName):
        loadedImage = QtGui.QImage()
        if not loadedImage.load(fileName):
            return False

        newSize = loadedImage.size().expandedTo(self.size())
        self.resizeImage(loadedImage, newSize)
        self.image = loadedImage
        #self.modified = False
        self.update()
        return True

    def paintEvent(self, event):
        painter = QtGui.QPainter(self)
        painter.drawImage(QtCore.QPoint(0, 0), self.image)

    def resizeImage(self, image, newSize):
        if image.size() == newSize:
            return

        newImage = QtGui.QImage(newSize, QtGui.QImage.Format_RGB32)
        newImage.fill(QtGui.qRgb(255, 255, 255))
        painter = QtGui.QPainter(newImage)
        painter.drawImage(QtCore.QPoint(0, 0), image)
        self.image = newImage

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

    def createActions(self):
        self.openAct = QtGui.QAction("&Open...", self, shortcut="Ctrl+O",
                triggered=self.open)

    def createMenus(self):
        fileMenu = QtGui.QMenu("&File", self)
        fileMenu.addAction(self.openAct)

        self.menuBar().addMenu(fileMenu)

def main():
    app = QtGui.QApplication(argv)
    window = MainWindow()
    window.show()
    exit(app.exec_())

    #root = Tkinter.Tk()
    #root.withdraw()

    #filename = tkFileDialog.askopenfilename()

    
    '''
    # Reads an image file.  It is stored internally as a matrix.
    image_cat = cv2.imread(filename)
    if image_cat == None:
        print('Error - the file does not exist or is in the wrong place.')
    cv2.imshow('Test image', image_cat)
    cv2.setMouseCallback('Test image', callback, image_cat)
    while(1):
        key = cv2.waitKey(10)
        if key == 27:  # ESC
            break

        elif key == 13: # enter
            #TODO rank by min variance sum and display

            print [str(item) for item in pa._findClusters()]
    '''
    

#------------------------------------------------------------------------
# If this module is running at the top level (as opposed to being
# imported by another module), then call the 'main' function.
#------------------------------------------------------------------------
if __name__ == '__main__':
    main()
