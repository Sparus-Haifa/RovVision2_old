#!/bin/bash
until ssh $REMOTE_SUB "echo"; do
    sleep 5
done
./ssh_route.sh