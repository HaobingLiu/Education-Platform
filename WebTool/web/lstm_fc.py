# -*- coding: UTF-8 -*-
import numpy as np
import pandas as pd
# import csv
# import matplotlib.pyplot as plt
import keras
from keras.models import Sequential
from keras.layers import Dense
from keras.layers import LSTM
from keras.layers import Masking
# from sklearn.model_selection import train_test_split
# from sklearn.preprocessing import MinMaxScaler
# from sklearn.metrics import mean_squared_error
# from keras.layers import Bidirectional
# #from keras.preprocessing.sequence import pad_sequences
###




np.random.seed(1119)



# x_test = np.array( pd.read_csv("x_test.csv",header=None) )
# x_test = np.reshape(x_test,(x_test.shape[0],7,1))
"""
上面是文件格式
下面是一个个学生，list格式
"""
x_test = np.array([[78.86,74.89,-2,-2,-2,-2,-2],[78.17,80.13,82.53,82.76,53.22,-2,-2]])
x_test = np.reshape(x_test,(x_test.shape[0],7,1))

batch_size = 32 #超参
epochs = 1000 #超参
units = 6 #超参 4不行

model = Sequential()
model.add(Masking(mask_value=-2., input_shape=(7,1)))
model.add(LSTM(units))
model.add(Dense(1))
print(model.summary())
model.compile(loss='mean_squared_error', optimizer='adam',metrics=['mse', 'mape'])

# filepath = './lstmfc/model-ep{epoch:03d}-mse{mean_squared_error:.3f}-val_mse{val_mean_squared_error:.3f}-val_mape{val_mean_absolute_percentage_error}.h5'
# checkpoint = keras.callbacks.ModelCheckpoint(filepath, monitor='val_mean_squared_error', verbose=1, save_best_only=True, mode='min')
# model.fit(x_train, y_train, epochs=epochs, batch_size=batch_size, verbose=1, validation_data=(x_test, y_test), shuffle=True, callbacks=[checkpoint])

###predict
model.load_weights('./lstmfc/model-ep995-mse28.667-val_mse28.815-val_mape4.917600361394993.h5')
print('load weights...')
reeee = model.predict(x_test)
print(reeee)
print(reeee.shape)
