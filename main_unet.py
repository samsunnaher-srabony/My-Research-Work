# -*- coding: utf-8 -*-
"""Main_UNET.ipynb

Automatically generated by Colab.

Original file is located at
    https://colab.research.google.com/drive/1RogVV_MKTZT4G6FT6BuJFW1zU9kNykT_
"""

# train dataset

!gdown --id 1sTtMvS78-PK_Ywo8flYrjFIIPtRHXogk

#unzip train

import zipfile
zip_ref = zipfile.ZipFile('/content/train2.zip') #teeth hle train hbe only
zip_ref.extractall('/content')

zip_ref.close()

# test dataset

!gdown --id 1sDybKyEkpeZoV0ug7ctgnJhozYZoEZ0k

#unzip test

zip_ref = zipfile.ZipFile('/content/test2.zip') #teeth hle train hbe only
zip_ref.extractall('/content')

zip_ref.close()

!pip install natsort

!pip install tensorflow-addons

import tensorflow as tf
import numpy as np
import os
from PIL import Image
import matplotlib.pyplot as plt
import cv2
from keras import layers, models
import pathlib
import natsort
from sklearn.model_selection import train_test_split
from sklearn.metrics import accuracy_score, precision_score, recall_score, classification_report,f1_score
import tensorflow_addons as tfa
from sklearn.metrics import confusion_matrix
from sklearn.preprocessing import MinMaxScaler

epochs = 5000
batch = 8
eta = 0.001
imageShape = (224, 224, 1)
maskShape = (224, 224, 1)

# read,resize dataset


class readDataset:
    def __init__(self, imagesPathes, masksPathes):
        self.imagesPathes = imagesPathes
        self.masksPathes = masksPathes
    def readPathes(self,):
      self.images = natsort.natsorted(list(pathlib.Path(self.imagesPathes).glob('*.*')))
      self.masks = natsort.natsorted(list(pathlib.Path(self.masksPathes).glob('*.*')))
    def readImages(self, data, typeData):
        images = []
        for img in data:
            img = cv2.imread(str(img), 0)
            img = img/255
            img = cv2.resize(img, (224, 224))
            if typeData == 'm':
                img = np.where(img > 0, 1, 0)
            images.append(img)
        return np.array(images)
    def dataAugmentation(self, images, masks):
        imagesupdate = []
        masksupdate = []
        for image, mask in zip(images, masks):
          for aug in range(2):
            imageup = image
            maskup = mask
            if aug == 0:
              imageup = image
              maskup = mask
            else:
              imageup = tf.image.flip_left_right(imageup)
              maskup = tf.image.flip_left_right(maskup)
            imagesupdate.append(imageup), masksupdate.append(maskup)
        return np.array(imagesupdate), np.array(masksupdate)

# tt mana train,t mana test

datasetObjectt = readDataset('/content/train2/images',
                            '/content/train2/masks')    #teeth hle train and test hbe only
datasetObjectt.readPathes()

datasetObject = readDataset('/content/test2/images',
                            '/content/test2/masks')
datasetObject.readPathes()

# train dataset size
len(datasetObjectt.images), len(datasetObjectt.masks)

# test dataset size
len(datasetObject.images), len(datasetObject.masks)

# train
imagest = datasetObjectt.readImages(datasetObjectt.images, 'i')
maskst = datasetObjectt.readImages(datasetObjectt.masks, 'm')
imagest.shape, maskst.shape

# test

images = datasetObject.readImages(datasetObject.images, 'i')
masks = datasetObjectt.readImages(datasetObject.masks, 'm')
images.shape, masks.shape

# train

np.unique(maskst), np.min(maskst), np.max(maskst), np.min(imagest), np.max(maskst)

# test

np.unique(masks), np.min(masks), np.max(masks), np.min(images), np.max(masks)

# valid means test and train means train
validImages = images
validMasks = masks
trainImages = imagest
trainMasks = maskst
validImages.shape, validMasks.shape, trainImages.shape, trainMasks.shape

#convolution layer of unet


def convolution(inputs, filter, padding, strides, kernel, activation, conv_type):
  x = inputs
  x = layers.Conv2D(filter, kernel_size = kernel, padding = padding,
                    strides = strides)(x)
  x = layers.GroupNormalization(groups = filter)(x)
  if conv_type == 'decoder':
      x = layers.Activation(activation)(x)
      x = layers.Conv2D(filter*2, kernel_size = kernel, padding = padding, strides = strides)(x)
      x = layers.GroupNormalization(groups = filter*2)(x)
      x = layers.Activation(activation)(x)
      x = layers.Conv2D(filter, kernel_size = kernel, padding = padding, strides = strides)(x)
      x = layers.GroupNormalization(groups = filter)(x)

  x = layers.Activation(activation)(x)
  return x

def encoder(input, filter, padding, strides, kernel, activation):
  x = input
  x = convolution(x, filter, padding, strides, kernel, activation, 'encoder')
  downsample = layers.AveragePooling2D()(x)
  return downsample, x

def decoder(input, filter, skip, padding, strides, kernel, activation):
  x = input
  x = layers.Conv2DTranspose(filter, kernel_size = kernel, padding = padding,
                             strides = 2, activation = activation)(x)
  x = layers.average([x, skip])
  x = convolution(x, filter, padding, strides, kernel, activation, 'decoder')
  return x

def simpleunet(input, filter, padding, strides, kernel):
  x = input
  con1, skip1 = encoder(x, filter, padding = padding, strides = strides,
                        kernel = kernel, activation = 'LeakyReLU')
  con2, skip2 = encoder(con1, filter*2, padding = padding, strides = strides,
                        kernel = kernel, activation = 'LeakyReLU')
  con3, skip3 = encoder(con2, filter*4, padding = padding, strides = strides,
                        kernel = kernel, activation = 'LeakyReLU')
  con4, skip4 = encoder(con3, filter*8, padding = padding, strides = strides,
                        kernel = kernel, activation = 'LeakyReLU')
  con5, skip5 = encoder(con4, filter*16, padding = padding, strides = strides,
                        kernel = kernel, activation = 'LeakyReLU')
  deco1 = decoder(con5, filter*16, skip5, padding = padding, strides = strides,
                  kernel = kernel, activation = 'relu')
  deco2 = decoder(deco1, filter*8, skip4, padding = padding, strides = strides,
                  kernel = kernel, activation = 'relu')
  deco3 = decoder(deco2, filter*4, skip3, padding = padding, strides = strides,
                  kernel = kernel, activation = 'relu')
  deco4 = decoder(deco3, filter*2, skip2, padding = padding, strides = strides,
                  kernel = kernel, activation = 'relu')
  deco5 = decoder(deco4, filter, skip1, padding = padding, strides = strides,
                  kernel = kernel, activation = 'relu')
  output = layers.Conv2DTranspose(1, kernel_size = kernel, strides = strides,
                                  padding = padding, activation = 'sigmoid')(deco5)
  simpleunet = models.Model(inputs = input, outputs = output, name = 'unet')

  simpleunet.summary()
  return simpleunet

U = simpleunet(input = layers.Input(shape = (224, 224, 1)), filter = 32,
              padding = 'same', kernel = 3, strides = 1)

tf.keras.utils.plot_model(U, show_shapes = True)

#epoches result print

def samples(simpleunet, images, realMasks):
  masks = tf.squeeze(simpleunet.predict(images))
  all = np.vstack([realMasks, masks])
  plt.figure(figsize = (12, 4))
  for i in range(16):
    plt.subplot(2, 8, (i + 1))
    plt.imshow(all[i], cmap = 'gray')
  plt.show()

for epoch in range(epochs):
    indexs = np.random.randint(0, len(trainImages), size = (batch, ))
    realImages = trainImages[indexs]
    realMasks = trainMasks[indexs]
    realTag = tf.ones(shape = (batch, ))
    predictMasks = tf.squeeze(U.predict([realImages], verbose = 0))
    allImages = np.vstack([realImages, realImages])
    if epoch % 500 == 0:
        print('Epoch/Epochs: {}/{}'.format(epoch, epochs))
        validIndexs = np.random.randint(0, len(validImages), size = (8, ))
        samples(U, validImages[validIndexs], validMasks[validIndexs])

U = simpleunet(input = layers.Input(shape = (224, 224, 1)), filter = 32,
              padding = 'same', kernel = 3, strides = 1)
for layer in U.layers[:20]:
  layer.trainable = False

U.compile(loss = tf.keras.losses.BinaryFocalCrossentropy(),
                  optimizer = tf.keras.optimizers.Adam(learning_rate = 0.00001),
                  metrics=[
                              'accuracy',
                               tf.keras.metrics.Precision(name='precision'),
                               tf.keras.metrics.Recall(name='recall'),



    ])

#accuracy,precisison,recall history


history = U.fit(trainImages, trainMasks, epochs = 80, batch_size = 4,
                        validation_data = (validImages, validMasks), callbacks = [
                            tf.keras.callbacks.EarlyStopping(patience = 5, monitor = 'val_loss',
                                                             mode = 'min',
                                                             restore_best_weights = True)
                        ])

#graph
import matplotlib.pyplot as plt

metrics = ['Loss', 'Accuracy']

print("Available keys in history.history:", history.history.keys())

#loss graph
if 'loss' in history.history and 'val_loss' in history.history:
    plt.figure(figsize=(8, 6))
    plt.plot(history.history['loss'], label='loss')
    plt.plot(history.history['val_loss'], label='val_loss')
    plt.title('Binary Focal Cross Entropy Loss')
    plt.xlabel('Epoch')
    plt.ylabel('Loss')
    plt.legend()
    plt.show()
else:
    print("Keys 'loss' or 'val_loss' not found in history.history")

#accuracy graph
if 'accuracy' in history.history and 'val_accuracy' in history.history:
    plt.figure(figsize=(8, 6))
    plt.plot(history.history['accuracy'], label='accuracy')
    plt.plot(history.history['val_accuracy'], label='val_accuracy')
    plt.title('Accuracy')
    plt.xlabel('Epoch')
    plt.ylabel('Accuracy')
    plt.legend()
    plt.show()
else:
    print("Keys 'accuracy' or 'val_accuracy' not found in history.history")

#test

result=U.evaluate(validImages, validMasks)

loss, accuracy, precision, recall = result

#f1 score

f1_score = 2*(precision * recall)/(precision + recall)

print(f"Loss: {loss:.4f}")
print(f"Accuracy: {accuracy:.4f}")
print(f"Precision: {precision:.4f}")
print(f"Recall: {recall:.4f}")
print(f"F1 Score: {f1_score:.4f}")

#train

result=U.evaluate(trainImages, trainMasks)

loss, accuracy, precision, recall =result

#f1 score
f1_score =2*(precision * recall)/(precision + recall)


print(f"Loss: {loss:.4f}")
print(f"Accuracy: {accuracy:.4f}")
print(f"Precision: {precision:.4f}")
print(f"Recall: {recall:.4f}")
print(f"F1 Score: {f1_score:.4f}")

# Perform predictions



masks_pred = U.predict(validImages)
masks_pred = (masks_pred >= 0.5).astype('int')

masks_pred.shape

#test predicted mask

from google.colab import drive

def save_predicted_gums(images, y_pred, save_folder='/content/drive/My Drive/predicted_gum', dpi=300):  #teeth hle predicted_teeth folder

    drive.mount('/content/drive')

    os.makedirs(save_folder, exist_ok=True)

    num_images = len(images)

    for i in range(num_images):
        plt.figure(figsize=(6, 6), dpi=dpi)
        plt.imshow(images[i], cmap='gray')
        plt.imshow(np.reshape(y_pred[i], (224, 224)), alpha=0.6, cmap='gray')
        plt.axis('off')

        save_path = os.path.join(save_folder, f'predicted_gum{i + 1}.png')    #predicted_teeth{i+1}
        plt.savefig(save_path, dpi=dpi)
        plt.close()

    print(f"Predicted masks saved in {save_folder} folder.")

#only for print

# def draw(images, masks, y_pred):
#     num_images = len(images)  # Assuming images is a list or an array of images

#     plt.figure(figsize=(12, num_images * 2))
#     index = -1

#     for i in range(num_images * 3):  # Display each image three times (original, original + mask, original + predicted)
#         plt.subplot(num_images, 3, (i + 1))

#         image_index = i // 3
#         if i % 3 == 0:
#             plt.imshow(images[image_index], cmap='gray')
#             plt.title(f'Image {image_index + 1}')
#         elif i % 3 == 1:
#             plt.imshow(images[image_index], cmap='gray')
#             plt.imshow(masks[image_index], alpha=0.6, cmap='gray')
#             plt.title(f'Original Mask {image_index + 1}')
#         elif i % 3 == 2:
#             plt.imshow(images[image_index], cmap='gray')
#             plt.imshow(np.reshape(y_pred[image_index], (224, 224)), alpha=0.6, cmap='gray')
#             plt.title(f'Predicted Mask {image_index + 1}')

#     plt.tight_layout()
#     plt.show()

save_predicted_gums(validImages,masks_pred)

masks_pred = U.predict(trainImages)
masks_pred = (masks_pred >= 0.5).astype('int')

masks_pred.shape

#train predicted mask

from google.colab import drive

def save_predicted_gum(images, y_pred, save_folder='/content/drive/My Drive/predicted_gum', dpi=300): #predicted_teeth

    drive.mount('/content/drive')


    os.makedirs(save_folder, exist_ok=True)

    num_images = len(images)

    for i in range(34, 116):
        plt.figure(figsize=(6, 6), dpi=dpi)
        plt.imshow(images[i-34], cmap='gray')
        plt.imshow(np.reshape(y_pred[i-34], (224, 224)), alpha=0.6, cmap='gray')
        plt.axis('off')

        save_path = os.path.join(save_folder, f'predicted_gum{i + 1}.png') #predicted_teeth{i+1}
        plt.savefig(save_path, dpi=dpi)
        plt.close()

    print(f"Predicted masks saved in {save_folder} folder.")

save_predicted_gum(trainImages,masks_pred)