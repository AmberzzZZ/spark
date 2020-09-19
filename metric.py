import json
import os
import glob
import SimpleITK as sitk
import math
import numpy as np


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

    return case_TP, case_FP, case_FN


def cal_metrics_multi(gt_lst, pred_lst, cls_id, in_distance):    # per case
    cls_id_dict = {'v1':2, 'v2':3, 'v3':4, 'v4':5, 'v5':6}
    tp_lst = [0 for i in range(7)]
    fp_lst = [0 for i in range(7)]
    fn_lst = [0 for i in range(7)]
    case_TP, case_FP, case_FN = 0, 0, 0
    for gt_kp in gt_lst:
        gt_x, gt_y, spacing_x, spacing_y = gt_kp[:4]
        signs = gt_kp[4:]
        cls_ids = [cls_id_dict[i] for i in signs]

        TP = 0
        FP = 0
        min_dis = 6
        min_cls = 8
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
                    if dis < min_dis:
                        min_cls = cls
                        min_dis = dis
                else:
                    FP += 1
        if TP:
            case_TP += 1
            tp_lst[min_cls] += 1
        else:
            case_FN += 1
            fn_lst[cls_ids[0]] += 1
        case_FP += FP
        fp_lst[cls_ids[0]] += FP

    return case_TP, case_FP, case_FN, tp_lst, fp_lst, fn_lst


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


def match_gt(kp, gt_points, pred_points):
    for pred_kp in pred_points:
        if pred_kp['coord'] == kp[:2]:
            pred_kp_label = pred_kp['tag']['identification']
            for gt_kp in gt_points:
                if gt_kp in gt_points:
                    if gt_kp['tag']['identification'] == pred_kp_label:
                        if 'vertebra' in gt_kp['tag'].keys():
                            if gt_kp['tag']['vertebra'] == 'v1':
                                return 0
                            if gt_kp['tag']['vertebra'] == 'v2':
                                return 1
                        if 'disc' in gt_kp['tag'].keys():
                            if ',' in gt_kp['tag'].keys():
                                signs = gt_kp['tag']['disc'].split(',')
                            else:
                                signs = [gt_kp['tag']['disc']]
                            cls_id_dict = {'v1':2, 'v2':3, 'v3':4, 'v4':5, 'v5':6}
                            return cls_id_dict[signs[0]]


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
    idx = 0
    for anno_per_case in annotations_gt:
        # read gt
        folder = match_studyUid(data_dir, anno_per_case['studyUid'])
        if not folder:
            continue
        slice_info = anno_per_case['data'][0]
        slice, spacing = match_slice(folder, slice_info['seriesUid'], slice_info['instanceUid'])
        if not slice or not spacing:
            continue
        print('idx: ', idx, " folder: ", folder)
        idx += 1

        kpoints = slice_info['annotation'][0]['data']['point']
        gt_lst = [[] for i in range(8)]   # [vertebra-v1, vertebra-v2, disc-v1, disc-v2, disc-v3, disc-v4, disc-v5, disc-multi]
        for point in kpoints:
            signs = []
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
                if ',' in point['tag']['disc']:
                    print('find multi label')
                    signs = point['tag']['disc'].split(',')
                    cls_id = 7
            gt_lst[cls_id].append(point['coord']+spacing+signs)
        print('number of gt points: ', len(kpoints))

        # read pred
        slice_info_pred = match_pred(annotations_pred, anno_per_case['studyUid'])
        if not slice_info_pred:
            continue
        kpoints = slice_info_pred['annotation'][0]['data']['point']
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
        print('number of pred points: ', len(kpoints))

        # cal metric per case per cls
        in_distance = []
        case_tp = [0 for i in range(7)]
        case_fp = [0 for i in range(7)]
        case_fn = [0 for i in range(7)]
        for i in range(8):
            if not gt_lst[i]:
                continue
            if i < 7:
                case_TP, case_FP, case_FN = cal_metrics(gt_lst[i], pred_lst, i, in_distance)
                TP[i] += case_TP
                FP[i] += case_FP
                FN[i] += case_FN
                case_tp[i] += case_TP
                case_fp[i] += case_FP
                case_fn[i] += case_FN
            else:
                case_TP, case_FP, case_FN, tp_lst, fp_lst, fn_lst = cal_metrics_multi(gt_lst[i], pred_lst, i, in_distance)
                print('multi: ', case_TP==sum(tp_lst), case_FP==sum(fp_lst), case_FN==sum(fn_lst))
                for j in range(7):
                    TP[j] += tp_lst[j]
                    FP[j] += fp_lst[j]
                    FN[j] += fn_lst[j]
                    case_tp[j] += tp_lst[j]
                    case_fp[j] += fp_lst[j]
                    case_fn[j] += fn_lst[j]

        # 5. distance >=6 for all: FP
        if len(pred_lst) != len(in_distance):
            for kp in [i for i in pred_lst if i not in in_distance]:
                # find matched gt point
                gt_label = match_gt(kp, slice_info['annotation'][0]['data']['point'], slice_info_pred['annotation'][0]['data']['point'])
                FP[gt_label] += 1
                case_fp[gt_label] += 1

        print('case tp: ', case_tp)
        print('case fp: ', case_fp)
        print('case fn: ', case_fn)

    # cal recall/precision/f1 per cls
    print('cls tp: ', TP)
    print('cls fp: ', FP)
    print('cls fn: ', FN)
    recall = [0 for i in range(7)]
    precision = [0 for i in range(7)]
    f1 = [0 for i in range(7)]
    for i in range(7):
        recall[i] = TP[i] / (TP[i] + FN[i])
        precision[i] = TP[i] / (TP[i] + FP[i])
        if (precision[i]+recall[i])==0:
            f1[i] = 0
        else:
            f1[i] = 2*precision[i]*recall[i] / (precision[i]+recall[i])
    # cal score
    weights = [TP[i]+FN[i] for i in range(7)]
    weights = [float(i)/sum(weights) for i in weights]
    # score = math.mean(f1)
    score = np.sum(np.array(f1)*np.array(weights))
    print('cls f1: ', f1)
    print('score: ', score)



# ######### model limit ########################
# TP = [26,224,115,62,61,16,34]
# FP = [0 for i in range(7)]
# FN = [0 for i in range(7)]
# TP[1] -= 54
# FN[1] += 54

# recall = [0 for i in range(7)]
# precision = [0 for i in range(7)]
# f1 = [0 for i in range(7)]
# for i in range(7):
#     recall[i] = TP[i] / (TP[i] + FN[i])
#     precision[i] = TP[i] / (TP[i] + FP[i])
#     if (precision[i]+recall[i])==0:
#         f1[i] = 0
#     else:
#         f1[i] = 2*precision[i]*recall[i] / (precision[i]+recall[i])
# # cal score
# weights = [TP[i]+FN[i] for i in range(7)]
# weights = [float(i)/sum(weights) for i in weights]
# score = np.sum(np.array(f1)*np.array(weights))
# print('cls f1: ', f1)
# print('score: ', score)
# # cls f1:  [1.0, 0.8629441624365483, 1.0, 1.0, 1.0, 1.0, 1.0]
# # score:  0.9429358594531353







