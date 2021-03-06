import sys


try:
    import gdal
    import ogr
    #from iobjectspy.data import GeoRegion, Point2D
    from Simplify import utmconv
    from osr import CoordinateTransformation
    from osr import SpatialReference
    from Simplify import Douglas
    import numpy as np
    from shapely.geometry import *
    import geopandas as geopd
    import matplotlib.pyplot as plt
except:
    print(Exception.message)
    sys.exit()


# read shapefile with gdal
def gdal_readfile(file_path):
    """
    :param file_path:
    :return:
    """
    driver = ogr.GetDriverByName("ESRI Shapefile")
    data = driver.Open(file_path,0)

    return data

#extract points of polygon，and fill the polygon
def extract_polygon_points(gdl_data):
    """
    :param gdl_data:
    :param area_threshold:
    :return:
    """
    # read layers

    layer = gdl_data.GetLayer()

    polygon_info = layer.GetNextFeature()
    #value of shp type
    val = polygon_info.GetFieldAsInteger("TYPE")

    wgs84_all_points_list = []
    utm_all_points_list = []
    line_type_flag = []
    geometry_polygon = polygon_info.GetGeometryRef()


    # extract polygon boundary
    bounds = geometry_polygon.GetBoundary()
    geometry_name = bounds.GetGeometryName()
    if val == 255:

        # judge the boundary type
        if geometry_name == "MULTILINESTRING":
            utm_multiline = []
            wgs84_multiline = []
            for line in list(bounds):
                multiline_points = line.GetPoints()
                utm_line = []


                for point in multiline_points:
                    #wgs84 to utm
                    x, y = utmconv.latlon2utmxy(utmconv.deg2rad(point[0]), utmconv.deg2rad(point[1]), 50)
                    utm_line.append([x,y])

                # overlapping polygon area compares with area_threshold
                #if compute_polygon_area(utm_line) > area_threshold:
                utm_multiline.append(utm_line)
                wgs84_multiline.append(multiline_points)
            wgs84_all_points_list.append(wgs84_multiline)
            utm_all_points_list.append(utm_multiline)
            line_type_flag.append(0)

        else:
            line_points = bounds.GetPoints()
            utm_line = []
            for point in line_points:
                # wgs84 to utm
                x, y = utmconv.latlon2utmxy(utmconv.deg2rad(point[0]), utmconv.deg2rad(point[1]), 50)
                utm_line.append([x, y])
            # non-overlapping polygon area compares with area_threshold( first or second)
            #if compute_polygon_area(bounds) > area_threshold:
            wgs84_all_points_list.append(line_points)
            utm_all_points_list.append(utm_line)
            line_type_flag.append(1)


    while polygon_info is not None:

        try:
            polygon_info_next = layer.GetNextFeature()
            val = polygon_info_next.GetFieldAsInteger("TYPE")

            if val == 255:
                geometry_polygon_next = polygon_info_next.GetGeometryRef()
                bounds = geometry_polygon_next.GetBoundary()
                geometry_name = bounds.GetGeometryName()

                # judge the boundary type
                if geometry_name == "MULTILINESTRING":
                    utm_multiline = []
                    wgs84_multiline = []
                    for line in list(bounds):
                        multiline_points = line.GetPoints()
                        utm_line = []

                        for point in multiline_points:
                            # wgs84 to utm
                            x, y = utmconv.latlon2utmxy(utmconv.deg2rad(point[0]), utmconv.deg2rad(point[1]), 50)
                            utm_line.append([x, y])

                        # overlapping polygon area compares with area_threshold
                        # if compute_polygon_area(utm_line) > area_threshold:
                        utm_multiline.append(utm_line)
                        wgs84_multiline.append(multiline_points)

                    wgs84_all_points_list.append(wgs84_multiline)
                    utm_all_points_list.append(utm_multiline)
                    line_type_flag.append(0)
                else:
                    line_points = bounds.GetPoints()
                    utm_line = []
                    for point in line_points:
                        # wgs84 to utm
                        x, y = utmconv.latlon2utmxy(utmconv.deg2rad(point[0]), utmconv.deg2rad(point[1]), 50)
                        utm_line.append([x, y])

                    #non-overlapping polygon area compares with area_threshold( first or second)
                    # if compute_polygon_area(bounds) > area_threshold:
                    wgs84_all_points_list.append(line_points)
                    utm_all_points_list.append(utm_line)
                    line_type_flag.append(1)

        except Exception as e:

            break


    return wgs84_all_points_list, utm_all_points_list,line_type_flag

#compute polygon area
def compute_polygon_area(polygon_points):
    """
    :param geometry:
    :return: area of polygon
    """
    wkt = "LINESTRING ("
    for point in polygon_points:
        wkt += str(point[0]) + " " + str(point[1]) + ","
    wkt = wkt[:-1] + ")"
    geometry = ogr.CreateGeometryFromWkt(wkt)
    return ogr.Geometry.Area(ogr.ForceToPolygon(geometry))

def dropduplicate(simply_points_list):
    return sorted(set(simply_points_list),key = simply_points_list.index)

def line_simplify(douglas_threashold,line_points):
    model = Douglas.Douglas(douglas_threashold)
    model.simplify(line_points)
    while len(model.seg_list) > 0:
        model.simplify(model.seg_list.pop())
    simplify_points = model.simplify_point_list

    return simplify_points

def multiline_simplify(douglas_threashold,multiline_points):
    multiline_simplify_points = []
    for line in multiline_points:
        model = Douglas.Douglas(douglas_threashold)
        model.simplify(line)
        while len(model.seg_list) > 0:
            model.simplify(model.seg_list.pop())
        simplify_points = model.simplify_point_list
        multiline_simplify_points.append(simplify_points)

    return multiline_simplify_points

# simplify the polygon with douglas
def simplify(file_path, douglas_threashold = 15):
    """
    :param file_path:
    :param douglas_threashold:
    :param area_threshold:
    :return:
    """
    # read data
    gdl_data = gdal_readfile(file_path)

    # extract points of polygon
    wgs84_polygon_list,utm_polygon_list,flag = extract_polygon_points(gdl_data)

    #data preparing
    simplify_map_polygon = []
    line = []

    for polygon_index in range(len(utm_polygon_list)):
        wgs84_geometry_line = wgs84_polygon_list[polygon_index]
        #process multiline
        if  flag[polygon_index] == 0:
            utm_multiline = []
            for geo in wgs84_geometry_line:
                utm_multiline.append(LineString(geo))
            line.append(MultiLineString(utm_multiline))

            # douglas(multiline)
            multiline_simplify_points = multiline_simplify(douglas_threashold, utm_polygon_list[polygon_index])

            # sort the index of polygon_points

            multiline_index_list = []
            for i_line in range(len(multiline_simplify_points)):
                points_index = []

                for point in multiline_simplify_points[i_line]:

                    point_index = utm_polygon_list[polygon_index][i_line].index(point)
                    points_index.append(point_index)
                multiline_index_list.append(points_index)


            multiline_results = []
            for i in range(len(multiline_index_list)):
                line_point = []
                for j in sorted(set(multiline_index_list[i])):
                    line_point.append(wgs84_geometry_line[i][j])
                line_point.append(wgs84_geometry_line[i][0])
                if len(line_point) >= 3:
                    multiline_results.append(LineString(line_point))


            simplify_map_polygon.append(MultiLineString(multiline_results))

        #process line
        else:
            line.append(LineString(wgs84_polygon_list[polygon_index]))

            # douglas(line)
            line_simplify_points = line_simplify(douglas_threashold, utm_polygon_list[polygon_index])

            # sort the index of polygon_points
            line_index_list = []
            for point in line_simplify_points:
                point_index = utm_polygon_list[polygon_index].index(point)
                line_index_list.append(point_index)

            line_results = []

            for i in sorted(set(line_index_list)):
                line_results.append(wgs84_polygon_list[polygon_index][i])
            line_results.append(wgs84_polygon_list[polygon_index][0])
            if len(line_results) >= 3:
                simplify_map_polygon.append(LineString(line_results))



    fig,ax = plt.subplots(figsize=(10, 4))
    data = geopd.GeoDataFrame({"geometry":line})

    simplify_data = geopd.GeoDataFrame({"geometry":simplify_map_polygon})

    data["geometry"].plot(ax=ax,color = "b")
    simplify_data["geometry"].plot(ax=ax, color="r")


    plt.show()

    return simplify_map_polygon

if __name__ == '__main__':



    #data = geopd.read_file("/Users/maguorui/PycharmProjects/NJGT/Simplify/Data/202006152019.shp")
    #print(data)
    simplify("/Users/maguorui/PycharmProjects/NJGT/Simplify/Data/202006171124.shp")



