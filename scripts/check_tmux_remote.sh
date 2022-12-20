#!/bin/bash

# a script to check if tmux is running on remote

if ssh $REMOTE_SUB "tmux info &> /dev/null"; then 
    echo running
    exit 0
else
    echo not running
    exit 1
fi