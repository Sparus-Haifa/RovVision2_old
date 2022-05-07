#!/bin/bash
#script to run with a host network
export ROS_MASTER_URI=http://$(hostname --ip-address):11311
export ROS_HOSTNAME=$(hostname --ip-address)
# setup ros environment
source "/opt/ros/$ROS_DISTRO/setup.bash"
source "/home/catkin_ws/devel/setup.bash"
#roslaunch sonar_zmq run.launch demo:=true