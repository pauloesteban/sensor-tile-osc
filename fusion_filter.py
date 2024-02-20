

# Modified by Paulo Chiliguano 
# Developed by Travis West
# Directed by Dr Roberto Alonso Trillo
# HKBU Academy of Music
# 2024

"""Fusion filter
"""
import numpy as np
from time import monotonic
from pyquaternion import Quaternion


class BaseFilter:
    def __init__(self):
        self.period = 0
        self.current = monotonic()
        self.previous = self.current
        self.q       = Quaternion()
        self.q_align = Quaternion()

    def calculate_period(self):
        self.current = monotonic()
        self.period = self.current - self.previous
        self.previous = self.current

        return self.period

    def set_alignment(self):
        self.q_align = self.q.conjugate

    def align(self, quaternion):
        return self.q_align * quaternion

    def fuse(self, omega, v_a, v_m, k_I = 1.0, k_P = 3.0, k_a=1.0, k_m=1.0):
        return Quaternion()

    def fuse_and_align(self, *args):
        q = self.fuse(*args)
        return self.align(q), self.q_align.rotate(self.ma_earth)


class FusionFilter(BaseFilter):
    def __init__(self):
        super().__init__()
        self.static_threshold = 0.01
        self.galpha = 0.93
        self.b_hat      = np.zeros(3)
        self.h          = np.zeros(3)
        self.b          = np.zeros(3)
        self.ma_earth   = np.zeros(3)
        self.ma_sensor  = np.zeros(3)
        self.v_hat_x    = np.zeros(3)
        self.v_hat_a    = np.zeros(3)
        self.w_a        = np.zeros(3)
        self.w_x        = np.zeros(3)
        self.w_mes      = np.zeros(3)
        self.da         = np.zeros(3)
        self.anm1       = np.zeros(3)
        self.aa         = np.zeros(3)
        self.gyro_bias = np.zeros(3)


    def set_gyro_bias_alpha(self, v):
        self.galpha = v

    def set_static_threshold(self, v):
        self.static_threshold = v

    def fuse(self, omega, v_a, v_m, k_I = 0.0, k_P = 3.0, k_a=1.0, k_m=0.0):
        self.calculate_period()

        self.aa = self.anm1 * 0.5 + self.aa * 0.5 # average accel
        self.da = (self.aa - self.anm1) # "derivative" accel
        self.static = np.linalg.norm(self.da) < self.static_threshold
        self.anm1 = v_a

        if self.static:
            self.gyro_bias = (1 - self.galpha) * omega + self.galpha * self.gyro_bias
        omega -= self.gyro_bias

        rotation = self.q.rotation_matrix # the basis axes of the sensor frame expressed in the global frame
        inverse  = self.q.conjugate.rotation_matrix # the basis axes of the global frame expressed in the sensor frame

        # inverse[2] represents the global Z axis (related to gravity) expressed in the sensor coordinate frame
        self.ma_sensor = v_a - inverse[:,2]             # zero-g in sensor frame
        self.ma_earth  = np.matmul(inverse, self.ma_sensor) # zero-g in global frame

        v_a = v_a / np.linalg.norm(v_a)
        v_m = v_m / np.linalg.norm(v_m)
        self.v_x = np.cross(v_a, v_m) # cross-product of accel and magnetic field (cross vector)

        self.h = np.matmul(rotation, self.v_x)
        self.b = np.array([np.sqrt(self.h[0]*self.h[0] + self.h[1]*self.h[1]), 0, self.h[2]])

        self.v_hat_a = inverse[:,2] # estimated gravity vector
        self.v_hat_x = np.matmul(inverse, self.b) # estimated cross vector

        # the cross product $a x b$ gives a vector that points along the axis of rotation to move
        # the lh operand to the rh operand, with a magnitude $||a x b|| = ||a|| ||b|| |sin(\theta)|$
        # where $\theta$ is the angle between the vectors. When the vectors are normalized and the
        # angle is nearly zero, $a x b$ approximates the rotation vector from a to b.
        # see also eqs. (32c) and (48a) in Mahoney et al. 2008
        self.w_a = np.cross(v_a, self.v_hat_a) # discrepancy based on accelerometer reading
        self.w_x = np.cross(self.v_x, self.v_hat_x) # discrepancy based on cross vector
        self.w_mes = self.w_a * k_a + self.w_x * k_m

        # error correction is added to omega (angular rate) before integrating
        if k_I > 0.0:
            self.b_hat += self.static * self.w_mes * self.period # see eq. (48c)
            omega += k_P * self.w_mes + k_I * self.b_hat
        else:
            self.b_hat = np.zeros(3) # Madgwick: "prevent integral windup"
            omega += k_P * self.w_mes

        self.q.integrate(omega, self.period)
        return self.q
