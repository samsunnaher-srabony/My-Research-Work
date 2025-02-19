# -*- coding: utf-8 -*-
"""impected tooth detection(edge detection).ipynb

Automatically generated by Colab.

Original file is located at
    https://colab.research.google.com/drive/1At8y3WFm2wS49-PNRB_Sb84sjWU7_WrD
"""

import cv2
import numpy as np

import matplotlib.pyplot as plt
from skimage.io import imread, imshow
from skimage.color import rgb2gray
from skimage.morphology import (erosion, dilation, closing, opening,
                                area_closing, area_opening)
from skimage.measure import label, regionprops, regionprops_table
from google.colab.patches import cv2_imshow



# Read the original image
img = cv2.imread('/content/116O.png', cv2.IMREAD_GRAYSCALE)

# Blur the image for better edge detection

_, binary = cv2.threshold(img, 0, 255, cv2.THRESH_BINARY+cv2.THRESH_OTSU)
img_blur = cv2.GaussianBlur(binary, (3,3), 0)
cv2_imshow(img_blur)
cv2.waitKey(0)
cv2.destroyAllWindows()

# Canny Edge Detection
edges = cv2.Canny(image=img_blur, threshold1=100, threshold2=200) # Canny Edge Detection

cv2_imshow(edges)
cv2.imwrite('/content/116E.png', edges)
cv2.waitKey(0)

cv2.destroyAllWindows()



###Masking layer by layer
(nlabels, labelmap, stats, centroids) = cv2.connectedComponentsWithStats(255 - edges, connectivity=4, ltype=cv2.CV_32S)

root_label = labelmap[0,0]
area_coloring = { root_label: False } # label -> color
work = [ root_label ]
while work:
    area_label = work.pop(0)
    assert area_label in area_coloring
    color = area_coloring[area_label]

    # adjacent areas by dilating mask and finding unique labels
    mask = (labelmap == area_label).astype(np.uint8)
    mask_dilated = cv2.dilate(mask, kernel=None, iterations=3) # 3 iterations to bridge boundaries (1-2 pixels)
    adjacent_areas = set(np.unique(labelmap[mask_dilated.astype(bool)])) - {0, area_label} # excluding background and self

    areas_to_color = adjacent_areas - set(area_coloring) # - already colored
    for adjacent_area in areas_to_color:
        area_coloring[adjacent_area] = not color
    work += areas_to_color

canvas = cv2.cvtColor(255 - edges, cv2.COLOR_GRAY2BGR)
for (label, color) in area_coloring.items():
    if not color: continue
    mask = (labelmap == label)
    canvas[mask] = 186 # gray

remov_low = canvas <150
remov_high = canvas >200

mask = remov_low | remov_high
cv2.imwrite('/content/drive/MyDrive/impected/116I.png',255  - mask*255.0)
cv2.waitKey(0)

cv2.destroyAllWindows()