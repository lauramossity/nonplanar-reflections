import cv2
from cv2 import cv
import numpy as np
import Tkinter, tkFileDialog
import random
import itertools
from math import hypot

from PySide import QtCore
from PySide.QtGui import QColor




'''
TODO:
- Add border/offset only when cluster is found
- create an intersectionsCollection class

'''


class LineCollection:

    def __init__(self):
        self.lines = []
        self.intersections = []

    def addLine(self, newLine):
        self.lines.append(newLine)
        self.intersections = self._findIntersections()

    def draw(self, painter, color):
        # TODO: calculate border points for each line, draw a line between those points
        painter.setPen(QColor(color[0], color[1], color[2]))
        for l in self.lines:
            painter.drawLine(l)
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

class PlanarAnalysis:
    # collection of collections of lines, one for each object

    def __init__(self):
        self.lineCollections = []
        self.lineCollections.append(LineCollection())
        self.openCollectionIdx = 0
        self.colors = []
        self.colors.append((random.randint(0,255),random.randint(0,255),random.randint(0,255)))

    # method to start a new collection for a new object in the scene
    def startNewLineCollection(self):
        self.lineCollections.append(LineCollection())
        self.openCollectionIdx += 1
        self.colors.append((random.randint(0,255),random.randint(0,255),random.randint(0,255)))

    def draw(self, painter):
        # draw all lines
        for lc in self.lineCollections:
            lc.draw(painter, self.colors[self.lineCollections.index(lc)])

    def addLine(self, newLine):
        self.lineCollections[self.openCollectionIdx].addLine(newLine)

    def addLine(self, point1, point2):
        newLine = QtCore.QLineF(point1, point2)
        self.lineCollections[self.openCollectionIdx].addLine(newLine)

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
