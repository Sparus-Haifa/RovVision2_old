#!/bin/bash

# a script to check if tmux is running
# return 0 if running, 1 if not

if tmux info &> /dev/null; then 
    echo running
    exit 0
else
    echo not running
    exit 1
fi