import rclpy
import sys

import numpy as np
import cv2
import threading
import time
from datetime import datetime

from interfaces.camera import ListenerCamera
from interfaces.motors import PublisherMotors
from interfaces.laser import ListenerLaser
from interfaces.pose3d import ListenerPose3d

from shared.image import SharedImage
from shared.value import SharedValue

# Hardware Abstraction Layer


class HAL:
    IMG_WIDTH = 320
    IMG_HEIGHT = 240

    def __init__(self):
        print("HAL initializing", flush=True)
        rclpy.init(args=sys.argv)
        rclpy.create_node('HAL')

        # Shared memory variables
        self.shared_image = SharedImage("halimage")
        self.shared_v = SharedValue("velocity")
        self.shared_w = SharedValue("angular")
        self.shared_laserdata = []
        for i in range(360):
            name = "laserdata" + str(i)
            self.shared_laserdata.append(SharedValue(name))

        # ROS Topics
        self.motors = PublisherMotors("/cmd_vel", 4, 0.3)
        self.camera = ListenerCamera("/depth_camera/image_raw")
        self.laser = ListenerLaser("/scan")
        self.odometry = ListenerPose3d("/odom")

        self.start_time = 0

        # Update thread
        self.thread = ThreadHAL(self.update_hal)
        print("HAL initialized", flush=True)

    # Function to start the update thread
    def start_thread(self):
        print("HAL thread starting", flush=True)
        self.start_time = time.time()
        self.thread.start()

    def getLaserData(self):
        try:
            rclpy.spin_once(self.laser)
            values = self.laser.getLaserData().values
            for i in range(360):
                self.shared_laserdata[i].add(values[i])
        except Exception as e:
            print(f"Exception in hal getImage {repr(e)}")

    def getPose3d(self):
        return self.odometry.getPose3d()

    # Get Image from ROS Driver Camera
    def getImage(self):
        try:
            rclpy.spin_once(self.camera)
            image = self.camera.getImage().data
            self.shared_image.add(image)
        except Exception as e:
            print(f"Exception in hal getImage {repr(e)}")

    # Set the velocity
    def setV(self):
        velocity = self.shared_v.get()
        self.motors.sendV(velocity)

    # Get the velocity
    def getV(self):
        velocity = self.shared_v.get()
        return velocity

    # Get the angular velocity
    def getW(self):
        angular = self.shared_w.get()
        return angular

    # Set the angular velocity
    def setW(self):
        angular = self.shared_w.get()
        self.motors.sendW(angular)

    def update_hal(self):
        self.getLaserData()
        self.getImage()
        self.setV()
        self.setW()

    # Destructor function to close all fds
    def __del__(self):
        self.shared_image.close()
        self.shared_v.close()
        self.shared_w.close()
        self.shared_laserdata.close()


class ThreadHAL(threading.Thread):
    def __init__(self, update_function):
        super(ThreadHAL, self).__init__()
        self.time_cycle = 80
        self.update_function = update_function

    def run(self):
        print("Starting HAL thread", flush=True)
        while (True):
            start_time = datetime.now()

            # print(f"Calling update function inside hal thread")
            self.update_function()

            finish_time = datetime.now()

            dt = finish_time - start_time
            ms = (dt.days * 24 * 60 * 60 + dt.seconds) * \
                1000 + dt.microseconds / 1000.0

            if (ms < self.time_cycle):
                time.sleep((self.time_cycle - ms) / 1000.0)
