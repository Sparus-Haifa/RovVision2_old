demo=false
if [ "$1" = "demo" ]; then
    echo "demo mode"
    # exit 1 
    demo=true
fi
docker run \
    -it \
    --rm \
    --net=host \
    --env="DISPLAY" \
    --env="QT_X11_NO_MITSHM=1" \
    --volume="/tmp/.X11-unix:/tmp/.X11-unix:rw" \
    --privileged \
    --name ros \
    ros_sonar_image /bin/bash -it -c "roslaunch sonar_zmq run.launch demo:=$demo"