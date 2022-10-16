'''
Created on Jun 29, 2018

@author: njiang
'''

import os, argparse
from skimage.io import imread
from glob import glob
import numpy as np
from numpy import nonzero

def options():

    parser = argparse.ArgumentParser(description='Generate point cloud file from binary image slices',formatter_class=argparse.ArgumentDefaultsHelpFormatter)

    parser.add_argument('-i', "--input_folder", help="directory of binay image slices", required=True)

    args = parser.parse_args()

    return args

args = options()
original_folder = args.input_folder

parent_path = os.path.dirname(original_folder)
folder_name = os.path.basename(original_folder)
obj_file = os.path.join(parent_path, folder_name+".out")

files = sorted(glob(original_folder+'/*.png'))

for y in range(len(files)):

    img = imread(files[y])

    if y == 0:
        imgs = np.zeros((len(files), img.shape[0], img.shape[1]),np.uint8)
    imgs[y, ...] = img

indices = nonzero(imgs)
indices = np.array(indices)
indices = np.transpose(indices)

with open(obj_file, "wb+") as f:
    np.savetxt(f, np.array([0.15]), fmt = '%s')
    np.savetxt(f, np.array([int(len(indices))]), fmt = '%s')
    np.savetxt(f, indices[..., (1,2,0)], fmt='%s', delimiter=' ')












