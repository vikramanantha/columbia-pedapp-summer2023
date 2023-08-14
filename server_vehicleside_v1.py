# Vikram Anantha
# Columbia Summer Internship - Summer 2023
# Mentored under Sharon Di and Yongjie Fu

# July 15 2023
# Server Code - Vehicle Side - Version 1
# Version 1 Framework

# THIS CODE IS MEANT TO BE RUN WITH server_pedside_v1.py and PedAppV1

# Summary: It reads in COSMOS vehicle data "frames", calculates the trajectories, and stores them


import helper_functions as hf
import glob
import json
import time
import random
from datetime import datetime

frames_pathnames_processed = set()
all_frames = []

frames_for_traj = 400 # how many of the last frames should be used in calculating the trajectory
demo_fps = 17
framespath = "/Users/markivanantha/Documents/Columbia Project/frames/frame_*.json"
savetrajpath = '/Users/markivanantha/Documents/Columbia Project/trajectories/realtime_traj.json'
messagetopic = "vikram/columbia/summer2023/fakecosmosdata"

## Collect and store the vehicle positions from the files ##
# This function isn't needed anymore, since the info is read from MQTT messages
# def collect_vehicle_pos_from_files(path_to_message, demo=False):
#     global all_frames
    
#     frame_pathnames = sorted(glob.glob(path_to_message)) # gets all the files in the format, sorted

#     for message_filename in frame_pathnames: 
#         if (message_filename not in frames_pathnames_processed): # if it hasn't been processed yet
#             # print("\n")
#             # print("Reading Message %s" % message_indx)

#             frame = hf.get_frame_from_file(message_filename)
#             all_frames.append(frame)
#             frames_pathnames_processed.add(message_filename)
#             # print("Processed %s" % (message_filename.split('/')[-1]))
#             if (demo): break
            
#             # print(frames_pathnames_processed)

#     # print(len(all_frames))
#     return all_frames

def collect_vehicle_pos_from_mqtt(client, userdata, msg):
    message = msg.payload.decode() # receive message
    message_json = json.loads(message)
    
    t = message_json['time']
    print(f"Message Received at time {datetime.fromtimestamp(t)}")
    
    frame = hf.get_frame_from_file_v2(message_json)
    
    
    all_frames.append(frame)
    # print(json.dumps(json.loads(message), indent=4))
    
    try:
        vehicle_trajs = calc_vehicle_trajs(all_frames)
        store_vehicle_trajs(vehicle_trajs, savetrajpath)
    except Exception as e:
        print("Exception!")
        print(e)
        input()


## Calculate the trajectories given the frames ##
def calc_vehicle_trajs(pos):
    coords = hf.get_coords_from_frames(pos, end_max=frames_for_traj)

    data = hf.generate_parametric_traj_from_coords(coords)
    
    data['t'] = pos[-1]['t'] # store the timestamp
    data['i'] = len(pos)
    # print("Frames processed!")
    return data


## Store the vehicle trajectories in a neatly organized json file for the other server code to read from ##
def store_vehicle_trajs(trajs, traj_file_pathname):
    file = open(traj_file_pathname, 'w')
    json.dump(
        trajs, 
        file, 
        indent=4 # "neatly organized"
    ) 
    file.close()

def start_mqtt():
    hf.setup(
        fport=1883, 
        ftopicreceive=messagetopic, 
    )
    client = hf.connect_mqtt()
    hf.setup_receiver(client)
    client.on_message = collect_vehicle_pos_from_mqtt
    client.loop_forever()

## Main code ##
def run(demo=False):
    start_mqtt()
    
    # while True:
    #     start = time.time()
    #     # vehicle_poss = collect_vehicle_pos_from_files(path_to_message = framespath, demo=demo)
    #     try:
    #         vehicle_trajs = calc_vehicle_trajs(vehicle_poss)
    #         store_vehicle_trajs(vehicle_trajs)
    #     except Exception as e:
    #         print("Exception!")
    #         print(e)
    #         input()
    #     # input()
    #     end = time.time()
    #     print("Loop in %s seconds" % (end-start))
    #     if demo: time.sleep(max(0, (1/demo_fps)))
        
run(demo=False)

# Demo is just for if I need to make a screenrecording from the test data
# Should be false in the real thing
# (I made it easy, all you have to do is turn run(demo=True) to false, and it should
#  trickle down the functions)