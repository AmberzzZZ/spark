import json
import os
import glob
import SimpleITK as sitk
import math


def cal_metrics(gt_lst, pred_lst, cls_id, in_distance):    # per case
    case_TP, case_FP, case_FN = 0, 0, 0
    for gt_kp in gt_lst:
        gt_x, gt_y, spacing_x, spacing_y = gt_kp[:4]

        TP = 0
        FP = 0
        for pred_kp in pred_lst:
            # 1. distance < 6 && same cls: TP
            # 2. other matched: skip
            # 3. not matched: FP
            # 4. without match: FN
            pred_x, pred_y, cls = pred_kp
            dis = math.sqrt(((gt_x-pred_x)*spacing_x)**2+((gt_y-pred_y)*spacing_y)**2)
            if dis<6:
                if pred_kp not in in_distance:
                    in_distance.append(pred_kp)
                if cls == cls_id:
                        TP += 1
                else:
                    FP += 1
        if TP:
            case_TP += 1
        else:
            case_FN += 1
        case_FP += FP

    if len(pred_kp) != len(in_distance):
        case_FP += len(pred_kp)-len(in_distance)

    return case_TP, case_FP, case_FN


def cal_metrics_multi(gt_lst, pred_lst, cls_id, in_distance):    # per case
    cls_id_dict = {'v1':2, 'v2':3, 'v3':4, 'v4':5, 'v5':6}
    case_TP, case_FP, case_FN = 0, 0, 0
    for gt_kp in gt_lst:
        gt_x, gt_y, spacing_x, spacing_y = gt_kp[:4]
        signs = gt_kp[4:]
        cls_ids = [cls_id_dict[i] for i in signs]

        TP = 0
        FP = 0
        for pred_kp in pred_lst:
            # 1. distance < 6 && same cls: TP
            # 2. other matched: skip
            # 3. not matched: FP
            # 4. without match: FN
            pred_x, pred_y, cls = pred_kp
            dis = math.sqrt(((gt_x-pred_x)*spacing_x)**2+((gt_y-pred_y)*spacing_y)**2)
            if dis<6:
                if pred_kp not in in_distance:
                    in_distance.append(pred_kp)
                if cls in cls_ids:
                        TP += 1
                else:
                    FP += 1
        if TP:
            case_TP += 1
        else:
            case_FN += 1
        case_FP += FP

    if len(pred_kp) != len(in_distance):
        case_FP += len(pred_kp)-len(in_distance)

    return case_TP, case_FP, case_FN


def match_studyUid(data_dir, studyUid):
    for folder in os.listdir(data_dir):
        for dcm in glob.glob(os.path.join(data_dir, folder)+'/*dcm'):
            image = sitk.ReadImage(dcm)
            studyID = image.GetMetaData('0020|000d') if image.HasMetaDataKey('0020|000d') else 'Nan'
            if studyID==studyUid:
                return os.path.join(data_dir, folder)
    return None


def match_slice(data_dir, seriesUid, instanceUid):
    for dcm in glob.glob(data_dir+'/*dcm'):
        image = sitk.ReadImage(dcm)
        seriesID = image.GetMetaData('0020|000e') if image.HasMetaDataKey('0020|000e') else 'Nan'
        instanceID = image.GetMetaData('0008|0018') if image.HasMetaDataKey('0008|0018') else 'Nan'
        if seriesID==seriesUid and instanceID==instanceUid:
            # read pixel spacing
            spacing = image.GetMetaData('0028|0030') if image.HasMetaDataKey('0028|0030') else None
            if spacing:
                spacing = list(map(float, spacing.split('\\')))
            return dcm, spacing
    return None, None


def match_pred(annotations_pred, studyUid):
    for anno in annotations_pred:
        if anno['studyUid'] == studyUid:
            return anno['data'][0]
    return None


if __name__ == '__main__':

    data_dir = ""
    gt_json = ""
    pred_json = ""

    f = open(gt_json, 'r')
    annotations_gt = json.loads(f.read())
    f.close()

    f = open(pred_json, 'r')
    annotations_pred = json.loads(f.read())
    f.close()

    TP, FP, FN = [0 for i in range(7)], [0 for i in range(7)], [0 for i in range(7)]
    # tranverse per case
    for anno_per_case in annotations_gt:
        # read gt
        folder = match_studyUid(data_dir, anno_per_case['studyUid'])
        if not folder:
            continue
        slice_info = anno_per_case['data']
        slice, spacing = match_slice(folder, slice_info['seriesUid'], slice_info['instanceUid'])
        if not slice or not spacing:
            continue
        kpoints = slice_info['annotation'][0]['data']['point']
        gt_lst = [[] for i in range(8)]   # [vertebra-v1, vertebra-v2, disc-v1, disc-v2, disc-v3, disc-v4, disc-v5, disc-multi]
        for point in kpoints:
            if 'vertebra' in point['tag'].keys():
                if point['tag']['vertebra']=='v1':
                    cls_id = 0
                if point['tag']['vertebra']=='v2':
                    cls_id = 1
            if 'disc' in point['tag'].keys():
                signs = []
                if point['tag']['disc']=='v1':
                    cls_id = 2
                if point['tag']['disc']=='v2':
                    cls_id = 3
                if point['tag']['disc']=='v3':
                    cls_id = 4
                if point['tag']['disc']=='v4':
                    cls_id = 5
                if point['tag']['disc']=='v5':
                    cls_id = 6
                if ',' in point['tag']['disc']:
                    signs = point['tag']['disc'].split(',')
                    cls_id = 7
            gt_lst[cls_id].append(point['coord']+spacing+signs)

        # read pred
        slice_info_pred = match_pred(annotations_pred, anno_per_case['studyUid'])
        if not slice_info_pred:
            continue
        kpoints = slice_info_pred['point']
        pred_lst = []
        for point in kpoints:
            if 'vertebra' in point['tag'].keys():
                if point['tag']['vertebra']=='v1':
                    cls_id = 0
                if point['tag']['vertebra']=='v2':
                    cls_id = 1
            if 'disc' in point['tag'].keys():
                if point['tag']['disc']=='v1':
                    cls_id = 2
                if point['tag']['disc']=='v2':
                    cls_id = 3
                if point['tag']['disc']=='v3':
                    cls_id = 4
                if point['tag']['disc']=='v4':
                    cls_id = 5
                if point['tag']['disc']=='v5':
                    cls_id = 6
            pred_lst.append(point['coord']+[cls_id])

        # cal metric per case per cls
        in_distance = []
        for i in range(8):
            if not gt_lst[i]:
                continue
            if i < 7:
                case_TP, case_FP, case_FN = cal_metrics(gt_lst[i], pred_lst, i, in_distance)
            else:
                case_TP, case_FP, case_FN = cal_metrics_multi(gt_lst[i], pred_lst, i, in_distance)
            TP[i] += case_TP
            FP[i] += case_FP
            FN[i] += case_FN

        # 5. distance >=6 for all: FP
        if len(pred_lst) != len(in_distance):
            FP[i] += len(pred_lst) - len(in_distance)

    # cal recall/precision/f1 per cls
    recall = [0 for i in range(7)]
    precision = [0 for i in range(7)]
    f1 = [0 for i in range(7)]
    for i in range(7):
        recall[i] = TP[i] / (TP[i] + FN[i])
        precision[i] = TP[i] / (TP[i] + FP[i])
        f1[i] = 2*precision[i]*recall[i] / (precision[i]+recall[i])
    # cal score
    score = math.mean(f1)










