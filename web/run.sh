#!/bin/bash
server(){
	python3 app.py
}
until server; do
	echo "'server' crashed with exit code $?. Restarting">&2
	sleep 1
done
