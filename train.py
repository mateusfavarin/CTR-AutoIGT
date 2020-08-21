import cv2
import numpy as np
import sklearn.neighbors as nb
import pickle

IMG_COUNT = 756
X = []
Y = []

# Opening file containing the correct label for each number in the folder labels.
f = open("labels.txt", "r")
digits = f.readline()
f.close()

# Storing the inputs to the training function in the X, Y lists
for i in range(IMG_COUNT):
    # cv2 images are already represented as numpy arrays, so there's no need to convert them
    X.append(cv2.imread("digits/img"+str(i)+".png", cv2.IMREAD_GRAYSCALE))
    Y.append(int(digits[i]))

# Converting the lists to numpy arrays
Y = np.array(Y)
X = np.array(X)
# Reshaping each image to be 1-dimensional
X = np.reshape(X, (IMG_COUNT, X.shape[1] * X.shape[2]))

# Training using k-nearest neighbors algorithm
knc = nb.KNeighborsClassifier()
knc.fit(X, Y)

# Saving the model
with open("CTR_digits.knn", 'wb') as file:
    pickle.dump(knc, file)