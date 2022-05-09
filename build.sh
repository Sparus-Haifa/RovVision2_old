docker build -t blue_rov --build-arg VARIANT=ubuntu-20.04 --build-arg USER_ID=$(id -u) --build-arg GROUP_ID=$(id -g) . && \
cd hw/sonar_docker && ./build.sh && cd .. && \
docker pull osrf/ros:melodic-desktop-full