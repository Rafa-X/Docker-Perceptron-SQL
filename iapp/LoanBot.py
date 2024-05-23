import os
import numpy as np
import pickle

class LoanBot:
    weights_file = "LoanBot.pkl"
    instance = None
    weights = None
    bias = None
    feature_mins = None
    feature_maxes = None

    def __init__(self):
        if self.instance != None:
            return self.instance
        
        if os.path.exists(self.weights_file):  #check if the pickle file exists in the folder
            with open(self.weights_file, 'rb') as f:  #loads all the parameters for the perceptron
                self.instance = pickle.load(f)
                self.weights = self.instance.weights
                self.bias = self.instance.bias
                self.feature_mins = self.instance.feature_mins
                self.feature_maxes = self.instance.feature_maxes
        else:
            #if the file doesn't exist, initialize the parameters and saves it for the future in a pickle file
            self.weights = np.random.rand(4)  
            self.bias = 0
            self.instance = self
            self.save_instance()

    def save_instance(self):
        with open(self.weights_file, 'wb') as f:  #save the data for a later use
            pickle.dump(self, f)

    def train(self, data):
        training_data = np.array(data)  #convert the pickle data to an array

        #saves in two arrays the minimum and maximum elements in order descendant/ascendant
        self.feature_mins = np.min(training_data[:, :-1], axis = 0)
        self.feature_maxes = np.max(training_data[:, :-1], axis = 0)

        for row in training_data:  #for each row normalize the data and calculate if the result is 1/0 - accepted/rejected
            normalized_features = self.normalize_row(row[:-1])
            result = self.predict(normalized_features, 0)  #pass the arguments and train phase = 0
            if result != row[-1]:
                if row[4] == 1:
                    self.weights += normalized_features
                    self.bias += 1
                else:
                    self.weights -= normalized_features
                    self.bias -= 1

            self.save_instance()
        
    def test(self, data):  #function only for testing the perceptron
        testing_data = np.array(data)
        total_tests = 0
        total_correct = 0

        for row in testing_data:  #evaluate the data row per row evaluating the expected result guided for the bias
            total_tests += 1
            result = self.predict(row[:-1])
            print("Expected result: " + str(row[-1]))
            if result == row[-1]:
                total_correct += 1

        print(str((total_correct / total_tests) * 100) + "% accuracy")
        print("Tested " + str(total_tests) + " scenarios, and got " + str(total_correct) + " correct.")

    def predict(self, input_arr, phase):
        #phase -> tells if its in the train or real predict 
        weight_vector = np.array(self.weights)
        input_vector = self.normalize_row(np.array(input_arr))  #get the normalized row of data

        product = np.dot(weight_vector, input_vector)  #returns the dot (equal central values) in the given arrays
    
        print("Product = " + str(product))
        print("Bias = " + str(self.bias))
        if product < 45 and phase == 1:  result = 0
        else:  result = 1 / (1 + np.exp(-(product + self.bias)))
        print("Result = " + str(result))

        if result >= 1:  #activation function
            return 1
        else:
            return 0
    
    def normalize_row(self, row):  #normalize a row of data filtering the min and max values
        return (row - self.feature_mins) / (self.feature_maxes - self.feature_mins)
