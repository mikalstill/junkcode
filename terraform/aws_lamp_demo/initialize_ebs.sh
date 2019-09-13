#!/bin/bash

device=/dev/xvdd

blockid=`blkid ${device}`
if [ "%${blockid}%" == "%%" ]
then
  echo "Initializing EBS volume"
  parted --script ${device} \
    mklabel gpt \
    mkpart primary 1MiB 1000MiB
  systemctl restart udev
  mkfs -t ext4 ${device}1

  export `blkid -o export ${device}1`
  echo "UUID=\"${UUID}\" /srv ext4 defaults,discard 0 2" >> /etc/fstab
fi

mount /srv