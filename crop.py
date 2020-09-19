# curve_fit, rotate, crop patch
import cv2
import numpy as np
import math


def get_rotated_patch(arr, coords, patch_size, k=4):
    # pad to avoid boundary
    gapx = (patch_size[0]+1)//2
    gapy = (patch_size[1]+1)//2
    arr = np.pad(arr, [[gapy,gapy],[gapx,gapx],[0,0]], mode='constant')

    # curve_fit
    mat_a = curve_fit(coords, k)

    patch_lst = []
    for coord in coords:
        x, y = coord
        # cal theta
        curve_x = y
        curve_y = 0
        for j in range(k+1):
            curve_y += int(mat_a[j] * math.pow(curve_x, j))
        tx = 0
        ty = -1
        for j in range(1, k+1):
            tx += mat_a[j] * j * math.pow(curve_x, j-1)
        # rotate
        theta = math.atan(tx/ty)
        rotate_arr = yx_rotate(arr, math.degrees(theta), (x+gapx,y+gapy))
        # crop
        patchr = rotate_arr[y+patch_size[1], x+patch_size[0], :]
        patch_lst.append(patch_lst)

    return patch_lst


def curve_fit(points, k):
    # k: polynomial params: a0->ak
    # return: mat_a: a0->ak
    N = len(points)
    mat_x = np.zeros((k+1,k+1))
    mat_y = np.zeros((k+1))
    for i in range(k+1):
        for j in range(k+1):
            for m in range(N):
                mat_x[i][j] += math.pow(points[m][1], i+j)

        for m in range(N):
            mat_y[i] += math.pow(points[m][1], i) * points[m][0]

    mat_a = np.linalg.solve(mat_x, mat_y)
    return mat_a


def yx_rotate(arr, angle, rotate_center, interpolation=cv2.INTER_LINEAR):
    # rotate arr in yx plane
    rotate_arr = []
    for i in range(arr.shape[-1]):
        slice = arr[:,:,i]
        rotate_slice = rotate_img(angle, slice, rotate_center, interpolation=interpolation)
        rotate_arr.append(np.expand_dims(rotate_slice, axis=-1))
    rotate_arr = np.concatenate(rotate_arr, axis=-1)
    return rotate_arr


def rotate_img(angle, img, rotate_center, interpolation=cv2.INTER_LINEAR):
    # rotate img based on rotate_center
    h, w = img.shape
    rotate_Mat = cv2.getRotationMatrix2D(rotate_center, angle, 1)
    rotate_img = cv2.warpAffine(img, rotate_Mat, (w,h), flags=interpolation, borderValue=(0,0,0))
    return rotate_img





