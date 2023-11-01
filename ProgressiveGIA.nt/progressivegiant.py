import math
import numpy as np
import random
import sys
import time
import pandas as pd
from collections import defaultdict
from sklearn.linear_model import LogisticRegression
from shapely.geometry import LineString, MultiPolygon, Polygon
from sklearn.neighbors import KernelDensity
from sklearn.model_selection import GridSearchCV
from sklearn.model_selection import LeaveOneOut
from utilities import CsvReader
from datamodel import RelatedGeometries
from queue import PriorityQueue

class ProgressiveGIAnt :

    def __init__(self, budget,  qPairs,  delimiter,  sourceFilePath,  targetFilePath, wScheme) :
        self.budget = budget
        self.datasetDelimiter = len(sourceFilePath)
        self.delimiter = delimiter
        self.relations = RelatedGeometries(qPairs)
        self.sourceData = CsvReader.readAllEntities(delimiter, sourceFilePath)
        self.spatialIndex = defaultdict(lambda: defaultdict(list))
        self.targetFilePath = targetFilePath
        self.thetaX = -1
        self.thetaY = -1
        self.wScheme = wScheme

    def getMethodName(self):
      return 'progressive GIA.nt'


    def addToIndex(self, geometryId, envelope) :
        maxX = math.ceil(envelope[2] / self.thetaX)
        maxY = math.ceil(envelope[3] / self.thetaY)
        minX = math.floor(envelope[0] / self.thetaX)
        minY = math.floor(envelope[1] / self.thetaY)

        for latIndex in range(minX, maxX):
          for longIndex in range(minY, maxY):
              self.spatialIndex[latIndex][longIndex].append(geometryId)

    def applyProcessing(self) :
      time1 = int(time.time() * 1000)

      self.filtering()

      time2 = int(time.time() * 1000)

      self.initialization()

      time3 = int(time.time() * 1000)

      self.verification()

      time4 = int(time.time() * 1000)
      self.indexingTime = time2 - time1;
      self.initializationTime = time3 - time2;
      self.verificationTime = time4 - time3;
      self.printResults()

    def filtering(self):
        self.setThetas()
        self.indexSource()



    def getCandidates(self, targetId, tEntity):
        candidates = set()

        envelope = tEntity.envelope.bounds
        maxX = math.ceil(envelope[2] / self.thetaX)
        maxY = math.ceil(envelope[3] / self.thetaY)
        minX = math.floor(envelope[0] / self.thetaX)
        minY = math.floor(envelope[1] / self.thetaY)

        for latIndex in range(minX, maxX):
          for longIndex in range(minY,maxY):
              for sourceId in self.spatialIndex[latIndex][longIndex]:
                  if (self.flag[sourceId] == -1):
                      self.flag[sourceId] = targetId
                      self.freq[sourceId] = 0
                  self.freq[sourceId] += 1
                  candidates.add(sourceId)

        return candidates




    def getNoOfBlocks(self,envelope) :
      maxX = math.ceil(envelope[2] / self.thetaX)
      maxY = math.ceil(envelope[3] / self.thetaY)
      minX = math.floor(envelope[0] / self.thetaX)
      minY = math.floor(envelope[1] / self.thetaY)
      return (maxX - minX + 1) * (maxY - minY + 1)

    def getWeight(self,sourceId, tEntity) :
      commonBlocks = self.freq[sourceId]
      if self.wScheme == 'CF':
        return commonBlocks
      elif self.wScheme == 'JS_APPROX':
        return commonBlocks / (self.getNoOfBlocks(self.sourceData[sourceId].envelope) + self.getNoOfBlocks(tEntity.envelope) - commonBlocks)
      elif self.wScheme == 'MBR':
        srcEnv = self.sourceData[sourceId].envelope
        trgEnv = tEntity.envelope
        mbrIntersection = srcEnv.intersection(trgEnv);
        denominator = srcEnv.area + trgEnv.area - mbrIntersection.area
        if denominator == 0 :
          return 0
        return mbrIntersection.area/denominator
      return 1.0

    def indexSource(self) :
      geometryId = 0
      for sEntity in self.sourceData:
        self.addToIndex(geometryId, sEntity.bounds)
        geometryId += 1

    def validCandidate(self, candidateId, targetEnv):
        return self.sourceData[candidateId].envelope.intersects(targetEnv)

    def initialization(self): # reads target geometries on the fly
        self.flag = [-1] * len(self.sourceData)
        self.freq = [-1] * len(self.sourceData)
        self.topKPairs = PriorityQueue(maxsize = self.budget + 1)

        geoCollections = 0
        minimumWeight = -1
        targetId, totalDecisions, positiveDecisions, truePositiveDecisions = 0, 0, 0, 0
        targetData = CsvReader.readAllEntities("\t", self.targetFilePath)

        for targetGeom in targetData:
          candidates = self.getCandidates(targetId,targetGeom)
          for candidateMatchId in candidates:
                    if (self.validCandidate(candidateMatchId, targetGeom.envelope)):
                        weight = self.getWeight(candidateMatchId, targetGeom)
                        if (minimumWeight <= weight):
                          self.topKPairs.put((weight, candidateMatchId, targetId, targetGeom))
                          if (self.budget < self.topKPairs.qsize()):
                              minimumWeight = self.topKPairs.get()[0]
          targetId += 1
        print("Total target geometries", targetId)

    def printResults(self) :
      print("\n\nCurrent method", str(self.getMethodName()))
      print("Indexing Time", str(self.indexingTime))
      print("Initialization Time", str(self.initializationTime))
      print("Verification Time", str(self.verificationTime))
      self.relations.print()


    def setThetas(self):
        self.thetaX, self.thetaY = 0, 0
        for sEntity in self.sourceData:
            envelope = sEntity.envelope.bounds
            self.thetaX += envelope[2] - envelope[0]
            self.thetaY += envelope[3] - envelope[1]
        self.thetaX /= len(self.sourceData)
        self.thetaY /= len(self.sourceData)
        print("Dimensions of Equigrid", self.thetaX,"and", self.thetaY)




    def verification(self):
        counter = 0
        while(not self.topKPairs.empty()):
            counter += 1
            weight, source_id, target_id, tEntity = self.topKPairs.get()
            self.relations.verifyRelations(source_id, target_id, self.sourceData[source_id], tEntity)
        print("counter is", counter)


