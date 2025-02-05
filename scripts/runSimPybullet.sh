#!/bin/bash
source run_common.sh


#tmux select-pane -t 1
#tmux send-keys C-c ENTER
#sleep 0.5
#tmux send-keys C-c ENTER
#tmux send-keys ENTER
## Kill camera

#tmux kill-sess

tmux kill-session -t sim

if [ "$1" = "kill" ]; then
    echo "kill runSimPybullet"
    exit 1 
fi

if [ ! -v SIM ]
then
#tmux kill-session -t dronelab
#tmux new-session -d -s dronelab
PROJECT_PATH=../
else
PROJECT_PATH=/home/nanosub/proj/RovVision2/
#PYTHON=/miniconda/bin/python 
#tmux new-window

fi 

tmux new-session -d -s sim


#common for sim and hw
new_6_win
run 0 sim pybullet_bridge.py
sleep 2
run 1 onboard controller.py
#run 1 onboard sensors_gate.py
run 2 onboard "imGate.py -l"
run 3 onboard "sonGate.py -l"
sleep 1

tmux new-window
new_6_win
runLoop 0 plugins manual_plugin.py
runLoop 1 plugins depth_hold_plugin.py
runLoop 2 plugins att_hold_plugin.py
run 3 plugins oiTracker_plugin.py

#tmux new-window
#new_6_win
#run 0  plugins pos_hold_plugin.py
#run 1  onboard hw_stats.py

#only hw from here
if [ ! -v SIM ]
then 

FILE="/tmp/devusbmap.pkl"

while [ ! -f $FILE ];
do
   echo "detect usb connections"
   python3 ../utils/detect_usb.py
   sleep 1
done


tmux new-window
new_6_win

# run 0 sim pybullet_bridge.py
run 1 utils recorder.py
run 2 ground_control "rovViewer.py -s"
run 3 ground_control joy_rov.py
runShell 4 hw/sonar_docker "./run.sh demo"
#runShell 5 . jtop
tmux att
fi

