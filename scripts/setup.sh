#!/bin/bash

pushd `dirname $0`

sudo apt-get install python-virtualenv python-pip unzip
sudo apt-get install xvfb
sudo apt-get install xserver-xephyr
sudo apt-get install tightvncserver
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
python tests/basic_selenium_chrome.py

echo "run 'source bin/active' to enter virtualenv"

popd
