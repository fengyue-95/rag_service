#!/bin/bash

# 端口号
PORT=8000

# 查找占用端口的进程
PID=$(lsof -ti:$PORT)

if [ -n "$PID" ]; then
    echo "端口 $PORT 被进程 $PID 占用，正在终止..."
    kill -9 $PID
    echo "进程 $PID 已终止"
else
    echo "端口 $未被占用"
fi

# 启动应用
echo "正在启动应用..."
.venv/bin/python main.py