#!/usr/bin/env python3

import asyncio
import bleak
import random as rand
import json
import time
import sys
import socket

blacklist = set()
values = []

serviceUUID = "b82ab3fc-1595-4f6a-80f0-fe094cc218f9"
readUUID = "b82ab3fc-1595-4f6a-80f0-fe094cc218f9"

async def scan(blacklist):
    print("Beginning scan")
    addresses = set()
    devices = await bleak.BleakScanner.discover()

    for d in devices:
        addresses.add(d.address)

    blacklist = blacklist.intersection(addresses)
    addresses -= blacklist  # filter out static devices

    print(f"Scan complete\nFound addresses {addresses}")
    return blacklist, addresses

async def write_gatt(blackist, address, value):
    try:
        print(f"Attempting to write to address {address}")
        async with bleak.BleakClient(address) as client:
            service_collection = await client.get_services()
            services = service_collection.services

            # known bug in implementation of COVIDSafe causes
            # multiple duplicate services whenever Bluetooth is turned on or off
            # so we can't just search by UUID
            for service in services:
                if services[service].uuid == serviceUUID:
                    readChar = services[service].get_characteristic(readUUID)
                    writeChar = services[service].get_characteristic(writeUUID)
                    break

            charVal = await client.read_gatt_char(readChar)
            charVal = json.loads(charVal.decode())
            #TODO remove or true when done testing
            if (value["id"] != charVal["id"] or True): # make sure not to send ID back to same device
                a = await client.write_gatt_char(writeChar, value)
            else:
                print("Can't write to origin device")

    except Exception as e: # rule out all devices which aren't running the app
        blacklist.add(address)
        print(f"Failed to write because of exception {e}")

def scan_task(loop, blacklist):
    task = loop.create_task(scan(blacklist))
    loop.run_until_complete(task)
    return task.result()

def write_task(loop, addresses, blacklist):
    for address in addresses:
        if address not in blacklist:
            randVal = rand.randint(0, len(values) - 1)
            task = loop.create_task(write_gatt(blacklist, address, values[randVal][0]))
            loop.run_until_complete(task)


if __name__ == "__main__":
    if (len(sys.argv) != 2):
        print("Usage: replay port")
        exit()

    ip = "localhost"
    port = int(argv[1])

    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        s.bind((ip, port))
        s.listen()
        conn, addr = s.accept()

        loop = asyncio.get_event_loop()
        while True:
            data = conn.recv(1024)
            data = data.decode().split(",")
            for i in range(len(data)):
                data[i] = bytearray(data[i], encoding="utf-8")

            # Discover devices
            blacklist, new_addresses = scan_task(blacklist)
            write_task(loop, blacklist, new_addresses)
