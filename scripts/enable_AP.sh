#!/bin/bash

#Enable standalone AP mode
sudo systemctl enable hostapd dnsmasq
sudo cp /etc/dhcpcd.conf.enableAP /etc/dhcpcd.conf

echo "Rebooting in 5sec"
sleep 5
sudo reboot
