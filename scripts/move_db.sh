#!/bin/bash
sudo mkdir -p /var/watchtower
sudo chown `whoami` /var/watchtower/
cp /tmp/watchtower.db /var/watchtower/ || true
