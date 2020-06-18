import geopandas as geopd
import matplotlib.pyplot as plt
from shapely.geometry import *
from Simplify import utmconv
import math

line1 = LineString([[0,0],[0,1],[0,2],[2,2],[2,0]])
line2 = LineString([[0,-1],[0,2]])

print(line1.coords[0])

