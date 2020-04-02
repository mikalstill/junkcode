#!/bin/bash

# Extract a cinder volume via glance
#
# For example: ./cinder_exporter.sh "node1 for customer"
# 
# You're left with a file named for the cinder UUID of the volume

cinder_uuid=`cinder list 2> /dev/null | grep "$1" | tr -s " " | cut -f 2 -d " "`
echo "Cinder UUID is $cinder_uuid"

if [ -e images/$cinder_uuid.done ]
then
  echo "Volume already fetched"
  exit 1
fi

echo "Starting export to glance"
cinder upload-to-image $cinder_uuid "extract:$cinder_uuid" 2> /dev/null
sleep 10

glance_uuid=`glance image-list | grep "extract:$cinder_uuid" | tr -s " " |  cut -f 2 -d " "`
echo "Glance UUID is $glance_uuid"

if [ "%$glance_uuid%" == "%%" ]
then
  echo "Extraction failed"
  exit 1
fi

glance_state=`glance image-show $glance_uuid | grep status | tr -s " " |  cut -f 4 -d " "`
echo "Glance state is $glance_state"
while [ "$glance_state" != "active" ]
do
  echo "...waiting (state is $glance_state)"
  sleep 10
  glance_state=`glance image-show $glance_uuid | grep status | tr -s " " |  cut -f 4 -d " "`
done
echo "Glance state is $glance_state"

echo "Downloading image"
glance image-download --file images/$cinder_uuid.raw --progress $glance_uuid

echo "Cleaning up"
glance image-delete $glance_uuid
echo "Done"
touch images/$cinder_uuid.done