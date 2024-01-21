

# Modified by Paulo Chiliguano and Travis West
# Directed by Dr Roberto Alonso Trillo
# Department of Music - Hong Kong Baptist University
# 2022

"""Calibrator
"""
import numpy as np


class Calibrator():
    def __init__(self):
        self.DEG_RAD_RATIO = np.pi / 180.0
        self.accl_bias = np.zeros(3)
        self.gyro_bias = np.zeros(3)
        self.magn_bias = np.zeros(3)
        self.accl_transform = 0.001 * np.identity(3)

        # NOTE: the gyro is not yet calibrated in pyMIMU
        self.gyro_transform = self.DEG_RAD_RATIO * np.identity(3)

        self.magn_transform = np.identity(3)

    def calibrate(self, vector_measurement, matrix_transform, vector_bias):
        return np.matmul(matrix_transform, vector_measurement - vector_bias)

    def calibrate_accl(self, accl):
        return self.calibrate(accl, self.accl_transform, self.accl_bias)

    def calibrate_gyro(self, gyro):
        return self.calibrate(gyro, self.gyro_transform, self.gyro_bias)

    def calibrate_magn(self, magn):
        return self.calibrate(magn, self.magn_transform, self.magn_bias)

    #TODO: Set biases function
