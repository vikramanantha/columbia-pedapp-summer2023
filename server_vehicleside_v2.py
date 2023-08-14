# Vikram Anantha
# Columbia Summer Internship - Summer 2023
# Mentored under Sharon Di and Yongjie Fu

# Aug 9 2023
# Server Code - Vehicle Side - Version 2
# Version 1 Framework

# THIS CODE IS MEANT TO BE RUN WITH server_pedside_v2.py and PedAppV1

import helper_functions as hf
import glob
import json
import time
import random
from datetime import datetime


veh_topic_receive = "vikram/columbia/summer2023/fakecosmosdata"
futurecoords_path = '/Users/markivanantha/Documents/Columbia Project/trajectories/realtime_futurecoords.json'


frames_pathnames_processed = set()
all_frames = []

## Receive the MQTT message with the vehicle information ##
def collect_vehicle_pos_from_mqtt(client, userdata, msg):
    message = msg.payload.decode() # receive message
    message_json = json.loads(message)
    
    t = message_json['time']
    print(f"Message Received at time {datetime.fromtimestamp(t)}")
    
    frame = hf.get_frame_from_file_v3(message_json)
    
    store_vehicle_fc(
        data=frame,
        traj_file_pathname=futurecoords_path
    )



## Store the vehicle future coords in a neatly organized json file for the other server code to read from ##
def store_vehicle_fc(data, traj_file_pathname):
    file = open(traj_file_pathname, 'w')
    json.dump(
        data, 
        file, 
        indent=4 # "neatly organized"
    ) 
    file.close()


## Open up MQTT Client ##
def start_mqtt():
    hf.setup(
        fport=1883, 
        ftopicreceive=veh_topic_receive, 
    )
    client = hf.connect_mqtt()
    hf.setup_receiver(client)
    client.on_message = collect_vehicle_pos_from_mqtt
    client.loop_forever()

## Main code ##
def run():
    start_mqtt()
    
        
run()
