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

#### CHANGE THESE VARIABLES ACCORDINGLY #####

# veh_topic_receive = "vikram/columbia/summer2023/fakecosmosdata"
veh_topic_receive = "carla/detection"
# veh_topic_receive = "cosmos12f/trajs"
futurecoords_path = '/Users/markivanantha/Documents/Columbia Project/trajectories/realtime_futurecoords.json'
# broker='broker.emqx.io'
broker='broker.hivemq.com'


frames_pathnames_processed = set()
all_frames = []

times1 = []
times2 = []
times3 = []

data = {}

## Receive the MQTT message with the vehicle information ##
def collect_vehicle_pos_from_mqtt(client, userdata, msg):
    message = msg.payload.decode() # receive message
    message_json = json.loads(message)
    
    # t = message_json['start_time']
    t = time.time()
    # times1.append(time.time() - t)
    
    print(f"Message Received at time {datetime.fromtimestamp(t)}")
    
    
    
    frame = hf.get_frame_from_file_v3(message_json)
    # times2.append(time.time() - t)
    store_vehicle_fc(
        data=frame,
        traj_file_pathname=futurecoords_path
    )
    # times3.append(time.time() - t)
    
    # print("Avg Time from camera feed to received mqtt message:", hf.avg(times1))
    # data[hf.epoch_to_timestamp(time.time())] = {
    #             'avg time camera -> receive mqtt': times1[-1],
    #             'avg time camera -> process mqtt': times2[-1],
    #             'avg time camera -> store fcs': times3[-1],
    #     }
    # with open('/Users/markivanantha/Documents/Columbia Project/fieldservertestdata_v2.json', 'w') as file:
    #     json.dump(data, file, indent=4)
    # print("Avg Time2:", hf.avg(times2))
    # print("Avg Time3:", hf.avg(times3))



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
        fbroker=broker
    )
    client = hf.connect_mqtt()
    hf.setup_receiver(client)
    client.on_message = collect_vehicle_pos_from_mqtt
    client.loop_forever()

## Main code ##
def run():
    start_mqtt()
    
        
run()
