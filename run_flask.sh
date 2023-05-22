#!/bin/bash
# Find the process ID of the program that is listening on port 5000
pid=$(sudo netstat -tulpn | grep :5000 | awk '{print $7}' | cut -d/ -f1)
# If the process ID is not empty, kill the process
if [ -n "$pid" ]; then
    sudo kill -9 $pid
fi
# 运行git pull命令拉取最新代码
git pull
# Run flask run command in the background
nohup flask run --host 0.0.0.0 --port 5000 > app.log 2>&1 &