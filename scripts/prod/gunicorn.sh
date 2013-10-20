#!/bin/bash
cd $(git rev-parse --show-toplevel)
source bin/activate
cd app
nohup gunicorn app:app -w 4 -b 0.0.0.0:5000 &
