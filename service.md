# Simple Service Setup

This shows how to create a very simple Apex service with systemd, allowing
Apex to start automatically when your Linux device is powered on

# Assumptions

1. This is focused on a Raspberry Pi and it is assumed you have a user called "pi".
1. Apex is installed in /home/pi/apex
1. Apex config (aka apex.yaml) is located at /home/pi/apex/apex.yaml
1. Apex logging (aka apex.log) is located at /home/pi/apex/apex.log

# Steps

1. sudo ln -s /home/pi/apex/apex.service /etc/systemd/system/apex.service
1. sudo systemctl enable apex
1. sudo systemctl start apex

# Verify

Reboot your linux machine and type

sudoo systemctl status apex

Also look at the log and verify it has entries matches the current time.   For example,

tail -n 50 -F /home/pi/apex/apex.log