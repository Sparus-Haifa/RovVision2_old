docker run --rm --privileged multiarch/qemu-user-static --reset -p yes
docker build $1 -t ros_sonar .
