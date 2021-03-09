#!/bin/bash
source run_common.sh

tmux kill-ser


PROJECT_PATH=/home/host/projects/RovVision2/
#PYTHON=${1:-/miniconda/bin/python}

#[ $USER == 'uav' ] && export RESIZE_VIEWER=1500
[ $USER == 'uav' ] && export RESIZE_VIEWER=2300

if [ ! -v SIM ]
then
tmux kill-session -t dronelab
tmux new-session -d -s dronelab
PYTHON=/bin/python3
PROJECT_PATH=../
else
tmux new-window
fi 

new_4_win
runShell 0 scripts ./ssh_route.sh
sleep 1
run 1 ground_control joy_rov.py
run 2 ground_control "viewer.py --pub_data --udp"
#run 2 web "--version && FLASK_APP=server.py flask run"
#run 3 web "--version && sleep 3 && firefox http://127.0.0.1:5000/static/html/ropedive.html --new-window  --new-tab -url http://127.0.0.1:5000/static/html/checklists.html"
if [ ! -v SIM ]
then 
tmux att
fi
