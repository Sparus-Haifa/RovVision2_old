#!/bin/bash
cmd="./sysRun.sh"

if [ "$1" = "demo" ]; then
    echo "demo mode"
    cmd="./runSimPybullet.sh"
fi

if [ "$1" = "local" ]; then
    echo "local"
    cmd="./run_ground_control.sh"
fi


docker run  \
    -it \
    --rm \
    --net=host \
    --env="DISPLAY" \
    --env="QT_X11_NO_MITSHM=1" \
    --volume="/tmp/.X11-unix:/tmp/.X11-unix:rw" \
    --privileged  \
    --volume="/home/zeged/proj/blueROV/RovVision2_old:/home/docker" \
    --volume="/var/run/docker.sock:/var/run/docker.sock" \
    --name rov \
    blue_rov /bin/bash -it -c \
    "cd scripts && \
    $cmd && \
    docker kill ros_sonar || true && \
    docker kill ros_sonar_reconfigure || true"

#  && docker kill ros_sonar_reconfigure