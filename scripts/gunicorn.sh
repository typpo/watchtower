#!/bin/bash
cd `dirname $0`
cd ../app
nohup gunicorn app:app -w 4 -b 0.0.0.0:5000 &