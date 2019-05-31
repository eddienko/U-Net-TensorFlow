# ---------------------------------------------------------
# Tensorflow U-Net Implementation
# Licensed under The MIT License [see LICENSE for details]
# Written by Cheng-Bin Jin
# Email: sbkim0407@gmail.com
# ---------------------------------------------------------
import os
# import sys
# import cv2
import logging
import numpy as np
import tifffile as tiff

import utils as utils

logger = logging.getLogger(__name__)  # logger
logger.setLevel(logging.INFO)


class Dataset(object):
    def __init__(self, name='EMSegmentation', log_dir=None):
        # It is depended on dataset
        self.input_size = 572
        self.output_size = 388
        self.input_channel = 1
        self.input_shape = (self.input_size, self.input_size, self.input_channel)
        self.output_shape = (self.output_size, self.output_size)

        self.name = name
        self.dataset_path = '../../Data/EMSegmentation'

        self.train_imgs = tiff.imread(os.path.join(self.dataset_path, 'train-volume.tif'))
        self.train_labels = tiff.imread(os.path.join(self.dataset_path, 'train-labels.tif'))
        self.train_wmaps = np.load(os.path.join(self.dataset_path, 'train-wmaps.npy'))
        self.test_imgs = tiff.imread(os.path.join(self.dataset_path, 'test-volume.tif'))
        self.mean_value = np.mean(self.train_imgs)

        self.num_train = self.train_imgs.shape[0]
        self.num_test = self.test_imgs.shape[0]
        self.img_shape = self.train_imgs[0].shape

        self.init_logger(log_dir)

    @staticmethod
    def init_logger(log_dir):
        formatter = logging.Formatter('%(asctime)s:%(name)s:%(message)s')

        # file handler
        file_handler = logging.FileHandler(os.path.join(log_dir, 'dataset.log'))
        file_handler.setFormatter(formatter)

        # stream handler
        stream_handler = logging.StreamHandler()
        stream_handler.setFormatter(formatter)

        # add handlers
        logger.addHandler(file_handler)
        logger.addHandler(stream_handler)

    def info(self, use_logging=True, log_dir=None):
        if use_logging:
            logger.info('- Training-img set:\t{}'.format(self.train_imgs.shape))
            logger.info('- Training-label set:\t{}'.format(self.train_labels.shape))
            logger.info('- Training-wmap set:\t{}'.format(self.train_wmaps.shape))
            logger.info('- Test-img set:\t\t{}'.format(self.test_imgs.shape))

            logger.info('- image shape:\t\t{}'.format(self.img_shape))
        else:
            print('- Training-img set:\t{}'.format(self.train_imgs.shape))
            print('- Training-label set:\t{}'.format(self.train_labels.shape))
            print('- Training-wmap set:\t{}'.format(self.train_wmaps.shape))
            print('- Test-img set:\t\t{}'.format(self.test_imgs.shape))
            print('- image shape:\t\t{}'.format(self.img_shape))

        print('[*] Saving data augmented images to check U-Net fundamentals...')
        for idx in range(self.num_train):
            img_ = self.train_imgs[idx].copy()
            label_ = self.train_labels[idx].copy()
            wmap_= self.train_wmaps[idx].copy()
            utils.imshow(img_, label_, wmap_, idx, log_dir=log_dir)
            # utils.test_augmentation(img_, label_, idx, log_dir=log_dir)
            # utils.test_cropping(img_, label_, idx, self.input_size, self.output_size, log_dir=log_dir)
        print('[!] Saving data augmented images to check U-Net fundamentals!')


    def random_batch(self, idx, batch_size=2):
        idx = idx % self.num_train
        x_img, y_label = self.train_imgs[idx], self.train_labels[idx]

        x_batchs = np.zeros((batch_size, self.input_size, self.input_size), dtype=np.float32)
        # y_batchs will be represented in one-hot in solver.train()
        y_batchs = np.zeros((batch_size, self.output_size, self.output_size), dtype=np.float32)
        for idx in range(batch_size):
            x_batch, y_batch = utils.aug_translate(x_img, y_label)        # random translation
            x_batch, y_batch = utils.aug_flip(x_batch, y_batch)           # random horizontal and vertical flip
            x_batch, y_batch = utils.aug_rotate(x_batch, y_batch)         # random rotation
            x_batch, y_batch = utils.aug_elastic_deform(x_batch, y_batch) # random elastic deformation

            # Following the originl U-Net paper
            # Resize image to 696(696=572+92*2) x 696(696=572+92*2) then crop 572 x 572 input image
            # and 388 x 388 lable map
            # 92 = (572 - 388) / 2
            x_batch, y_batch = utils.cropping(x_batch, y_batch, self.input_size, self.output_size)

            x_batchs[idx, :, :] = x_batch
            y_batchs[idx, :, :] = y_batch

        return self.zero_centering(x_batchs), (y_batchs / 255).astype(np.uint8)

    def zero_centering(self, imgs):
        return imgs - self.mean_value


if __name__ == '__main__':
    data = Dataset()

    for i in range(data.num_train):
        img, label = data.train_imgs[i], data.train_labels[i]
        utils.imshow(img, label, idx=i)

