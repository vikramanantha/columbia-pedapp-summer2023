# Vikram Anantha
# Columbia Summer Internship - Summer 2023
# Mentored under Sharon Di and Yongjie Fu

# July 13 2023
# Server Code - Version 1
# This is the 1st official iteration of the server code

# THIS CODE IS MEANT TO BE RUN WITH server_vehicleside_v1.py and PedAppV1


import random
from paho.mqtt import client as mqtt_client
import json
import helper_functions as hf
import numpy as np
import time

demo = True
coords_to_start_traj_pred = 6 # the traj function doesnt work with less than 5ish datapoints
future_pred = 3 # how many seconds of future coords to generate
too_close = 10 # threshold for how close is too close with the cars and ped
sendingtopic = "vikram/columbia/summer2023/fromserver"
receivingtopic = "vikram/columbia/summer2023/toserver"
pedcolor = "#000000"

coordsendinterval = 0
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


def receive_ped_coords(client, userdata, msg):
    start1 = time.time()
    message = msg.payload.decode() # receive message
    ped_id, lat, long, times, place = message.split(",") 
    
    x, y = hf.get_xy_from_latlong(lat, long, place)
    # format of message: "[pedestrian_id],[x_coord],[y_coord],[time_seconds]"
    times = float(times)
    # Time is in seconds, measuring the time since epoch (Jan 1 1970 at 12am). This ensures
    # That all times that are being used in calculations are realtime from the point of recording,
    # and thus any intersecting-line calculations are accurate
    print(ped_id, x, y)
    
    sendbacktopic = hf.sendtopic + "/" + ped_id # The sendback topic is specific to the ped id
    if (ped_id not in ped_coords): # if this is the first time this ped is sending a message
        ped_coords[ped_id] = {'x': [], 'y': [], 't': []}
    ped_coords[ped_id]['x'].append(float(x))
    ped_coords[ped_id]['y'].append(float(y))
    ped_coords[ped_id]['t'].append(times)
    if (len(ped_coords[ped_id]['x']) >= coords_to_start_traj_pred): # if the ped has sent a certain number of coords to register a traj

        coordsendinterval = round(ped_coords[ped_id]['t'][-1] - ped_coords[ped_id]['t'][-2], 1)
        # ped_timeoffset = ped_coords[ped_id]['t'][0]
        ped_timeoffset = ped_coords[ped_id]['t'][-1]
        # print(np.array(ped_coords[ped_id]['t'])-ped_timeoffset)
        # The reason there is a time offset is because all the time are in seconds from epoch
        # which means the numbers are really big
        # This skews the trajectories, so instead there is an offset to make the numbers smaller

        xpred = hf.get_traj(
            np.array(ped_coords[ped_id]['t'])-ped_timeoffset, 
            np.array(ped_coords[ped_id]['x'])
        )
        ypred = hf.get_traj(
            np.array(ped_coords[ped_id]['t'])-ped_timeoffset, 
            np.array(ped_coords[ped_id]['y'])
        )

        ped_xnump, ped_ynump = hf.get_parametric_numpy_data(
            xpred, ypred, 
            s_future=future_pred,
            offset=ped_timeoffset,
            current_time=times
        )
        
        # Example:
        # ped_coords[x]    = [        300,         320,         340,         360,         380]
        # ped_coords[time] = [13276481723, 13276481724, 13276481725, 13276481726, 13276481727]
        # offset           = 13276481727
        # ped_coords[t]    = [         -4,          -3,          -2,          -1,           0]
        
        # future_coords[t] = [  0, 0.5,   1, 1.5,   2, 2.5]
        # future_coords[x] = [380, 390, 400, 410, 420, 430]
        
        # I have written this code such that whenever the trajectory is created, it is such that
        # time 0 is the current time, any negative time is in the past, positive is in the future
        # that way, if there is a trajectory, x(t)
        # x(0)  is where the vehicle should be right now
        # x(-3) is where the vehicle was 3 seconds ago
        # x(3)  is where the vehicle will be 3 seconds from now
        
        # Keep in mind that as the vehicle moves, the trajectory will update, not just in direction, 
        # but in where the x(0) is said to be
        # Ex: x(0)  from 12:36:00 is 700, but x(0) at 12:36:29 is 850
        #     However you still technically can use x(t) at 12:36:00
        #     x(29) from 12:36:00 would be 850, because x(29) predicts 29 seconds into the future
        # In short, each trajectory every second is different
        # This works well to predict where a vehicle will be even if it isn't detected anymore

        try:
            vehicle_data = hf.read_json_file() # reads the trajectories saved
            # Note: These trajectories are what's processed and stored in also_server_v1.py
        except: # sometimes it just fails, so try again 
            try:
                time.sleep(0.01)
                vehicle_data = hf.read_json_file()
            except: # sometimes it just fails, so there's nothing you can do 
                return
        ttc = float('inf')
        ttc_id = -1
        vehicle_numps = {}
        # Vehicle numps is a dict to save all the calculated future coords
        # and is sent to the app
        # Format of vehicle_numps:
        # {
        #     '42': { <-- vehicle id
        #         'x': [13, 14, 15, 16, ...], <-- future x coord
        #         'y': [26, 28, 30, 32, ...], <-- future y coord
        #     },
        #     '87': {
        #         ...
        #     }
        # }
        for vehicle_id in vehicle_data['o']:
            # print(".", vehicle_id)
            veh_xcoef = vehicle_data['o'][vehicle_id]['x']
            veh_ycoef = vehicle_data['o'][vehicle_id]['y']
            veh_timeoffset = vehicle_data['o'][vehicle_id]['offset']
            if (len(veh_xcoef) == 1 and veh_xcoef[0] == 0): # if the traj alg didn't work, the coefs are saved as [0]
                continue
            veh_xnump, veh_ynump = hf.get_parametric_numpy_data(
                veh_xcoef, veh_ycoef, 
                s_future=future_pred,
                offset=veh_timeoffset,
                current_time=times,
                demo=demo
            )
            vehicle_numps[vehicle_id] = {"x": veh_xnump, "y": veh_ynump}
            
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
            ttc_thiscar = np.min(warning_times) * coordsendinterval
            
            if (ttc_thiscar < ttc):
                ttc = ttc_thiscar + times
                ttc_id = vehicle_id
                
        if (ttc_id == -1):
            status = "good"
        else:
            status = "bad"
        if (ttc == float('inf')):
            ttc = -1
        stat_data = {
            'status': status,
            'ttc': ttc,
            'ttc_id': ttc_id,
            'strange': 0, # to send extra information, mainly for debugging
        }
        # if (float(x) > 600): stat_data['strange'] = 1
        hf.send(client=client, data=json.dumps(stat_data),topic_send=sendbacktopic)

        
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
            'status': 'info',
            'strange': 0, # to send extra information, mainly for debugging
        }
        
        ped_points = [[]]
        ped_random_color = pedcolor
        obj_data['realtime']['ped'].append({
            "x": round(ped_xnump[0]), 
            "y": round(ped_ynump[0]),
            "color": ped_random_color
            
        })
        
        for i in range(1, len(ped_xnump)):
            ped_points[0].append({
                "x": round(ped_xnump[i]), 
                "y": round(ped_ynump[i]),
                "color": ped_random_color
            })
        
        
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
        
        
        obj_data['future']['ped'] = ped_points
        obj_data['future']['veh'] = veh_points

        hf.send(client=client, data=json.dumps(obj_data), topic_send=sendbacktopic)
        end1 = time.time()
        

## CLIENT RUNS THIS ALL THE TIME ##
def communicate(client: mqtt_client):
    hf.setup_receiver(client)
    client.on_message = receive_ped_coords
    


def run():
    hf.setup(
        ftopicsend=sendingtopic,
        ftopicreceive=receivingtopic
    )
    client = hf.connect_mqtt()
    # client.loop_start()
    communicate(client)
    client.loop_forever()


if __name__ == "__main__":
    run()
    