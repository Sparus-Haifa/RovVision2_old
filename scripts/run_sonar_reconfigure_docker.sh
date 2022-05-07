DOCKER_COMMON_ARGS="--gpus all --env=NVIDIA_VISIBLE_DEVICES=all --env=NVIDIA_DRIVER_CAPABILITIES=all --env=DISPLAY --env=QT_X11_NO_MITSHM=1 -v /tmp/.X11-unix:/tmp/.X11-unix:rw"
docker run \
    -it \
    --rm \
    --net=host \
    --privileged \
    $DOCKER_COMMON_ARGS \
    --name ros_sonar_reconfigure \
    osrf/ros:melodic-desktop-full \
    rosrun rqt_reconfigure rqt_reconfigure