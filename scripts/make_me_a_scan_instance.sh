#!/bin/bash -e

echo "127.0.0.1 watchtower-scan" >> sudo tee -a /etc/hosts
sudo hostname "watchtower-scan"
