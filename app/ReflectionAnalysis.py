import cv2
from cv2 import cv
import numpy as np
import Tkinter, tkFileDialog
import random
import itertools
from math import hypot, sqrt, floor

from PySide import QtCore
from PySide.QtGui import QColor

from abc import ABCMeta, abstractmethod

from scipy.optimize import fsolve




# http://stackoverflow.com/questions/18406149/pyqt-pyside-how-do-i-convert-qimage-into-opencvs-mat-format
def convertQImageToMat(incomingImage):
    '''  Converts a QImage into an opencv MAT format  '''

    incomingImage = incomingImage.convertToFormat(4)

    width = incomingImage.width()
    height = incomingImage.height()

    ptr = incomingImage.bits()
    ptr.setsize(incomingImage.byteCount())
    arr = np.array(ptr).reshape(height, width, 4)  #  Copies the data
    return arr

# Find the intersection points between a QLine and a QRect
def intersectLineRect(line, rect):
    x1, y1, x2, y2 = rect.getCoords()

    toReturn = []

    rectLines = []
    rectLines.append(QtCore.QLineF(x1, y1, x2, y1))
    rectLines.append(QtCore.QLineF(x1, y1, x1, y2))
    rectLines.append(QtCore.QLineF(x2, y1, x2, y2))
    rectLines.append(QtCore.QLineF(x1, y2, x2, y2))

    for l in rectLines:
        intersectType, intersectionPoint = line.intersect(l)
        if intersectType != QtCore.QLineF.NoIntersection and rect.contains(intersectionPoint.toPoint()):
            toReturn.append(intersectionPoint)

    return toReturn

def minDistance(point, line):
    p = np.array(point.toTuple())
    a = np.array(line.p1().toTuple())
    unit = line.unitVector()
    n = np.array([unit.dx(), unit.dy()])

    return np.linalg.norm((a - p) - np.dot((a-p), n) * n)

class LineCollection:

    def __init__(self):
        self.lines = []
        self.intersections = []

    def addLine(self, newLine):
        self.lines.append(newLine)
        self.intersections = self._findIntersections()

    def undoLine(self):
        if self.lines:
            self.lines.pop()
            self.intersection = self._findIntersections()

    def draw(self, painter, borderRect, color):
        # TODO: calculate border points for each line, draw a line between those points
        painter.setPen(color)
        for l in self.lines:
            borderPoints = intersectLineRect(l, borderRect)
            painter.drawLine(borderPoints[0], borderPoints[1]) # Unsafe, may not return this many points
            painter.drawEllipse(l.p1(), 2, 2)
            painter.drawEllipse(l.p2(), 2, 2)

    def _findIntersections(self):        
        toReturn = []
        if len(self.lines) > 1:
            for i in self.lines:
                for j in self.lines[self.lines.index(i)+1:]:
                    intersectType, intersectionPoint = i.intersect(j)
                    if intersectType != QtCore.QLineF.NoIntersection:
                        toReturn.append(intersectionPoint)
        return toReturn

class AnalysisResult:
    numClusters = 0
    distanceSums = []
    originalIndices = []
    def __init__(self, clusters, distanceSums, indices):
        self.numClusters = clusters
        self.distanceSums = distanceSums
        self.originalIndices = indices

    def __repr__(self):
        return str("Number of clusters: %d, Distance sums: %s, Original indices: %s" % (self.numClusters, self.distanceSums, self.originalIndices))

class AbstractAnalysis:
    __metaclass__ = ABCMeta

    # collection of collections of lines, one for each object

    def __init__(self):
        self.lineCollections = []
        self.openCollectionIdx = -1
        self.colors = []
        self.startNewLineCollection()

    # method to start a new collection for a new object in the scene
    def startNewLineCollection(self):
        self.lineCollections.append(LineCollection())
        self.openCollectionIdx += 1
        newColor = QColor()
        # http://martin.ankerl.com/2009/12/09/how-to-create-random-colors-programmatically/
        '''
        rand = random.random()
        rand += 0.618033988749895
        rand %= 1
        '''
        phi = 0.618033988749895
        hue = self.openCollectionIdx * phi - floor(self.openCollectionIdx * phi)
        newColor.setHsv(int(hue*256), 120 + int(random.random()*(240-120+1)), 242)
        self.colors.append(newColor)

    def draw(self, painter, borderRect):
        # draw all lines
        for lc in self.lineCollections:
            lc.draw(painter, borderRect, self.colors[self.lineCollections.index(lc)])

    def addLine(self, newLine):
        self.lineCollections[self.openCollectionIdx].addLine(newLine)

    def addLine(self, point1, point2):
        newLine = QtCore.QLineF(point1, point2)
        self.lineCollections[self.openCollectionIdx].addLine(newLine)

    def undoLine(self):
        self.lineCollections[self.openCollectionIdx].undoLine()

    @abstractmethod
    def analyze(self):
        pass


class PlanarAnalysis(AbstractAnalysis):

    
    # method to return likely clusters and whether or not at least one deviates
    # perform k-means for k = number of objects to 1
    # calculate variance from centroids?
    def _findClusters(self):
        toReturn = []

        intersectionsCollection = [(lc.intersections, (self.lineCollections.index(lc),)) for lc in self.lineCollections]
        centroids = [np.mean(ic[0], axis=0) for ic in intersectionsCollection]

        for i in xrange(len(self.lineCollections), 0, -1):
            if i < len(self.lineCollections): # combine the two closest centroids
                toCombine = self._findIndicesWithMinDistance(centroids)

                # remove the items to be combined from intersectionsCollection
                item1 = intersectionsCollection[toCombine[0]]
                item2 = intersectionsCollection[toCombine[1]]

                del intersectionsCollection[max(toCombine)]
                del intersectionsCollection[min(toCombine)]

                # add combined list and indices of collections that were combined
                intersectionsCollection.append((item1[0] +item2[0], item1[1] + item2[1]))

                # recalculate centroids
                centroids = [np.mean(ic[0], axis=0) for ic in intersectionsCollection]

            # calculate the sum of the distances from the centroid to the points, put in result
            # todo: calculate variance for more than one collection
            #for idx in range(len(intersectionsCollection)):
            distanceSums = [sum( [hypot(point[0]-centroids[idx][0],  point[1]-centroids[idx][1]) for point in intersectionsCollection[idx][0] ]) for idx in range(len(intersectionsCollection))]
            toReturn.append(AnalysisResult(i, distanceSums, [ic[1] for ic in intersectionsCollection]))
        toReturn.sort(key=lambda x: sum(x.distanceSums))
        return toReturn

    def _findIndicesWithMinDistance(self, collection):

        # Used to find the indices of the closest two centroids
        # minSoFar = maxint
        # indices = (-1, -1)
        idxs = itertools.combinations(xrange(len(collection)), 2)

        def hypotIdx(iIdx, jIdx):
            i = collection[iIdx]
            j = collection[jIdx]
            return hypot(i[0] - j[0], i[1] - j[1])

        minidx = min(idxs, key=lambda x: hypotIdx(*x))

        # for iidx in xrange(len(collection)):
        #     i = collection[iidx]
        #     for jidx in xrange(iidx+1,len(collection)):
        #         j = collection[jidx]
        #         print "i, j", i, j
        #         dist = hypot(i[0] - j[0], i[1] - j[1])
        #         if dist < minSoFar:
        #             minSoFar = dist
        #             indices = (collection.index(i), collection.index(j))

        print minidx
        return minidx

    def analyze(self):
        raise NotImplementedError


class SphericalAnalysis(AbstractAnalysis):
    def __init__(self):
        # TODO: add a circle representation
        super(SphericalAnalysis, self).__init__()

        self.center = QtCore.QPointF(0,0)
        self.radius = 0
        self.circlePoints = []

    def draw(self, painter, borderRect):
        super(SphericalAnalysis, self).draw(painter, borderRect)
        if self.radius != 0:
            painter.setPen(QColor(255, 0, 0))
            painter.drawEllipse(self.center, self.radius, self.radius)
            for p in self.circlePoints:
                painter.drawEllipse(p, 2, 2)
            painter.drawEllipse(self.center,2,2)

    def solveCircle(self, points):
        # ax + by + c = x^2 + y^2
        Alist = []
        blist = []
        for point in points:
            Alist.append([point.x(), point.y(), 1])
            blist.append([-(point.x()**2+point.y()**2)])
        #A = np.array([[point1.x(),point1.y(),1], [point2.x(),point2.y(),1], [point3.x(),point3.y(),1]])
        #b = np.array([[-(point1.x()**2+point1.y()**2)], [-(point2.x()**2+point2.y()**2)], [-(point3.x()**2+point3.y()**2)]])
        #solution = np.linalg.solve(A,b)
        A = np.array(Alist)
        b = np.array(blist)
        rawSolution = np.linalg.lstsq(A,b)
        solution = rawSolution[0]

        print "Residuals:", rawSolution[1]

        h = solution[0,0] / -2  # h = -a/2
        k = solution[1,0] / -2  # k = -b/2

        r = sqrt(h**2 + k**2 - solution[2,0]) # r^2 = h^2 + k^2 - f

        return h, k, r

    def addCircle(self, argPoints, image):

        h, k, r = self.solveCircle(argPoints)

        self.center.setX(h)
        self.center.setY(k)
        self.radius = r
        self.circlePoints = argPoints

        # Improve the points picked using simple edge detection
        # For each point picked:
        newPoints = []

        for point in self.circlePoints:

            # Aggregate candidates for a new point by finding contiguous points towards and away from the center obtained previously
            newPointCandidates = []
            restrictionLine = QtCore.QLineF(point, self.center)
            slopeVector = QtCore.QPointF()
            if restrictionLine.dx() == 0:
                slopeVector.setX(0)
                slopeVector.setY(1)
            elif abs(restrictionLine.dy()) > abs(restrictionLine.dx()):
                slopeVector.setX(restrictionLine.dx() / restrictionLine.dy())
                slopeVector.setY(1)
            else:
                slopeVector.setX(1)
                slopeVector.setY(restrictionLine.dy() / restrictionLine.dx())

            for i in range(-5, 5):
                if i == 0:
                    newPointCandidates.append(point)
                    continue
                diff = i * slopeVector
                newPointCandidates.append(point + QtCore.QPoint(round(diff.x()), round(diff.y())))

            print newPointCandidates

            # Take the difference between each point and the next point
            absdiff = []
            for j in range(len(newPointCandidates) - 1): # for all points except the last one
                absdiff.append(abs(image.pixel(newPointCandidates[j])-image.pixel(newPointCandidates[j+1])))

            # replace the old point with the spot in between the two pixels with the max difference
            maxdiff, idx = max( (v, i) for i, v in enumerate(absdiff) )
            print "maxdiff: %f" % maxdiff
            if maxdiff != 0:
                newPoints.append((newPointCandidates[idx] + newPointCandidates[idx+1]) / 2)
            else:
                newPoints.append(QtCore.QPointF(point))
            
            '''
            region = image.copy(point.x() - 10, point.y() - 10, 21, 21)
            matRegion = convertQImageToMat(region)
            '''

        self.circlePoints = newPoints
        h, k, r = self.solveCircle(newPoints)

        print "Center shifted by", self.center.x() - h, self.center.y() - k

        self.center.setX(h)
        self.center.setY(k)
        self.radius = r


        # Make a list of the points within 10px of the picked point along the radial of the detected center
        # Find the differences between the points in the list and pick the max as the new point


        #Redo circle solution with new points

    def analyze(self):
        # For each line group, figure out if each line goes through the center of the circle or close to it.
        i = 1
        for lc in self.lineCollections:
            print "Line Collection %s" % i
            i += 1
            for line in lc.lines:
                print minDistance(self.center, line)
