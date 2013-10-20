#!/bin/bash

pushd `dirname $0`

sudo apt-get update
sudo apt-get install python-virtualenv python-pip unzip build-essential python-dev unzip xvfb xserver-xephyr postgresql postgresql-client postgresql-server-dev-all sqlite3
#sudo apt-get install tightvncserver
cd ..
virtualenv .
source bin/activate
pip install -r requirements.txt

# assuming 64 bit
# doing chrome
wget https://dl.google.com/linux/direct/google-chrome-stable_current_amd64.deb
sudo dpkg -i ./google-chrome*.deb
sudo apt-get -f install

wget https://chromedriver.googlecode.com/files/chromedriver_linux64_26.0.1383.0.zip
unzip chromedriver*
sudo mv chromedriver /usr/bin

#python tests/basic_selenium.py
python tests/server_chrome.py

mkdir /tmp/watchtower

# postgres stuff
echo "Creating postgres watchtower user..."
sudo -u postgres createuser --superuser watchtower
echo "Type '\password watchtower' to set a password, then press ctrl-D:"
sudo -u postgres psql

sudo -u postgres createdb watchtower

echo "run 'source bin/active' to enter virtualenv"

popd
