#!/bin/bash

sudo docker run -it --rm --net=ros --env="DISPLAY=novnc:0.0" -p 5900:5900 --gpus all turtlebot2
