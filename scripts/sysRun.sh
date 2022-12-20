#!/bin/bash


tmux kill-ser
sleep 1

if [ "$1" = "kill" ]; then
    echo "kill all system"
    ssh $REMOTE_SUB "tmux kill-ser"
    exit 1
fi


# run remote code only if tmux is not running
if ssh $REMOTE_SUB "tmux info &> /dev/null"; then 
    echo remote tmux is running
    # exit 0
else
    echo remote tmux is not running
    # exit 1
    ./run_remote.sh
    sleep 10
fi

./run_ground_control.sh
