import os
from random import shuffle, seed
from sklearn.model_selection import train_test_split
import shutil

# Set up data paths
data_path = "../data/raw-img/"
train_path = "../data/train/"
test_path = "../data/test/"
test_size = 0.2
rs = 42

# Set random seed for reproducibility
seed(rs)

# Create output directories
if not os.path.exists(train_path):
    os.mkdir(train_path) 
if not os.path.exists(test_path):
    os.mkdir(test_path) 

# Process each animal directory
for _, dirs, _ in os.walk(data_path):
    for di in dirs: # For each animal directory!
        for root, dirs, files in os.walk(os.path.join(data_path, di)):
            # Shuffle files and split into train/test
            shuffle(files)
            train_set, test_split = train_test_split(files, test_size=test_size, random_state=rs)
            
            # Helper function to copy files with new names
            c = lambda path: shutil.copy(os.path.join(data_path, di, f), os.path.join(path, str(i) + ".jpeg"))
            # Copy training files
            for i, f in enumerate(train_set):
                c(train_path)
            # Copy test files
            for i, f in enumerate(test_split):
                c(test_path)

        print(di)