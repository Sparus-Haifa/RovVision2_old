#!/bin/bash

auto=""
if [ "$1" = "auto" ]; then
    echo "auto"
    auto="auto"
fi

CMD="cd proj/RovVision2/scripts && ./run_onboard.sh $auto"
echo "running $CMD"
./sync_onboard.sh && sleep 1 && ssh -t $REMOTE_SUB $CMD
