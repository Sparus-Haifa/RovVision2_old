docker build -t blue_rov --build-arg VARIANT=ubuntu-20.04 docker/.
cd hw/sonar_docker && ./build.sh && cd ..
docker pull osrf/ros:melodic-desktop-full