#!/bin/bash

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
    $@"

#  && docker kill ros_sonar_reconfigure
# -v $HOME/.ssh:/home/user/.ssh:ro \

# echo $@