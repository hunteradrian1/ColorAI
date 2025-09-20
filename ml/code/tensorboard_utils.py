import os
import re
import tensorflow as tf

class CustomModelSaver(tf.keras.callbacks.Callback):
    """ Custom Keras callback for saving weights of networks. """

    def __init__(self, checkpoint_dir, max_num_weights=30):
        super(CustomModelSaver, self).__init__()

        # Set up checkpoint directory and weight limit
        self.checkpoint_dir = checkpoint_dir
        self.max_num_weights = max_num_weights

    def on_epoch_end(self, epoch, logs=None):
        """ At epoch end, weights are saved to checkpoint directory. """

        # Check existing weight files
        min_acc_file, max_acc_file, max_acc, num_weights = \
            self.scan_weight_files()

        cur_acc = logs["val_mean_squared_error"]

        # Create filename with epoch and accuracy
        save_name = "weights.e{0:03d}-acc{1:.4f}.h5".format(
            epoch, cur_acc)

        save_location = self.checkpoint_dir + os.sep + save_name
        print(("\nEpoch {0:03d} TEST accuracy ({1:.4f}) "
                ".\nSaving checkpoint at {location}")
                .format(epoch + 1, cur_acc, location = save_location))
        # Save current weights
        self.model.save_weights(save_location)

        # Clean up old weights if we exceed the limit
        if self.max_num_weights > 0 and \
                num_weights + 1 > self.max_num_weights:
            os.remove(self.checkpoint_dir + os.sep + min_acc_file)

    def scan_weight_files(self):
        """ Scans checkpoint directory to find current minimum and maximum
        accuracy weights files as well as the number of weights. """

        # Initialize tracking variables
        min_acc = float('inf')
        max_acc = 0
        min_acc_file = ""
        max_acc_file = ""
        num_weights = 0

        files = os.listdir(self.checkpoint_dir)

        # Scan all weight files
        for weight_file in files:
            if weight_file.endswith(".h5"):
                num_weights += 1
                # Extract accuracy from filename
                file_acc = float(re.findall(
                    r"[+-]?\d+\.\d+", weight_file.split("acc")[-1])[0])
                # Track best and worst accuracies
                if file_acc > max_acc:
                    max_acc = file_acc
                    max_acc_file = weight_file
                if file_acc < min_acc:
                    min_acc = file_acc
                    min_acc_file = weight_file

        return min_acc_file, max_acc_file, max_acc, num_weights
