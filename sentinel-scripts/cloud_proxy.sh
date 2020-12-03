#!/bin/bash
echo “Started bar.sh”
echo “Started foo.sh”
./foo.sh &
pid=$!
wait $pid
echo “Completed foo.sh”

