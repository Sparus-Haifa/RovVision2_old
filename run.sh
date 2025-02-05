#!/bin/bash
cmd="./sysRun.sh"

if [ "$1" = "demo" ]; then
    echo "demo mode"
    cmd="./runSimPybullet.sh"
fi

if [ "$1" = "local" ]; then
    echo "local"
    cmd="./run_ground_control.sh local"
fi

if [ "$1" = "bash" ]; then
    echo "bash"
    cmd="/bin/bash"
fi

if [ "$1" = "auto" ]; then
    echo "auto"
    cmd="./run_remote.sh auto && tmux att"

fi


# --volume="${PWD}:/home/docker" \
# --gpus="all" \
docker run  \
    -it \
    --rm \
    --net=host \
    --env="DISPLAY" \
    --env="QT_X11_NO_MITSHM=1" \
    --volume="/tmp/.X11-unix:/tmp/.X11-unix:rw" \
    --privileged  \
    --mount type=bind,source="${PWD}",target=/home/docker,bind-propagation=shared \
    --env DIND_USER_HOME=${PWD} \
    --volume="/var/run/docker.sock:/var/run/docker.sock" \
    --volume="/dev/bus/usb:/dev/bus/usb" \
    --volume="/dev:/dev" \
    --volume="/proc:/proc" \
    --name rov \
    blue_rov /bin/bash -it -c \
    "cd scripts && \
    $cmd || \
    ./sysRun.sh kill && \
    docker kill ros_sonar || true && \
    docker kill ros_sonar_reconfigure || true"

#  && docker kill ros_sonar_reconfigure
# -v $HOME/.ssh:/home/user/.ssh:ro \