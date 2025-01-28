# FROM ubuntu:20.04
# FROM ubuntu:bionic
# FROM python:3.7
# [Choice] Ubuntu version (use ubuntu-22.04 or ubuntu-18.04 on local arm64/Apple Silicon): ubuntu-22.04, ubuntu-20.04, ubuntu-18.04
# ARG VARIANT="jammy"
# FROM mcr.microsoft.com/vscode/devcontainers/base:0-${VARIANT}

FROM ubuntu:18.04
# FROM ubuntu:16.04



# nvidia-container-runtime
ENV NVIDIA_VISIBLE_DEVICES \
    ${NVIDIA_VISIBLE_DEVICES:-all}
ENV NVIDIA_DRIVER_CAPABILITIES \
    ${NVIDIA_DRIVER_CAPABILITIES:+$NVIDIA_DRIVER_CAPABILITIES,}graphics

# ENV DEBIAN_FRONTEND=noninteractive
ARG DEBIAN_FRONTEND=noninteractive


RUN apt-get update && \
    apt-get -qy full-upgrade && \
    apt-get install -qy curl && \
    apt-get install -qy curl && \
    curl -sSL https://get.docker.com/ | sh


######## some base installs ########
RUN apt-get update && apt-get -y upgrade
RUN apt-get -y install gawk git
RUN apt-get -y install xterm
RUN apt-get -y install build-essential
RUN apt-get -y install curl
RUN apt-get -y install vim
RUN apt-get -y install wget tmux
RUN apt-get -y install bash-completion
RUN apt-get -y install python3-pip
# RUN apt-get -y install ipython3
RUN apt-get -y install locate
RUN apt-get -y install net-tools
RUN apt-get -y install usbutils
# RUN apt-get update && DEBIAN_FRONTEND="noninteractive" TZ="Asia/Jerusalem" apt-get -y install git-cola
RUN apt-get -y install software-properties-common
RUN apt-get -y install libasound-dev
RUN apt-get -y install mesa-utils 
RUN apt-get -y install libgl1-mesa-glx
# RUN apt-get -y install ipython
RUN apt-get update && DEBIAN_FRONTEND="noninteractive" TZ="Asia/Jerusalem" apt-get -y install python3-tk
RUN apt-get -y install libjpeg-dev zlib1g-dev
#RUN apt-get update

RUN apt-get -y install libgtk2.0-dev

#RUN apt-get update && apt-get -y upgrade
#RUN pip3 install --upgrade pip

# RUN pip3 install scikit-build
RUN pip3 install git+https://github.com/scikit-build/scikit-build.git@56273a249f48cf0701cd20f733e8379c3587aacb
#==0.14.0
RUN apt-get update
RUN python3 -m pip install --upgrade pip
RUN pip3 install cmake
RUN pip3 install pybullet 
RUN pip3 install pygame 
#RUN pip3 install opencv-contrib-python 
RUN pip3 install dill zmq scikit-image matplotlib
RUN pip3 install numpy
#==1.21.4
# ENV CMAKE_MAKE_PROGRAM="make -j `nproc`"
# RUN pip3 install --upgrade pip
RUN python3 -V
RUN apt install -y libavcodec-dev libavformat-dev libavdevice-dev libavfilter-dev
RUN MAKEFLAGS="-j $(nproc)" CMAKE_ARGS="-DOPENCV_ENABLE_NONFREE=ON -DOPENCV_FFMPEG_USE_FIND_PACKAGE=FFMPEG -DOPENCV_FFMPEG_SKIP_DOWNLOAD=on -DOPENCV_FFMPEG_SKIP_BUILD_CHECK=on" pip3 install -v --no-binary=opencv-contrib-python opencv-contrib-python==4.5.3.56
#RUN pip3 install opencv-python 

# ENV DEBIAN_FRONTEND=

ENV ROV_TYPE=4
ENV ROV_IP=192.168.3.10
ENV WORK_DIR=/home/docker INSTALL_DIR=/opt
WORKDIR ${WORK_DIR}

######## limesdr install ###########
#packages for soapysdr available at myriadrf PPA
RUN add-apt-repository -y ppa:myriadrf/drivers
RUN apt-get update

#install core library and build dependencies
RUN apt-get -y install git g++ cmake libsqlite3-dev

# docker x11
RUN apt-get install -y gedit
RUN apt-get install -y x11-xserver-utils



# pyueye
## https://github.com/BackupGGCode/pyueye
## https://code.google.com/archive/p/pyueye/downloads
RUN apt-get update && apt-get install -y udev
COPY hw/idsCam/uEye_Linux_350_64Bit/ueyesdk-setup-3.50-usb-amd64.gz.run /
RUN chmod +x /ueyesdk-setup-3.50-usb-amd64.gz.run
RUN /ueyesdk-setup-3.50-usb-amd64.gz.run
RUN pip3 install pyueye

RUN apt-get clean
RUN apt-get autoclean
RUN apt-get autoremove -y


# ######## user settings ######
# RUN apt-get install sudo
# RUN useradd -u 1000 docker
# RUN echo "docker:docker" | chpasswd
# RUN echo "root:root" | chpasswd
# RUN echo 'root:Docker!' | chpasswd
# RUN echo "docker ALL=(ALL:ALL) NOPASSWD:ALL" >> /etc/sudoers

# USER docker

# #RUN sudo udevadm control --reload-rules || echo "done" 
# #RUN udevadm trigger

# # All users can use /home/user as their home directory
# ENV HOME=/home/docker

# WORKDIR /home/docker


# ####### handle limesdr-mini rules and permissions
# RUN sudo usermod -a -G plugdev docker
# RUN sudo usermod -aG root docker

# RUN sudo chown -R docker:docker /home/docker
# #RUN sudo service udev restart



# USER vscode
RUN apt-get update && apt-get install -y openssh-client

# RUN useradd -m user
RUN mkdir -p /home/root/.ssh
# COPY id_rsa_shared /root/.ssh/id_rsa
# COPY id_rsa_shared.pub /root/.ssh/id_rsa.pub

# RUN echo "test"

COPY id_rsa /root/.ssh/id_rsa
COPY id_rsa.pub /root/.ssh/id_rsa.pub

RUN eval `ssh-agent -s` && chmod 600 /root/.ssh/id_rsa  && ssh-add /root/.ssh/id_rsa


# RUN pip3 install pyueye
# COPY info.txt /home/user/

# COPY run.sh /home/user/
# ADD id_rsa_shared /home/user/.ssh/id_rsa

# RUN chown -R root:root /root/.ssh
RUN echo "Host remotehost\n\tStrictHostKeyChecking no\n" >> /root/.ssh/config
RUN ssh-keyscan -H 192.168.3.10 >> ~/.ssh/known_hosts

RUN apt-get install -y rsync

RUN echo 'export REMOTE_SUB=nanosub@192.168.3.10' >> ~/.bashrc
RUN echo 'export ROV_TYPE=4' >> ~/.bashrc 


# RUN python3 -m pip install --upgrade pip setuptools wheel
# RUN pip3 install pyueye==4.90.0.0


# RUN apt-get install -y python-pip python-dev
# RUN pip install pyueye==4.90.0.0




# USER user
# CMD ["/bin/bash"]


# ARG USER_ID
# ARG GROUP_ID

# RUN addgroup --gid $GROUP_ID user
# RUN adduser --disabled-password --gecos '' --uid $USER_ID --gid $GROUP_ID user
# USER user

# find pairs dependencies
RUN pip3 install pandas
RUN pip3 install natsort
RUN pip3 install sklearn
RUN pip3 install scikit-learn 



# moviePy depends:
# RUN apt-get install -y imageio



RUN apt-get update && apt-get install joystick -y