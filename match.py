import SimpleITK as sitk
import json
import glob
from metric import match_studyUid, match_slice


def find_tranverse(folder):
    for dcm_file in glob.glob(folder+'/*dcm'):
        image = sitk.ReadImage(dcm_file)
        image_orientation = image.GetMetaData('0020|0037') if image.HasMetaDataKey('0020|0037') else None
        if image_orientation:
            vector = list(map(float, image_orientation.split('\\')))
            x_vec = vector[:3]
            y_vec = vector[3:]
            normal_vec = 



    return dcm_lst

if __name__ == '__main__':

    data_dir = ""
    json_dir = ""

    f = open(json_dir, 'r')
    annotations = json.loads(f.read())
    f.close()

    for anno_per_case in annotations:
        folder = match_studyUid(data_dir, anno_per_case['studyUid'])
        if not folder:
            continue
        # find T2 mid
        slice_info = anno_per_case['data']
        slice, spacing = match_slice(folder, slice_info['seriesUid'], slice_info['instanceUid'])
        if not slice or not spacing:
            continue
        t2 = sitk.ReadImage(slice)
        t2_position = t2.GetMetaData('0020|0032') if t2.HasMetaDataKey('0020|0032') else 'Nan'
        t2_orientation = t2.GetMetaData('0020|0037') if t2.HasMetaDataKey('0020|0037') else 'Nan'
        # find tranverse series: 与x轴夹角大于45度
        normal_vector



