#!/bin/bash

sudo timeout -s SIGINT 5s hcitool -i hci0 lescan | grep : | cut -d ' ' -f1 | sort | uniq > addresses.txt

echo "Found addresses:"
cat addresses.txt

addresses=$(cat addresses.txt)
for address in $addresses
do
    echo Testing address $address
    gatttool -t random -b $address  --char-read --uuid=b82ab3fc-1595-4f6a-80f0-fe094cc218f9
done
