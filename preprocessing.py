import logging
import pandas as pd
import numpy as np
from typing import List

# TODO: if output_feature in input_features:
# inputs = windows[:-1] 3d
# outputs = windows[-1] 2d
# TODO: if output_features not in input_features:
# inputs = windows[:] 3d
# outputs = output_features[seqlen:] 2d


class Preprocessor:
    def __init__(self, dataset: pd.DataFrame,
                 input_sequence_length: int,
                 output_sequence_length: int,
                 input_features: List[str],
                 output_features: str,
                 test_fraction: float):
        """
        Preprocess data and store metadata for preprocessed data

        Args:
            dataset (pandas.DataFrame): Full dataset
            input_sequence_length (int): Length of input windows
            output_sequence_length (int): Length of output windows
            input_features (list[str]): Features used as inputs
            output_features (str): Feature used as outputs.
                We make the assumption that only one feature is used as the output.
            test_fraction (float): Fraction of data to use for validation
        """
        self.logger = logging.getLogger(__name__)
        self.dataset = dataset
        self.sequence_length = input_sequence_length
        self.input_features = input_features
        self.output_features = output_features
        self.test_fraction = test_fraction

        self.inputs, self.outputs = (None, None)
        self.xs, self.ys = (None, None)
        self.x_train, self.x_test, self.y_train, self.y_test = (None, None, None, None)

    def normalize(self, dataset):
        """
            Normalize the mean of each feature/column set to 0

            Args:
                dataset (np.ndarray): feature-filtered dataset

            Returns:
                np.ndarray: numpy array of 0-mean features

            """
        means = dataset.mean(axis=0)
        self.logger.debug('Data means: {}'.format(means))
        return dataset - means

    def generate_windows(self, arr, window_size):
        """
        Create a list of windows by sliding over the input array

        Args:
            arr (np.ndarray): original numpy array
            window_size (int): length of each window

        Returns:
            np.ndarray: numpy array of windows

        """
        shape = (arr.shape[0] - window_size + 1, window_size) + arr.shape[1:]
        strides = (arr.strides[0],) + arr.strides
        windows = np.lib.stride_tricks.as_strided(arr, shape=shape, strides=strides)
        self.logger.info('Window list shape: {}'.format(windows.shape))
        return windows

    def train_test_split(self, sequence, fraction):
        train, test = np.split(sequence, [int((1 - fraction) * len(sequence))])
        return train, test

    def process(self):
        """
            Turn a dataframe into a sequence of normalized window-label pairs,
            divided into training and testing sets.

            Returns:
                tuple[np.ndarray]: full sequence of windows, x_train, x_test, y_train, y_test

            """
        self.inputs = np.array(self.dataset[self.input_features])
        self.outputs = np.array(self.dataset[self.output_features])
        inputs, outputs = self.normalize(self.inputs), self.normalize(self.outputs)
        self.xs = self.generate_windows(inputs, self.sequence_length)
        self.ys = outputs[self.sequence_length-1:]
        self.x_train, self.x_test = self.train_test_split(self.xs, self.test_fraction)
        self.y_train, self.y_test = self.train_test_split(self.ys, self.test_fraction)
        return self.xs, self.x_train, self.x_test, self.y_train, self.y_test
