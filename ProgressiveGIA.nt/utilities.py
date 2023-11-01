import csv
from shapely.geometry import shape
from shapely.wkt import loads
import sys

maxInt = sys.maxsize
while True:
    try:
        csv.field_size_limit(maxInt)
        break
    except OverflowError:
        maxInt = int(maxInt/10)

class CsvReader:
    def readAllEntities(delimiter, inputFilePath):
        loadedEntities = []
        geoCollections = 0
        lineCount = 0  # Counter for lines read

        with open(inputFilePath, newline='') as f:
            reader = csv.reader(f, delimiter=delimiter)
            for row in reader:

                try:
                    geometry, *information = [s.split(delimiter)[0] for s in row]
                    geometry = shape(loads(geometry))
                except:
                    print("failed")
                    continue
                if geometry.geom_type == "GeometryCollection":
                    geoCollections += 1
                else:
                    #print(geometry)
                    #print(type(geometry))
                    loadedEntities.append(geometry)

        return loadedEntities
