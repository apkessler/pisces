#!/bin/bash

#Enable standalone AP mode
sudo systemctl disable hostapd dnsmasq
sudo cp /etc/dhcpcd.conf.default /etc/dhcpcd.conf

echo "Rebooting in 5sec"
sleep 5
sudo reboot
