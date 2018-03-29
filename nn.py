import os
import numpy as np 
from sklearn.neural_network import MLPClassifier
from sklearn.preprocessing import StandardScaler
from sklearn.model_selection import train_test_split
from sklearn.metrics import classification_report, confusion_matrix
from dbnn import data

if __name__ == "__main__":
    if os.path.exists('datann.npy'):
        print('loading data from file')
        data = np.load('datann.npy')
        X, y = list(data[0]), list(data[1])
    else:
        print('querying data from db')
        X, y = data()
    X_train, X_test, y_train, y_test = train_test_split(X, y)
    scaler = StandardScaler()
    scaler.fit(X_train)
    X_train = scaler.transform(X_train)
    X_test = scaler.transform(X_test)
    params = {
        'hidden_layer_sizes': (100,100,100),
        'activation': 'tanh',
        'solver': 'lbfgs',
        'alpha': .001,
        'learning_rate': 'adaptive',
        'learning_rate_init': .01
    }
    mlp = MLPClassifier(verbose=True, **params)
    mlp.fit(X_train, y_train)
    predictions = mlp.predict(X_test)
    print(confusion_matrix(y_test, predictions))
    print(classification_report(y_test, predictions))
    # print(mlp.coefs_)
    # print(mlp.intercepts_)