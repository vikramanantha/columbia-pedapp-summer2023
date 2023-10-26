# Vikram Anantha
# Columbia Summer Internship - Summer 2023
# Mentored under Sharon Di and Yongjie Fu

# Aug 9 2023
# Server Code - Version 1
# This is the 1st official iteration of the server code

# THIS CODE IS MEANT TO BE RUN WITH server_vehicleside_v2.py and PedAppV1

import random
from paho.mqtt import client as mqtt_client
import json
import helper_functions as hf
import numpy as np
import time
from datetime import datetime

demo = False
coords_to_start_traj_pred = 6 # the traj function doesnt work with less than 5ish datapoints
ttc_threshold = 2.5 # how many seconds of future coords to generate
too_close = 50 # threshold for how close is too close with the cars and ped
sendingtopic = "vikram/columbia/summer2023/fromserver"
receivingtopic = "vikram/columbia/summer2023/toserver"
pedcolor = "#000000"

future_coords_fps = 2.5

ped_coords = {}
# format of ped_coords:
# {
#     '37': { <-- ped id #37
#         'x': [3, 4, 5, 6, ...], <-- x coords
#         'y': [6, 8, 10, 12, ...], <-- y coords
#         't': [423168421, 423168422, 423168423, 423168424, ...] <-- time in seconds (since epoch)
#     },
#     '94': { <-- ped id #37
#         ...
#     }
# }
coordsendinterval = 0
quant_info = {"initialized": time.time()}

xtest = 300
ytest = 300
# ped_id_cv = -1

mqtt_to_cv_ids = {}

def settracking(ped_id_mqtt, x, y, place):
    settracking_realworld(ped_id_mqtt, x, y, place)
    # settracking_sim(ped_id_mqtt, x, y, place)


def settracking_realworld(ped_id_mqtt, x, y, place):
    
    try:
        vehicle_data = hf.read_json_file_v2()
    except Exception as e:
        try:
            time.sleep(0.01)
            vehicle_data = hf.read_json_file_v2()
        except: # sometimes it just fails, so there's nothing you can do 
            return
    
    closex = float('inf')
    closey = float('inf')
    
    ped_id_cv = -1
    
    for veh_id in vehicle_data['o']:
        if (vehicle_data['o'][veh_id]['class'] == 'vehicle'): continue
        vehx = vehicle_data['o'][veh_id]['x'][0]
        vehy = vehicle_data['o'][veh_id]['y'][0]
        
        diffx = abs(vehx - x)
        diffy = abs(vehy - y)
        
        
        if (diffx < closex and diffy < closey):
            closex = diffx
            closey = diffy
            ped_id_cv = veh_id
    
    if (ped_id_cv == -1):
        print("No pedestrian found")
        return
    
    print(f"MQTT id {ped_id_mqtt} is COSMOS id {ped_id_cv}")
    mqtt_to_cv_ids[ped_id_mqtt] = ped_id_cv
    # return ped_id_cv
    
def settracking_sim(ped_id_mqtt, x, y, place):
    
    try:
        vehicle_data = hf.read_json_file_v2()
    except Exception as e:
        try:
            time.sleep(0.01)
            vehicle_data = hf.read_json_file_v2()
        except: # sometimes it just fails, so there's nothing you can do 
            return
    
    ped_id_cv = "-1"
    print(f"MQTT id {ped_id_mqtt} is Simulation id {ped_id_cv}")
    mqtt_to_cv_ids[ped_id_mqtt] = ped_id_cv
    # return ped_id_cv

def receive_ped_coords(client, userdata, msg):
    start1 = time.time()
    message = msg.payload.decode() # receive message
    msgtype, ped_id_mqtt, lat, long, latency, place = message.split(",") 
    
    ### FOR RECORDING INFO ###
    rn = int(time.time())
    if (ped_id_mqtt not in quant_info):
        quant_info[ped_id_mqtt] = {
            "last ping": rn,
            "ttcs": {},
            "latencies": {
                'ping loop': {},
                'camera to warning render': {},
                'server processing': {},
                'camera to warning send': {},
                'camera to fc send': {},
                'server to phone warning mqtt': {}
            }
        }
    # else:
        # # quant_info[ped_id_mqtt]['latencies']['ping loop'][hf.epoch_to_timestamp(rn)] = rn-quant_info[ped_id_mqtt]['last ping']
        # # # quant_info[ped_id_mqtt]['latencies']['server to phone warning mqtt'][hf.epoch_to_timestamp(rn)] = latency
        # with open('fieldtestdata_v3_%s.json' % hf.epoch_to_timestamp(
        #     quant_info["initialized"], 
        #     format="%b_%-d_%Y_%H_%M_%S"
        # ), 'w') as file:
        #     json.dump(quant_info, file, indent=4)
        # # rn = time.time()
        # # quant_info[ped_id_mqtt]['last ping'] = rn
        
    ## TODO: There is a problem with the JSON Serialization, it says it cannot serialize int64
    # Look into this
    
    if (msgtype == 'tracking'):
        settracking(ped_id_mqtt, int(lat), int(long), place)

    try:
        vehicle_data = hf.read_json_file_v2()
    except Exception as e:

        try:
            time.sleep(0.01)
            vehicle_data = hf.read_json_file_v2()
        except: # sometimes it just fails, so there's nothing you can do 

            return

    cameratime = vehicle_data['t']
    # trafficlight = 'RED'
    # trafficcolor = '#ff0000'
    # traffictimeleft = 3
        
    sendbacktopic = hf.sendtopic + "/" + ped_id_mqtt # The sendback topic is specific to the ped id
    
    if (ped_id_mqtt not in mqtt_to_cv_ids):
        print(f"Ped {ped_id_mqtt} hasn't been established yet")
        
        vehicle_numps = vehicle_data['o']
        
        obj_data = {
            'future': {
                'ped':
                    [],
                'veh': 
                    [],
            },
            'realtime': {
                'ped':
                    [],
                'veh': 
                    [],
            },
            'you': {
                'x': -1,
                'y': -1
            },
            # 'trafficlight': {
            #     'status': trafficlight,
            #     'color': trafficcolor,
            #     'timeleft': traffictimeleft
            # },
            'status': 'info',
            'strange': 0, # to send extra information, mainly for debugging
            # 'starttime': cameratime,
            'starttime': time.time(),
        }

        veh_points = []
        for vehnump in vehicle_numps:
            veh_random_color = hf.random_color(vehnump)
            veh_points.append([])
            obj_data['realtime']['veh'].append({
                "x": round(vehicle_numps[vehnump]['x'][0]), 
                "y": round(vehicle_numps[vehnump]['y'][0]),
                "color": veh_random_color
            })
            
            for i in range(1, len(vehicle_numps[vehnump]['x'])):
                veh_points[0].append({
                    "x": round(vehicle_numps[vehnump]['x'][i]), 
                    "y": round(vehicle_numps[vehnump]['y'][i]),
                    "color": veh_random_color
                })
        
        obj_data['future']['veh'] = veh_points

        hf.send(client=client, data=json.dumps(obj_data), topic_send=sendbacktopic)
        
        return
        
        
    ped_id_cv = mqtt_to_cv_ids[ped_id_mqtt]
    
    # print("official ped id:", ped_id_cv)
    
    ttc = float('inf')
    ttc_id = -1
    
    vehicle_numps = vehicle_data['o']

    
    if (ped_id_mqtt in mqtt_to_cv_ids):
        # print(f"Ped MQTT ID: {ped_id_mqtt} | time {times}...")
        if (ped_id_cv not in vehicle_data['o']):
            print(f"Couldn't find ped CV id {ped_id_cv}")
            
            vehicle_numps = vehicle_data['o']
        
            obj_data = {
                'future': {
                    'ped':
                        [],
                    'veh': 
                        [],
                },
                'realtime': {
                    'ped':
                        [],
                    'veh': 
                        [],
                },
                'you': {
                    'x': -2,
                    'y': -2
                },
                # 'trafficlight': {
                #     'status': trafficlight,
                #     'color': trafficcolor,
                #     'timeleft': traffictimeleft
                # },
                'status': 'info',
                'strange': 0, # to send extra information, mainly for debugging
                # 'starttime': cameratime,
                'starttime': time.time(),
            }
            
            veh_points = []
            for vehnump in vehicle_numps:
                veh_random_color = hf.random_color(vehnump)
                veh_points.append([])
                obj_data['realtime']['veh'].append({
                    "x": round(vehicle_numps[vehnump]['x'][0]), 
                    "y": round(vehicle_numps[vehnump]['y'][0]),
                    "color": veh_random_color
                })
                
                for i in range(1, len(vehicle_numps[vehnump]['x'])):
                    veh_points[0].append({
                        "x": round(vehicle_numps[vehnump]['x'][i]), 
                        "y": round(vehicle_numps[vehnump]['y'][i]),
                        "color": veh_random_color
                    })
            
            obj_data['future']['veh'] = veh_points

            hf.send(client=client, data=json.dumps(obj_data), topic_send=sendbacktopic)
            
            
            return
        ped_xnump = np.array(vehicle_data['o'][ped_id_cv]['x'])
        ped_ynump = np.array(vehicle_data['o'][ped_id_cv]['y'])
        for vehicle_id in vehicle_data['o']:
            if (ped_id_cv == vehicle_id): continue
            if (vehicle_data['o'][vehicle_id]['class'] == 'pedestrian'):
                continue
            veh_xnump = np.array(vehicle_data['o'][vehicle_id]['x'])
            veh_ynump = np.array(vehicle_data['o'][vehicle_id]['y'])
            
            
            ## Detecting collisions based on the future coords ##
            # How it works:
            # make a difference array based on the ped and veh coords
            #    ped_xnump = [14, 12, 10,  8,  7,  6]
            #    veh_xnump = [ 2,  6,  9, 13, 18, 24]
            #    dif_xnump = [12,  6,  1,  5, 11, 18]
            #   tooclose_x = [-1, -1,  1, -1, -1, -1]
            #   tooclose_y = [ 1, -1,  1, -1,  1, -1]
            # warningtimes = [ 0   0   1   0   0   0]
            #                          ^ identified as ttc
            # thus index 2 => 2 seconds in the future is the time to collision
            
            try:
                dif_xnump = np.absolute(ped_xnump-veh_xnump)
                dif_ynump = np.absolute(ped_ynump-veh_ynump)
            except Exception as e:
                print("Something went wrong with the difference array")
                input(e)
            tooclose_x = np.flatnonzero(dif_xnump <= too_close)
            tooclose_y = np.flatnonzero(dif_ynump <= too_close)
            
            warning_times = np.intersect1d(tooclose_x, tooclose_y)
            if (warning_times.size == 0):
                continue
            ttc_thiscar = np.min(warning_times)
            
            if (ttc_thiscar < ttc):
                ttc = ttc_thiscar / future_coords_fps
                ttc_id = vehicle_id
                

        if (ttc_id == -1 or ttc >= ttc_threshold):
            status = "good"
        else:
            status = "bad"
        if (ttc == float('inf')):
            ttc = -1
        stat_data = {
            'status': status,
            'ttc': ttc,
            'ttc_id': ttc_id,
            'strange': 0, # to send extra information, mainly for debugging,
            # 'starttime': cameratime,
            'starttime': time.time()
        }
        # if (float(x) > 600): stat_data['strange'] = 1
        # print(json.dumps(stat_data, indent=4))
        try:
            hf.send(client=client, data=json.dumps(stat_data),topic_send=sendbacktopic)
        except Exception as e:
            print(e)
            
        # rn = time.time()
        # quant_info[ped_id_mqtt]['latencies']['camera to warning send'][hf.epoch_to_timestamp(rn)] = rn - cameratime
        # if (ttc != -1):
        quant_info[ped_id_mqtt]['ttcs'][cameratime] = {
            'status': status,
            'ttc': ttc,
            'x': ped_xnump[0],
            'y': ped_ynump[0],
            'ttc_id': ttc_id,
            'ttc_threshold': ttc_threshold,
            'too_close': too_close,
        }
        obj_data = {
            'future': {
                'ped':
                    [],
                'veh': 
                    [],
            },
            'realtime': {
                'ped':
                    [],
                'veh': 
                    [],
            },
            'you': {
                'x': round(ped_xnump[0], 2),
                'y': round(ped_ynump[0], 2)
            },
            # 'trafficlight': {
            #     'status': trafficlight,
            #     'color': trafficcolor,
            #     'timeleft': traffictimeleft
            # },
            'status': 'info',
            'strange': 0, # to send extra information, mainly for debugging,
            # 'starttime': cameratime,
            'starttime': time.time(),
        }
        
        
        ped_random_color = pedcolor
        ped_points = [[]]
        obj_data['realtime']['ped'].append({
            "x": round(ped_xnump[0]), 
            "y": round(ped_ynump[0]),
            "color": ped_random_color
            # "color": "#000000"
            
        })
        
        # print(obj_data['realtime']['ped'])
        
        for i in range(1, len(ped_xnump)):
            ped_points[0].append({
                "x": round(ped_xnump[i]), 
                "y": round(ped_ynump[i]),
                # "color": "#000000"
                "color": ped_random_color
            })
        
        
        veh_points = []
        for vehnump in vehicle_numps:
            if (vehnump == ped_id_cv): 
                continue
            veh_random_color = hf.random_color(vehnump)
            veh_points.append([])
            obj_data['realtime']['veh'].append({
                "x": round(vehicle_numps[vehnump]['x'][0]), 
                "y": round(vehicle_numps[vehnump]['y'][0]),
                "color": veh_random_color
            })
            
            for i in range(1, len(vehicle_numps[vehnump]['x'])):
                veh_points[0].append({
                    "x": round(vehicle_numps[vehnump]['x'][i]), 
                    "y": round(vehicle_numps[vehnump]['y'][i]),
                    "color": veh_random_color
                })
        
        
        obj_data['future']['ped'] = ped_points
        obj_data['future']['veh'] = veh_points

        try:
            hf.send(client=client, data=json.dumps(obj_data), topic_send=sendbacktopic)
        except Exception as e:
            print(e)
            # TODO
            # There is a problem with the JSON Serialization, 
            # it said that it cannot serialize int64
        end1 = time.time()

        # quant_info[ped_id_mqtt]['latencies']['camera to fc send'][hf.epoch_to_timestamp(rn)] = end1 - cameratime
        # quant_info[ped_id_mqtt]['latencies']['server processing'][hf.epoch_to_timestamp(rn)] = end1-start1
        
        # with open('fieldtestdata.txt', 'a') as file:
        #     if (ttc != -1):
        #         file.write(
        #             f"{datetime.fromtimestamp(cameratime)} {ped_id_mqtt} {ttc} {round(end1-start1, 10)}\n"
        #         )
        
    else:
        print("\n\n\n\n\n")
        print("PROBLEM AREA")
        print(mqtt_to_cv_ids, ped_id_cv, ped_id_mqtt)
        print("\n\n\n\n\n")

## CLIENT RUNS THIS ALL THE TIME ##
def communicate(client: mqtt_client, onmessage):
    hf.setup_receiver(
        client, 
        receiver_topic=receivingtopic,
    )
    client.on_message = receive_ped_coords
    


def run():
    hf.setup(
        ftopicsend=sendingtopic,
        ftopicreceive=receivingtopic
    )
    client = hf.connect_mqtt()
    # client.loop_start()

    
    communicate(
        client=client, 
        onmessage= receive_ped_coords
    )
    client.loop_forever()
    # while True:
    #     print("asdf")
    #     for mqtt_id in mqtt_to_cv_ids:
    #         check_collisions(
    #             ped_id_cv=mqtt_to_cv_ids[mqtt_id],
    #             ped_id_mqtt=mqtt_id,
    #         )
    #     time.sleep(1/sendback_per_second)


if __name__ == "__main__":
    run()
    
    
    
# Store TTC
# Store Latency