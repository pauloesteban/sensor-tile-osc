

# Modified by Paulo Chiliguano and Travis West
# Directed by Dr Roberto Alonso Trillo
# Department of Music - Hong Kong Baptist University
# 2022

"""Gesture model
"""
import numpy as np
from pyquaternion import Quaternion
from calibrator import Calibrator
from fusion_filter import FusionFilter


class GestureModel():
    def __init__(self):
        self.RAD_DEG_RATIO = 180 / np.pi
        self.skewness = 0
        self.tilt = 0
        self.roll = 0
        self.caccl = np.zeros(3)
        self.cgyro = np.zeros(3)
        self.cmagn = np.zeros(3)
        self.matrix = np.identity(3)
        self.movement_acceleration = np.zeros(3)
        self.acceleration_derivative = np.zeros(3)
        self.movement_velocity = np.zeros(3)
        self.quaternion = Quaternion()
        self.calibrator = Calibrator()
        self.fusion_filter = FusionFilter()

    def tick(self, accl, gyro, magn):
        self.caccl = self.calibrator.calibrate_accl(accl)
        self.cgyro = self.calibrator.calibrate_gyro(gyro)
        self.cmagn = self.calibrator.calibrate_magn(magn)
        self.quaternion = self.fusion_filter.fuse(self.cgyro, self.caccl, self.cmagn)
        self.matrix = self.quaternion.rotation_matrix
        self.skewness = self.RAD_DEG_RATIO * np.arctan2(self.matrix[1,0], self.matrix[0,0])
        self.tilt = self.RAD_DEG_RATIO * np.arctan2(self.matrix[2,0], np.sqrt(self.matrix[2,1] * self.matrix[2,1] + self.matrix[2,2] * self.matrix[2,2]))
        self.roll = self.RAD_DEG_RATIO * np.arctan2(self.matrix[2,1], self.matrix[2,2])
        self.movement_acceleration = self.fusion_filter.ma_sensor
        self.acceleration_derivative = self.fusion_filter.da
        self.movement_velocity = self.movement_velocity * 0.9999 + self.movement_acceleration