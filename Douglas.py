import math

class Douglas():
    def __init__(self,threshold = 20):

        self.threshold = threshold
        self.simplify_points = []
        # 1.新建一个point_list存放简化后的点,新建一个seg_list存放分割路段
        self.simplify_point_list = []
        self.seg_list = []

    def get_distance(self,point,start_point,end_point):

        # 若直线与y轴平行，则距离为点的x坐标与直线上任意一点的x坐标差值的绝对值
        if end_point[0] - start_point[0] == 0:
            return math.fabs(point[0] - start_point[0])
        # 若直线与x轴平行，则距离为点的y坐标与直线上任意一点的y坐标差值的绝对值
        if end_point[1] - start_point[1] == 0:
            return math.fabs(point[1] - start_point[1])
        # 斜率
        k = (end_point[1] - start_point[1]) / (end_point[0] - start_point[0])
        # 截距
        b = start_point[1] - k * start_point[0]
        # 带入公式得到距离dis
        dis = math.fabs(k * point[0]- point[1] + b) / math.pow(k * k + 1, 0.5)
        return dis


    def simplify(self, polygon_points):

        # 2.取多边形首尾两点
        start_point = polygon_points[0]
        end_point = polygon_points[-1]


        # 4.计算多边形上除首尾点外任意一点到直线距离,并找出距离直线距离最大的点
        max_distance = 0
        max_index = 0
        for index, point in enumerate(polygon_points):
            # 转换为Point类

            distance = self.get_distance(point,start_point,end_point)
            if distance > max_distance:
                max_distance = distance
                max_index = index

        # 5.判断最大距离是否大于设置的阈值
        # 若大于阈值,将曲线分割为两部分
        if max_distance > self.threshold:
            seg_a = polygon_points[:max_index]
            seg_b = polygon_points[max_index:]
            for seg in [seg_a, seg_b]:
                    self.seg_list.append(seg)

        # 若小于阈值，则去掉多边形上除首尾点以外的所有的点
        else:
            self.simplify_point_list.append(start_point)
            self.simplify_point_list.append(end_point)
