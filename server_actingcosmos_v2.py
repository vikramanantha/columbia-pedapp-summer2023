# Vikram Anantha
# Columbia Summer Internship - Summer 2023
# Mentored under Sharon Di and Yongjie Fu

# Aug 10 2023
# Acting COSMOS Server Code
#      Code Version 1
# Framework Version 2
# THIS CODE IS MEANT TO BE RUN WITH server_v2.py and PedAppV1

# NOTE:
# This code is meant to act as the COSMOS server sending out data about the vehicles
# This code is not meant to be part of the official framework

# Summary: It takes previously stored COSMOS data, and sends it out via MQTT


## IMPORTS ##
import random
import time
import json
import uuid
import source
import os
from paho.mqtt import client as mqtt_client
from datetime import datetime
import math
import helper_functions as hf
import glob

## GLOBAL VARIABLES ##

sendtopic = "vikram/columbia/summer2023/fakecosmosdata"
framespath = "frames/frames_aug82023/frame_*.json"
sendingdelay = 2
    

## MAIN CODE ##
def publish(client):
    
    frames = sorted(glob.glob(framespath))
    
    for frame in frames:
        with open(frame, 'r') as f:
            hf.send(client, json.dumps(json.load(f)), verbose=True, topic_send=hf.sendtopic)
        time.sleep(sendingdelay)

## RUN THIS CODE ##
def run():
    hf.setup(ftopicsend=sendtopic, fbroker='broker.hivemq.com')
    client = hf.connect_mqtt()
    client.loop_start()
    publish(client)


if __name__ == '__main__':
    run()