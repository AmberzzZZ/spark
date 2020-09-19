## annotations
    list, 每个元素对应一个training sample的label
    每个label是一个dict, 一级dict_keys(['studyUid', 'version', 'data'])
    data的value是个list，每个元素对应一张片子的标注dict, 二级dict_keys(['seriesUid', 'instanceUid', 'annotation'])
    其中的annotation的value是个list，每个元素对应dict，三级dict_keys(['annotator', 'data'])
    其中的data是个dict，四级dict_keys(['point'])
    point的value是个list，每个元素对应一个关键点的dict，五级dict_keys(['tag', 'coord', 'zIndex'])
    tag的value是个dict，用来表示关键点类别和病灶类别，六级dict_keys(['identification', 'vertebra']) ／ (['identification', 'dict'])
    coord的value是个list，用来表示关键点坐标
    zindex的value是个int，用来表示当前标注的片子是第几个slice



## data
    每个folder里面都有多个扫描序列，
    每个序列中可能同时包含螺旋和定位像，所以要逐张遍历，找到定位像
    我们要根据annotation里面的seriesUid找到t2矢状位，根据zindex找到对应slice，提取到data/目录下
    同时简化annotation，保留关键点信息，tag和coord，提取到label/目录下
    命名方式是foldername
    coord有z方向坐标，能够提取相应T2轴状位的图像，z方向插值。



## series
    以study0为例，
    series1, ScoutA_TSC 100/18 20mm, 256*256*9, 里面既有轴状位又有矢状位还有冠状位

    series2, ScoutA_TSC 100/18 20mm, 256*256*2, processed image，上面有划线，用来定位脊柱
    series2, FSE 4000/128 5mmS, 512*512*9, 定位后脊柱的矢状位非连续扫描，x方向voxel spacing贼大

    series3, ScoutA_TSC 100/18 20mm, 256*256*2, processed image，上面有划线，用来定位脊柱
    series3, SE 420/19 5mmS, 512*512*9, 定位后脊柱的矢状位非连续扫描，x方向voxel spacing贼大
    
    s2和s3应该就是mri的t2和t1, 间盘亮的那个是t2

    series4, ScoutA_TSC 100/18 20mm, 256*256*2, processed image，上面有划线，用来定位脊柱
    series4, IRFSE 4000/90/123 5mmS, 256*256*9, 定位后脊柱的矢状位非连续扫描，x方向voxel spacing贼大

    感觉s4也是t2，但是resolution不同

    series5, ScoutA_TSC 100/18 20mm, 256*256*1, processed image，上面有划线，用来定位间盘
    series5, FSE 4000/128 5mmS, 512*512*13, 包含一张联动的定位像和3*4个间盘重建图像，每个间盘重建3张


    判断T2: 官方给了instance id
    判断轴状位: 通过orientation，计算法向量与世界坐标系的夹角，阈值确定
    筛除定位像: 层厚&夹角


## metrics
    一个gt点的6mm范围内，只能有TP和FP，且TP最多有一个，FP有几个算几个
    一个gt点的6mm范围内如果没有TP，就算一个FN
    如果一个pred点不在任何gt点的6mm范围内，也算FP
    
    注意间盘病灶存在多标签的情况
    f1 score根据样本量加权，计算参考https://tianchi.aliyun.com/competition/entrance/531809/information


## crop
    关键点，曲线拟合，基于法线方向转正，切patch






    















