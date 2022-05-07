#
# this dockerfile roughly follows the 'Ubuntu install of ROS Melodic' from:
#   http://wiki.ros.org/melodic/Installation/Ubuntu
#
# ARG BASE_IMAGE=nvcr.io/nvidia/l4t-base:r32.5.0
ARG BASE_IMAGE=ubuntu:bionic
FROM ${BASE_IMAGE}

# ARG ROS_PKG=ros_base
ARG ROS_PKG=desktop

ENV ROS_DISTRO=melodic
ENV ROS_ROOT=/opt/ros/${ROS_DISTRO}

ENV DEBIAN_FRONTEND=noninteractive

# WORKDIR /workspace
RUN mkdir -p /home/catkin_ws/src
WORKDIR /home/catkin_ws/src

# 
# add the ROS deb repo to the apt sources list
#
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
          git \
		cmake \
		build-essential \
		curl \
		wget \
		gnupg2 \
		lsb-release \
		ca-certificates \
    && rm -rf /var/lib/apt/lists/*

RUN sh -c 'echo "deb http://packages.ros.org/ros/ubuntu $(lsb_release -sc) main" > /etc/apt/sources.list.d/ros-latest.list'
RUN curl -s https://raw.githubusercontent.com/ros/rosdistro/master/ros.asc | apt-key add -


# 
# install ROS packages
#
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
		ros-melodic-`echo "${ROS_PKG}" | tr '_' '-'` \
		ros-melodic-image-transport \
		ros-melodic-vision-msgs \
          python-rosdep \
          python-rosinstall \
          python-rosinstall-generator \
          python-wstool \
    && rm -rf /var/lib/apt/lists/*






#
# init/update rosdep
#
RUN apt-get update && \
    cd ${ROS_ROOT} && \
    rosdep init && \
    rosdep update && \
    rm -rf /var/lib/apt/lists/*





RUN apt-get update
# opencv
RUN apt install -y libopencv-dev
RUN apt install -y ros-melodic-cv-bridge



# Blueprint Oculus Sonar
RUN git clone https://github.com/ipab-slmc/pybind11_catkin.git
WORKDIR /home/catkin_ws/src/pybind11_catkin
RUN rosdep install --from-paths ./ -iry


WORKDIR /home/catkin_ws/
RUN /bin/bash -c '. /opt/ros/melodic/setup.bash && catkin_make'
WORKDIR /home/catkin_ws/src






RUN git clone https://gitlab.com/apl-ocean-engineering/oculus_sonar_driver.git
RUN cd oculus_sonar_driver && git checkout 926eb59065b82cddbbf94f07469aebfa1c3720ed && cd ..
# RUN apt-get install -y python3-vcstool
# RUN vcs import --input oculus_sonar_driver/oculus_sonar_driver.rosinstall
RUN git clone https://github.com/apl-ocean-engineering/hydrographic_msgs.git
RUN cd hydrographic_msgs && git checkout 8a053bd4d14955363940e63c14e646d28da75504 && cd ..

RUN git clone https://gitlab.com/apl-ocean-engineering/g3log_ros.git
RUN cd g3log_ros && git checkout 65c63b96801d501bef852a8177d7c137a723ea54 && cd ..

RUN git clone https://github.com/apl-ocean-engineering/liboculus.git
RUN cd liboculus && git checkout 7f2f82b9b58c6f10e76f820f8313b4f387597e9d && cd ..

RUN git clone https://github.com/apl-ocean-engineering/sonar_image_proc.git
RUN cd sonar_image_proc && git checkout cdacfd3ba5234fa338dd6f5ffb0f243e86a79dd0 && cd ..


RUN git clone https://gitlab.com/apl-ocean-engineering/apl_msgs.git
RUN cd apl_msgs && git checkout e0dd91aecceb8e1fad932afcc1f142e5da5d52ff && cd ..


WORKDIR /home/catkin_ws/
# RUN /bin/bash -c '. /opt/ros/melodic/setup.bash && catkin_make --only-pkg-with-deps acoustic_msgs'
# RUN /bin/bash -c '. /opt/ros/melodic/setup.bash && catkin_make --only-pkg-with-deps apl_msgs hydrographic_msgs g3log_ros liboculus'
# # RUN cd src/sonar_image_proc && git checkout c07a263a15a5ec1d9f18d65745a5c4f440178104 && cd ..
# RUN cd src/sonar_image_proc && git checkout 79e547d89ffe934b0ae37c6eb3abbaf1213ac2f8 && cd ..
# RUN /bin/bash -c '. /opt/ros/melodic/setup.bash && catkin_make --only-pkg-with-deps sonar_image_proc'
# ADD CMakeLists.txt /home/catkin_ws/src/oculus_sonar_driver/CMakeLists.txt
# RUN /bin/bash -c '. /opt/ros/melodic/setup.bash && catkin_make -DCATKIN_WHITELIST_PACKAGES=""'
RUN /bin/bash -c '. /opt/ros/melodic/setup.bash && catkin_make'




# Dev / Debus tools
RUN apt-get install -y net-tools \
    nano \
    gedit \
    iputils-ping \
    netcat


# sonar_zmq pkg
RUN apt-get install -y python-pip
RUN pip install pyzmq
WORKDIR /home/catkin_ws/
# RUN mkdir -p /home/catkin_ws/src/sonar_zmq
ADD sonar_zmq /home/catkin_ws/src/sonar_zmq
RUN mkdir -p /home/bags
ADD bags/example.bag /home/bags



WORKDIR /home/catkin_ws/
RUN /bin/bash -c '. /opt/ros/melodic/setup.bash && catkin_make'










# # 
# # setup entrypoint
# #
# COPY ./packages/ros_entrypoint.sh /ros_entrypoint.sh

COPY ./ros_entrypoint.sh /


RUN echo 'source /opt/ros/${ROS_DISTRO}/setup.bash' >> /root/.bashrc
RUN echo "source /home/catkin_ws/devel/setup.bash" >> ~/.bashrc

# ENTRYPOINT ["/ros_entrypoint.sh"]
# CMD ["bash"]
# CMD ["roscore"]
# WORKDIR /
