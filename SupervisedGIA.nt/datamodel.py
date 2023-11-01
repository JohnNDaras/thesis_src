from shapely import relate
from de9im_patterns import contains, crosses_lines, crosses_1, crosses_2, disjoint, equal, intersects, overlaps1, overlaps2, touches, within, covered_by, covers

class RelatedGeometries :
        def __init__(self, qualifyingPairs) :
            self.pgr = 0
            self.exceptions = 0
            self.detectedLinks = 0
            self.verifiedPairs = 0
            self.qualifyingPairs = qualifyingPairs
            self.interlinkedGeometries = 0
            self.continuous_unrelated_Pairs = 0
            self.violations = 0
            self.containsD1 = []
            self.containsD2 = []
            self.coveredByD1 = []
            self.coveredByD2 = []
            self.coversD1 = []
            self.coversD2 = []
            self.crossesD1 = []
            self.crossesD2 = []
            self.equalsD1 = []
            self.equalsD2 = []
            self.intersectsD1 = []
            self.intersectsD2 = []
            self.overlapsD1 = []
            self.overlapsD2 = []
            self.touchesD1 = []
            self.touchesD2 = []
            self.withinD1 = []
            self.withinD2 = []

        def addContains(self, gId1,  gId2) :
          self.containsD1.append(gId1)
          self.containsD2.append(gId2)
        def addCoveredBy(self, gId1,  gId2):
           self.coveredByD1.append(gId1)
           self.coveredByD2.append(gId2)
        def addCovers(self, gId1,  gId2):
           self.coversD1.append(gId1)
           self.coversD2.append(gId2)
        def addCrosses(self, gId1,  gId2) :
          self.crossesD1.append(gId1)
          self.crossesD2.append(gId2)
        def addEquals(self, gId1,  gId2) :
          self.equalsD1.append(gId1)
          self.equalsD2.append(gId2)
        def addIntersects(self, gId1,  gId2) :
          self.intersectsD1.append(gId1)
          self.intersectsD2.append(gId2)
        def addOverlaps(self, gId1,  gId2) :
          self.overlapsD1.append(gId1)
          self.overlapsD2.append(gId2)
        def addTouches(self, gId1,  gId2) :
          self.touchesD1.append(gId1)
          self.touchesD2.append(gId2)
        def addWithin(self, gId1,  gId2) :
          self.withinD1.append(gId1)
          self.withinD2.append(gId2)

        def  getInterlinkedPairs(self) :
            return self.interlinkedGeometries
        def  getNoOfContains(self) :
            return len(self.containsD1)
        def  getNoOfCoveredBy(self) :
            return len(self.coveredByD1)
        def  getNoOfCovers(self) :
            return len(self.coversD1)
        def  getNoOfCrosses(self) :
            return len(self.crossesD1)
        def  getNoOfEquals(self) :
            return len(self.equalsD1)
        def  getNoOfIntersects(self) :
            return len(self.intersectsD1)
        def  getNoOfOverlaps(self) :
            return len(self.overlapsD1)
        def  getNoOfTouches(self) :
            return len(self.touchesD1)
        def  getNoOfWithin(self) :
            return len(self.withinD1)
        def  getVerifiedPairs(self) :
            return self.verifiedPairs

        def print(self) :
            print("Qualifying pairs:\t", str(self.qualifyingPairs))
            print("Exceptions:\t", str(self.exceptions))
            print("Detected Links:\t", str(self.detectedLinks))
            print("Interlinked geometries:\t", str(self.interlinkedGeometries))
            print("No of contains:\t", str(self.getNoOfContains()))
            print("No of covered-by:\t" + str(self.getNoOfCoveredBy()))
            print("No of covers:\t", str(self.getNoOfCovers()))
            print("No of crosses:\t", str(self.getNoOfCrosses()))
            print("No of equals:\t", str(self.getNoOfEquals()))
            print("No of intersects:\t" + str(self.getNoOfIntersects()))
            print("No of overlaps:\t", str(self.getNoOfOverlaps()))
            print("No of touches:\t", str(self.getNoOfTouches()))
            print("No of within:\t", str(self.getNoOfWithin()))

            if self.qualifyingPairs != 0:
              print("Recall", str((self.interlinkedGeometries / float(self.qualifyingPairs))))
            else:
              print('array is empty')
            if self.verifiedPairs != 0:
              print("Precision", str((self.interlinkedGeometries / self.verifiedPairs)))
            else:
              print('array is empty 2')
            if self.qualifyingPairs != 0 and self.verifiedPairs != 0:
              print("Progressive Geometry Recall", str(self.pgr / self.qualifyingPairs / self.verifiedPairs))
            else:
              print('array is empty 3')
            print("Verified pairs", str(self.verifiedPairs))


        def  verifyRelations(self, geomId1,  geomId2,  sourceGeom,  targetGeom) :
            related = False
            array = relate(sourceGeom, targetGeom)
            self.verifiedPairs += 1

            if intersects.matches(array):
                related = True
                self.detectedLinks += 1
                self.addIntersects(geomId1, geomId2)
            if within.matches(array):
                related = True
                self.detectedLinks += 1
                self.addWithin(geomId1, geomId2)
            if covered_by.matches(array):
                related = True
                self.detectedLinks += 1
                self.addCoveredBy(geomId1, geomId2)
            if crosses_lines.matches(array) or crosses_1.matches(array) or crosses_2.matches(array):
                related = True
                self.detectedLinks += 1
                self.addCrosses(geomId1, geomId2)
            if overlaps1.matches(array) or overlaps2.matches(array):
                related = True
                self.detectedLinks += 1
                self.addOverlaps(geomId1, geomId2)
            if  equal.matches(array):
                related = True
                self.detectedLinks += 1
                self.addEquals(geomId1, geomId2)
            if  touches.matches(array):
                related = True
                self.detectedLinks += 1
                self.addTouches(geomId1, geomId2)
            if  contains.matches(array):
                related = True
                self.detectedLinks += 1
                self.addContains(geomId1, geomId2)
            if covers.matches(array):
                related = True
                self.detectedLinks += 1
                self.addCovers(geomId1, geomId2)

            if (related) :
                self.interlinkedGeometries += 1
                self.pgr += self.interlinkedGeometries
                self.continuous_unrelated_Pairs = 0
            else:
                self.continuous_unrelated_Pairs += 1


            return related
