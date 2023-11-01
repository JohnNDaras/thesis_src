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

class SupervisedGIAnt:

    def __init__(self, budget: int, qPairs: int, delimiter: str, sourceFilePath: str, targetFilePath: str):
        self.CLASS_SIZE = 50
        self.NO_OF_FEATURES = 16
        self.SAMPLE_SIZE = 100
        self.POSITIVE_PAIR = 1
        self.NEGATIVE_PAIR = 0
        self.trainingPhase = False

        self.budget = budget
        self.delimiter = delimiter
        self.sourceData = CsvReader.readAllEntities(delimiter, sourceFilePath)
        print('Source geometries', len(self.sourceData))

        self.targetFilePath = targetFilePath
        self.datasetDelimiter = len(self.sourceData)
        self.relations = RelatedGeometries(qPairs)
        self.sample = []
        self.sample_for_verification = []
        self.spatialIndex = defaultdict(lambda: defaultdict(list))
        self.verifiedPairs = set()
        self.minimum_probability_threshold = 0
        self.thetaX = -1
        self.thetaY = -1

    def applyProcessing(self) :
      time1 = int(time.time() * 1000)
      self.setThetas()
      self.indexSource()
      time2 = int(time.time() * 1000)
      self.preprocessing()
      time3 = int(time.time() * 1000)
      self.trainModel()
      time4 = int(time.time() * 1000)
      self.verification()
      time5 = int(time.time() * 1000)

      print("Indexing Time\t:\t" + str(time2 - time1))
      print("Initialization Time\t:\t" + str(time3 - time2))
      print("Training Time\t:\t" + str(time4 - time3))
      print("Verification Time\t:\t" + str(time5 - time4))
      self.relations.print()

    def indexSource(self) :
      geometryId = 0
      for sEntity in self.sourceData:
        self.addToIndex(geometryId, sEntity.bounds)
        geometryId += 1

    def addToIndex(self, geometryId, envelope) :
        maxX = math.ceil(envelope[2] / self.thetaX)
        maxY = math.ceil(envelope[3] / self.thetaY)
        minX = math.floor(envelope[0] / self.thetaX)
        minY = math.floor(envelope[1] / self.thetaY)

        for latIndex in range(minX, maxX+1):
          for longIndex in range(minY, maxY+1):
              self.spatialIndex[latIndex][longIndex].append(geometryId)

    def preprocessing(self):
        self.flag = [-1] * len(self.sourceData)
        self.frequency = [-1] * len(self.sourceData)
        self.distinctCooccurrences =  [0] * len(self.sourceData)
        self.realCandidates =  [0] * len(self.sourceData)
        self.totalCooccurrences =  [0] * len(self.sourceData)
        self.maxFeatures = [-sys.float_info.max] * self.NO_OF_FEATURES
        self.minFeatures = [sys.float_info.max] * self.NO_OF_FEATURES
        for s in self.sourceData:
            if self.maxFeatures[0] < s.envelope.area:
                self.maxFeatures[0] = s.envelope.area

            if s.envelope.area < self.minFeatures[0]:
                self.minFeatures[0] = s.envelope.area

            no_of_blocks = self.getNoOfBlocks(s.bounds)
            if self.maxFeatures[3] < no_of_blocks:
                self.maxFeatures[3] = no_of_blocks

            if no_of_blocks < self.minFeatures[3]:
                self.minFeatures[3] = no_of_blocks

            no_of_points = self.getNoOfPoints(s)
            if self.maxFeatures[6] < no_of_points:
                self.maxFeatures[6] = no_of_points

            if no_of_points < self.minFeatures[6]:
                self.minFeatures[6] = no_of_points

            if self.maxFeatures[8] < s.length:
                self.maxFeatures[8] = s.length

            if s.length < self.minFeatures[8]:
                self.minFeatures[8] = s.length

        targetData = CsvReader.readAllEntities("\t", self.targetFilePath)

        max_candidate_pairs = self.datasetDelimiter * len(targetData)
        selected_pairs = set(random.sample(range(0, max_candidate_pairs), self.SAMPLE_SIZE))

        targetGeomId, pairId = 0, 0
        for targetGeom in targetData:
            if self.maxFeatures[1] < targetGeom.envelope.area:
                self.maxFeatures[1] = targetGeom.envelope.area

            if targetGeom.envelope.area < self.minFeatures[1]:
                self.minFeatures[1] = targetGeom.envelope.area

            noOfBlocks = self.getNoOfBlocks(targetGeom.bounds)
            if self.maxFeatures[4] < noOfBlocks:
                self.maxFeatures[4] = noOfBlocks

            if noOfBlocks < self.minFeatures[4]:
                self.minFeatures[4] = noOfBlocks

            no_of_points = self.getNoOfPoints(s)
            if self.maxFeatures[7] < no_of_points:
                self.maxFeatures[7] = no_of_points

            if no_of_points < self.minFeatures[7]:
                self.minFeatures[7] = no_of_points

            if self.maxFeatures[9] < targetGeom.length:
                self.maxFeatures[9] = targetGeom.length

            if targetGeom.length < self.minFeatures[9]:
                self.minFeatures[9] = targetGeom.length

            candidateMatches = self.getCandidates(targetGeomId, targetGeom)

            currentCandidates = 0
            currentDistinctCooccurrences = len(candidateMatches)
            currentCooccurrences = 0

            for candidateMatchId in candidateMatches:
              self.distinctCooccurrences[candidateMatchId] += 1
              currentCooccurrences += self.frequency[candidateMatchId]

              self.totalCooccurrences[candidateMatchId] += self.frequency[candidateMatchId]

              if self.validCandidate(candidateMatchId, targetGeom.envelope):
                  currentCandidates += 1
                  self.realCandidates[candidateMatchId] += 1

                  mbrIntersection = self.sourceData[candidateMatchId].envelope.intersection(targetGeom.envelope)

                  if self.maxFeatures[2] < mbrIntersection.area:
                      self.maxFeatures[2] = mbrIntersection.area

                  if mbrIntersection.area < self.minFeatures[2]:
                      self.minFeatures[2] = mbrIntersection.area

                  if self.maxFeatures[5] < self.frequency[candidateMatchId]:
                      self.maxFeatures[5] =  self.frequency[candidateMatchId]

                  if self.frequency[candidateMatchId] < self.minFeatures[5]:
                      self.minFeatures[5] = self.frequency[candidateMatchId]
                  if len(self.sample) < 1000:
                        self.random_number = random.randint(0, 1)
                        if self.random_number == 0:
                          self.sample.append((candidateMatchId, targetGeomId, targetGeom))
                  #Create sample for verification
                  if len(self.sample_for_verification) < 500:
                        if self.random_number == 1:
                          self.sample_for_verification.append((candidateMatchId, targetGeomId, targetGeom))

                  pairId += 1

            if self.maxFeatures[13] < currentCooccurrences:
                self.maxFeatures[13] = currentCooccurrences

            if currentCooccurrences < self.minFeatures[13]:
                self.minFeatures[13] = currentCooccurrences

            if self.maxFeatures[14] < currentDistinctCooccurrences:
                self.maxFeatures[14] = currentDistinctCooccurrences

            if currentDistinctCooccurrences < self.minFeatures[14]:
                self.minFeatures[14] = currentDistinctCooccurrences

            if self.maxFeatures[15] < currentCandidates:
                self.maxFeatures[15] = currentCandidates

            if currentCandidates < self.minFeatures[15]:
                self.minFeatures[15] = currentCandidates

            targetGeomId += 1

        for i in range(self.datasetDelimiter):
            if self.maxFeatures[10] < self.totalCooccurrences[i]:
                self.maxFeatures[10] = self.totalCooccurrences[i]

            if self.totalCooccurrences[i] < self.minFeatures[10]:
                self.minFeatures[10] = self.totalCooccurrences[i]

            if self.maxFeatures[11] < self.distinctCooccurrences[i]:
                self.maxFeatures[11] = self.distinctCooccurrences[i]

            if self.distinctCooccurrences[i] < self.minFeatures[11]:
                self.minFeatures[11] = self.distinctCooccurrences[i]

            if self.maxFeatures[12] < self.realCandidates[i]:
                self.maxFeatures[12] = self.realCandidates[i]

            if self.realCandidates[i] < self.minFeatures[12]:
                self.minFeatures[12] = self.realCandidates[i]

    def getNoOfPoints(self, geometry):
        if isinstance(geometry, Polygon):
            return len(geometry.exterior.coords)
        elif isinstance(geometry, LineString):
            return len(geometry.coords)
        elif isinstance(geometry, MultiPolygon):
            return sum([len(polygon.exterior.coords) for polygon in geometry.geoms])
        else:
            #print(type(geometry))
            #print(geometry)
            return 0

    def getCandidates(self, targetId, targetGeom):
        candidates = set()

        envelope = targetGeom.envelope.bounds
        maxX = math.ceil(envelope[2] / self.thetaX)
        maxY = math.ceil(envelope[3] / self.thetaY)
        minX = math.floor(envelope[0] / self.thetaX)
        minY = math.floor(envelope[1] / self.thetaY)

        for latIndex in range(minX, maxX+1):
          for longIndex in range(minY,maxY+1):
              for sourceId in self.spatialIndex[latIndex][longIndex]:
                  if (self.flag[sourceId] == -1):
                      self.flag[sourceId] = targetId
                      self.frequency[sourceId] = 0
                  self.frequency[sourceId] += 1
                  candidates.add(sourceId)

        return candidates

    def setThetas(self):
        self.thetaX, self.thetaY = 0, 0
        for sEntity in self.sourceData:
            envelope = sEntity.envelope.bounds
            self.thetaX += envelope[2] - envelope[0]
            self.thetaY += envelope[3] - envelope[1]

        self.thetaX /= len(self.sourceData)
        self.thetaY /= len(self.sourceData)
        print("Dimensions of Equigrid", self.thetaX,"and", self.thetaY)

    def validCandidate(self, candidateId, targetEnv):
        return self.sourceData[candidateId].envelope.intersects(targetEnv)

    def trainModel(self):
        self.trainingPhase = True
        random.shuffle(self.sample)
        negativeClassFull, positiveClassFull = False, False
        negativePairs, positivePairs = [], []
        excessVerifications = 0
        for sourceId, targetId, targetGeom in self.sample:
            if negativeClassFull and positiveClassFull:
                break

            isRelated = self.relations.verifyRelations(sourceId, targetId, self.sourceData[sourceId], targetGeom)
            self.verifiedPairs.add((sourceId, targetId))

            if isRelated:
                if len(positivePairs) < self.CLASS_SIZE:
                    positivePairs.append((sourceId, targetId, targetGeom))
                else:
                    excessVerifications += 1
                    positiveClassFull = True
            else:
                if len(negativePairs) < self.CLASS_SIZE:
                    negativePairs.append((sourceId, targetId, targetGeom))
                else:
                    excessVerifications += 1
                    negativeClassFull = True

        print("Excess verifications\t:\t", excessVerifications)
        print("Labelled negative instances\t:\t", len(negativePairs))
        print("Labelled positive instances\t:\t", len(positivePairs))

        X, y = [], []
        for sourceId, targetId, targetGeom in negativePairs:
            X.append(self.get_feature_vector(sourceId, targetId, targetGeom))
            y.append(self.NEGATIVE_PAIR)
        for sourceId, targetId, targetGeom in positivePairs:
            X.append(self.get_feature_vector(sourceId, targetId, targetGeom))
            y.append(self.POSITIVE_PAIR)

        X = np.array(X)
        y = np.array(y)
        if len(negativePairs) == 0 or len(positivePairs) == 0:
            raise ValueError("Both negative and positive instances must be labelled.")
        else:
            self.classifier = LogisticRegression(max_iter=1000)
            self.classifier.fit(X, y)
        self.trainingPhase = False

    def get_feature_vector(self, sourceId, targetId, targetGeom):
        featureVector = [0] * (self.NO_OF_FEATURES)

        if(self.trainingPhase == 1):
          candidateMatches = self.getCandidates(targetId, targetGeom)
          for candidateMatchId in candidateMatches:
            featureVector[13] += self.frequency[candidateMatchId]
            featureVector[14]+=1
            if (self.validCandidate(candidateMatchId, targetGeom.envelope)): # intersecting MBRs
                  featureVector[15]+=1

        mbrIntersection = self.sourceData[sourceId].envelope.intersection(targetGeom.envelope)

        #area-based features
        featureVector[0] = (self.sourceData[sourceId].envelope.area - self.minFeatures[0]) / self.maxFeatures[0] * 10000  # source area
        featureVector[1] = (targetGeom.envelope.area - self.minFeatures[1]) / self.maxFeatures[1] * 10000  # target area
        featureVector[2] = (mbrIntersection.area - self.minFeatures[2]) / self.maxFeatures[2] * 10000  # intersection area

        #grid-based features
        featureVector[3] = (self.getNoOfBlocks(self.sourceData[sourceId].bounds) - self.minFeatures[3]) / self.maxFeatures[3] * 10000 # source blocks
        featureVector[4] = (self.getNoOfBlocks(targetGeom.bounds) - self.minFeatures[4]) / self.maxFeatures[4] * 10000 # source blocks
        featureVector[5] = (self.frequency[sourceId] - self.minFeatures[5]) / self.maxFeatures[5] * 10000 # common blocks

        # boundary-based features
        featureVector[7] = (self.getNoOfPoints(self.sourceData[sourceId]) - self.minFeatures[7]) / self.maxFeatures[7] * 10000 # source boundary points
        featureVector[8] = (self.getNoOfPoints(targetGeom) - self.minFeatures[8]) / self.maxFeatures[8] * 10000 # target boundary points
        featureVector[9] = (targetGeom.length - self.minFeatures[9]) / self.maxFeatures[9] * 10000 # source length
        featureVector[6] = (self.sourceData[sourceId].length - self.minFeatures[6]) / self.maxFeatures[6] * 10000  # target length
        #candidate-based features
        #source geometry
        featureVector[10] = (self.totalCooccurrences[sourceId] - self.minFeatures[10]) / self.maxFeatures[10] * 10000
        featureVector[11] = (self.distinctCooccurrences[sourceId] - self.minFeatures[11]) / self.maxFeatures[11] * 10000
        featureVector[12] = (self.realCandidates[sourceId] - self.minFeatures[12]) / self.maxFeatures[12] * 10000
        #target geometry
        featureVector[13] = (featureVector[13] - self.minFeatures[13]) / self.maxFeatures[13] * 10000
        featureVector[14] = (featureVector[14] - self.minFeatures[14]) / self.maxFeatures[14] * 10000
        featureVector[15] = (featureVector[15] - self.minFeatures[15]) / self.maxFeatures[15] * 10000

        return featureVector

    def getNoOfBlocks(self, envelope) :
      maxX = math.ceil(envelope[2] / self.thetaX)
      maxY = math.ceil(envelope[3] / self.thetaY)
      minX = math.floor(envelope[0] / self.thetaX)
      minY = math.floor(envelope[1] / self.thetaY)
      return (maxX - minX + 1) * (maxY - minY + 1)

    def verification(self):
        Prediction_probs, retainedPairs = [], []
        targetId, totalDecisions, positiveDecisions, truePositiveDecisions = 0, 0, 0, 0
        targetData = CsvReader.readAllEntities("\t", self.targetFilePath)
        for targetGeom in targetData:
          candidateMatches = self.getCandidates(targetId,  targetGeom)

          for candidateMatchId in candidateMatches:
              if (self.validCandidate(candidateMatchId, targetGeom.envelope)):
                if (candidateMatchId, targetId) in self.verifiedPairs:
                  continue

                totalDecisions += 1
                currentInstance = self.get_feature_vector(candidateMatchId, targetId, targetGeom)
                prediction = self.classifier.predict(np.array([currentInstance]))
                if prediction == [1]:
                    positiveDecisions += 1
                    retainedPairs.append((candidateMatchId, targetId, targetGeom))
                Prediction_probs.append(float(self.classifier.predict_proba(np.array([currentInstance]))[:,1]))
          targetId += 1

        counter = len(self.verifiedPairs)
        print("Positive Decisions\t:\t" + str(positiveDecisions))
        print("Total Decisions\t:\t" + str(totalDecisions))
        for sourceId, targetId, targetGeom in retainedPairs:
          isRelated = self.relations.verifyRelations(sourceId, targetId, self.sourceData[sourceId], targetGeom)
          if isRelated:
              truePositiveDecisions += 1
          if (self.budget == counter):
            break
        print("True Positive Decisions\t:\t" + str(truePositiveDecisions))
