import json

from qgis.core import  QgsGeometry, QgsCoordinateReferenceSystem, QgsPoint, QgsCoordinateTransform, QgsProject


def coord_transform(points):
    tr_points = {}

    for i in points.keys():
        lon = float(points[i].split()[1][1:])
        lat = float(points[i].split()[2][:-1])
        source = int(points[i].split()[0].split(';')[0][5:])

        geom = QgsGeometry(QgsPoint(lon, lat))
        sourceCRS = QgsCoordinateReferenceSystem(source)
        targetCRS = QgsCoordinateReferenceSystem(31254)
        tr = QgsCoordinateTransform(sourceCRS, targetCRS, QgsProject.instance())
        geom.transform(tr)

        tr_points[i] = geom.asPoint()

    return tr_points

class jsonImport():

    def __init__(self, json_path):
        self.json_path = json_path

        self.__readJSON()
        self.iid = [i['iid'] for i in self.data]

        self.__set_ori()
        self.__set_pos()
    
    def __readJSON(self):
        with open(self.json_path, 'r') as f:
            self.data = json.load(f)

    def __set_ori(self):
        self.ori = {}
        for i,j in enumerate(self.iid):
            self.ori[j] = {'alpha':float(self.data[i]['alpha']), 'beta':float(self.data[i]['beta']), 'gamma':float(self.data[i]['gamma'])}

    def __set_pos(self):
        self.pos = {}
        altitude = {}
        points = {}
        tr_points = {}

        for i,j in enumerate(self.iid):
            points[j] = self.data[i]['geom']
            altitude[j] = float(self.data[i]['altitude'])
        
        tr_points = coord_transform(points)

        for i in self.iid:
            self.pos[i] = {'X0':tr_points[i].x(), 'Y0':tr_points[i].y(), 'Z0':altitude[i]}
        

    def get_ori(self):
        return self.ori

    def get_pos(self):
        return self.pos
    
    def get_iid(self):
        return self.iid

    def printJSON(self):
        for i in self.data:
            print(i)

