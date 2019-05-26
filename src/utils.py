# ---------------------------------------------------------
# Tensorflow U-Net Implementation
# Licensed under The MIT License [see LICENSE for details]
# Written by Cheng-Bin Jin
# Email: sbkim0407@gmail.com
# ---------------------------------------------------------
import os
import cv2
import sys
import elasticdeform
import numpy as np

from scipy.ndimage import rotate


def make_folders(is_train, cur_time=None):
    if is_train:
        model_dir = os.path.join('model', '{}'.format(cur_time))
        log_dir = os.path.join('logs', '{}'.format(cur_time))

        if not os.path.isdir(model_dir):
            os.makedirs(model_dir)

        if not os.path.isdir(log_dir):
            os.makedirs(log_dir)
    else:
        model_dir = os.path.join('model', '{}'.format(cur_time))
        log_dir = os.path.join('logs', '{}'.format(cur_time))

    return model_dir, log_dir


def imshow(img, label, idx, alpha=0.6, delay=1, log_dir=None, show=False):
    img_dir = os.path.join(log_dir, 'img')
    if not os.path.isdir(img_dir):
        os.makedirs(img_dir)

    if len(img.shape) == 2:
        img = np.dstack((img, img, img))

    pseudo_label = None
    if len(label.shape) == 2:
        pseudo_label = pseudoColor(label)

    beta = 1. - alpha
    overlap = cv2.addWeighted(src1=img,
                              alpha=alpha,
                              src2=pseudo_label,
                              beta=beta,
                              gamma=0.0)

    canvas = np.hstack((img, pseudo_label, overlap))
    cv2.imwrite(os.path.join(img_dir, 'GT_' + str(idx).zfill(2) + '.png'), canvas)

    if show:
        cv2.imshow('Show', canvas)

        if cv2.waitKey(delay) & 0xFF == 27:
            sys.exit('Esc clicked!')


def pseudoColor(label, thickness=3):
    img = label.copy()
    img, contours, hierachy = cv2.findContours(img, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    img = np.dstack((img, img, img))

    for i in range(len(contours)):
        cnt = contours[i]
        cv2.drawContours(img, [cnt], contourIdx=-1, color=(0, 255, 0), thickness=thickness)
        cv2.fillPoly(img, [cnt], color=randomColors(i))

    return img


def randomColors(idx):
    Sky = [128, 128, 128]
    Building = [128, 0, 0]
    Pole = [192, 192, 128]
    Road = [128, 64, 128]
    Pavement = [60, 40, 222]
    Tree = [128, 128, 0]
    SignSymbol = [192, 128, 128]
    Fence = [64, 64, 128]
    Car = [64, 0, 128]
    Pedestrian = [64, 64, 0]
    Bicyclist = [0, 128, 192]
    DarkRed = [0, 0, 139]
    PaleVioletRed = [147, 112, 219]
    Orange = [0, 165, 255]
    Teal = [128, 128, 0]

    color_dict = [Sky, Building, Pole, Road, Pavement,
                  Tree, SignSymbol, Fence, Car, Pedestrian,
                  Bicyclist, DarkRed, PaleVioletRed, Orange, Teal]

    return color_dict[idx % len(color_dict)]

def test_augmentation(img, label, idx, margin=10, log_dir=None):
    img_dir = os.path.join(log_dir, 'img')
    if not os.path.isdir(img_dir):
        os.makedirs(img_dir)

    img_tran, label_tran = aug_translate(img, label)          # random translation
    img_flip, label_flip = aug_flip(img, label)             # random horizontal and vertical flip
    img_rota, label_rota = aug_rotate(img, label)             # random rotation
    img_defo, label_defo = aug_elastic_deform(img, label)   # random elastic deformation
    img_pert, label_pert = aug_perturbation(img, label)     # random intensity perturbation

    # Arrange the images in a canvas and save them into the log file
    imgs = [img, img_tran, img_flip, img_rota, img_defo, img_pert]
    labels = [label, label_tran, label_flip, label_rota, label_defo, label_pert]
    h, w = img.shape
    canvas = np.zeros((2 * h + 3 * margin, len(imgs) * w + (len(imgs) + 1) * margin), dtype=np.uint8)

    for i, (img, label) in enumerate(zip(imgs, labels)):
        canvas[margin:margin+h, (i+1) * margin + i * w:(i+1) * margin + (i + 1) * w] = img
        canvas[2*margin+h:2*margin+2*h, (i+1) * margin + i * w:(i+1) * margin + (i + 1) * w] = label

    cv2.imwrite(os.path.join(img_dir, 'augmentation_' + str(idx).zfill(2) + '.png'), canvas)

def aug_translate(img, label, max_factor=1.1):
    assert len(img.shape) == 2 and len(label.shape) == 2

    # Resize originl image
    resize_factor = np.random.uniform(low=1.,  high=max_factor)
    img_bigger = cv2.resize(src=img.copy(), dsize=None, fx=resize_factor, fy=resize_factor,
                            interpolation=cv2.INTER_LINEAR)
    label_bigger = cv2.resize(src=label.copy(), dsize=None, fx=resize_factor, fy=resize_factor,
                              interpolation=cv2.INTER_NEAREST)

    # Generate random positions for horizontal and vertical axes
    h_bigger, w_bigger = img_bigger.shape
    h_star = np.random.random_integers(low=0, high=h_bigger-img.shape[0])
    w_star = np.random.random_integers(low=0, high=w_bigger-img.shape[1])

    # Crop image from the bigger one
    img_crop = img_bigger[h_star:h_star+img.shape[1], w_star:w_star+img.shape[0]]
    label_crop = label_bigger[h_star:h_star+img.shape[1], w_star:w_star+img.shape[0]]

    return img_crop, label_crop

def aug_flip(img, label):
    assert len(img.shape) == 2 and len(label.shape) == 2

    # Random horizontal flip
    if np.random.uniform(low=0., high=1.) > 0.5:
        img_hflip = cv2.flip(src=img, flipCode=0)
        label_hflip =  cv2.flip(src=label, flipCode=0)
    else:
        img_hflip = img.copy()
        label_hflip = label.copy()

    # Random vertical flip
    if np.random.uniform(low=0., high=1.) > 0.5:
        img_vflip = cv2.flip(src=img_hflip, flipCode=1)
        label_vflip = cv2.flip(src=label_hflip, flipCode=1)
    else:
        img_vflip = img_hflip.copy()
        label_vflip = label_hflip.copy()

    return img_vflip, label_vflip

def aug_rotate(img, label):
    assert len(img.shape) == 2 and len(label.shape) == 2

    # Random rotate image
    angle = np.random.randint(low=0, high=360, size=None)
    img_rotate = rotate(input=img, angle=angle, axes=(0, 1), reshape=False, order=3, mode='reflect')
    label_rotate = rotate(input=label, angle=angle, axes=(0, 1), reshape=False, order=3, mode='reflect')

    # Correct label map
    label_rotate[label_rotate > 127] = 255
    label_rotate[label_rotate < 127] = 0

    return img_rotate, label_rotate

def aug_elastic_deform(img, label):
    assert len(img.shape) == 2 and len(label.shape) == 2

    # Apply deformation with a random 3 x 3 grid to inputs X and Y,
    # with a different interpolation for each input
    img_distort, label_distort = elasticdeform.deform_random_grid(X=[img, label],
                                                                  sigma=10,
                                                                  points=3,
                                                                  order=[3, 0],
                                                                  mode='mirror')

    return img_distort, label_distort


def aug_perturbation(img, label, low=0.8, high=1.2):
    pertur_map = np.random.uniform(low=low, high=high, size=img.shape)
    img_en = np.round(img * pertur_map).astype(np.uint8)
    img_en = np.clip(img_en, a_min=0, a_max=255)
    return img_en, label

def pre_bilaterFilter(img, d=3, sigmaColor=75, simgaSpace=75):
    pre_img = cv2.bilateralFilter(src=img, d=d, sigmaColor=sigmaColor, sigmaSpace=simgaSpace)
    return pre_img

# def uint82float32():

# zero centering

# add last channel
