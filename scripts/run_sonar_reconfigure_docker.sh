DOCKER_COMMON_ARGS="--gpus all --env=NVIDIA_VISIBLE_DEVICES=all --env=NVIDIA_DRIVER_CAPABILITIES=all --env=DISPLAY --env=QT_X11_NO_MITSHM=1 -v /tmp/.X11-unix:/tmp/.X11-unix:rw"



# check if the sonar is publishing data
# if it is, then run the reconfigure tool
# if it is not, then wait a bit and try again
while true; do
    if docker run \
    -it \
    --rm \
    --net=host \
    --privileged \
    $DOCKER_COMMON_ARGS \
    --env ROS_MASTER_URI=http://192.168.3.10:11311 \
    --env ROS_IP=192.168.3.10 \
    --env ROS_HOSTNAME=192.168.3.10 \
    --name ros_sonar_reconfigure \
    osrf/ros:melodic-desktop-full \
    /bin/bash -c 'echo \"192.168.3.10      nanosubJet\" >> /etc/hosts && \
    source /opt/ros/melodic/setup.bash && \
    rostopic echo /oculus/drawn_sonar -n 1'; then
        echo "sonar is publishing data"
        break
    else
        echo "sonar is not publishing data"
        sleep 1
    fi
done




docker run \
    -it \
    --rm \
    --net=host \
    --privileged \
    $DOCKER_COMMON_ARGS \
    --env ROS_MASTER_URI=http://192.168.3.10:11311 \
    --env ROS_IP=192.168.3.11 \
    --env ROS_HOSTNAME=192.168.3.11 \
    --name ros_sonar_reconfigure \
    osrf/ros:melodic-desktop-full \
    /bin/bash -c 'echo "192.168.3.10      nanosubJet" >> /etc/hosts && \
    source /opt/ros/melodic/setup.bash && \
    rosrun rqt_reconfigure rqt_reconfigure'


# /bin/bash

# /bin/bash -c 'echo "192.168.3.10      nanosubJet" >> /etc/hosts' && \
    
    #  && \
    
# source /opt/ros/melodic/setup.bash && \
# rosrun rqt_reconfigure rqt_reconfigure


# cat etc/hosts \

# rostopic info /oculus/drawn_sonar


# rosparam set /oculus/oculus_sonar_driver/gain 200