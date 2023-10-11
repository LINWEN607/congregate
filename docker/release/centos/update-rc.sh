#!/bin/bash

# Setup the bashrc

echo 'if [ -z "$(ps aux | grep mongo | grep -v grep)" ]; then sudo mongod --fork --logpath /var/log/mongodb/mongod.log; fi' >> ~/.bashrc
echo 'if [ -z "$(ps aux | grep mongo | grep -v grep)" ]; then sudo mongod --fork --logpath /var/log/mongodb/mongod.log; fi' >> ~/.zshrc
echo "alias python='python3.8'" >> ~/.bashrc
echo "alias python='python3.8'" >> ~/.zshrc
echo "alias python3='python3.8'" >> ~/.bashrc
echo "alias python3='python3.8'" >> ~/.zshrc
echo "alias pip='python3.8 -m pip'" >> ~/.bashrc
echo "alias pip='python3.8 -m pip'" >> ~/.zshrc
echo "alias ll='ls -al'" >> ~/.bashrc
echo "alias ll='ls -al'" >> ~/.zshrc
echo "alias license='cat /opt/congregate/LICENSE'" >> ~/.bashrc
echo "alias license='cat /opt/congregate/LICENSE'" >> ~/.zshrc
