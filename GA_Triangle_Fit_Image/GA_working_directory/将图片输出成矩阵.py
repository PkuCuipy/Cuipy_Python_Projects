import numpy as np
from PIL import Image
import time
import os

image_path = "/Users/cuipy/Desktop/GA_working_directory/vae.png"
output_path = "/Users/cuipy/Desktop/GA_working_directory/target_image.dat"
target_image = Image.open(image_path).convert('RGBA')

target_mat = np.asarray(target_image, dtype='int16')
target_mat.tofile(output_path)
