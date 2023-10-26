# Vikram Anantha
# Columbia Summer 2023 Internship
# Mentored under Sharon Di and Yongjie Fu

# HELPER FUNCTIONS
# These are functions that are used in multiple codes
# so I figured it would be best to put them all in one file
# that can be imported in each file

import random
from paho.mqtt import client as mqtt_client
import json
import time
from datetime import datetime
import os
import numpy as np
import scipy.optimize as optimize
from sklearn.linear_model import LinearRegression
avg = lambda arr: sum(arr)/len(arr)


broker, port, sendtopic, receivetopic, client_id = None, None, None, None, None
xy_latlong_model = None
places = {
    "W 120 at Amsterdam": {
        "coordpairs": [
            [[40.80930959999999885213, -73.95931310000000280525], [328,584]],
            [[40.80943609999999921456, -73.95911300000000210275], [486,215]],
            [[40.80932539999999875135, -73.95908500000000174168], [655,382]],
            [[40.80920580000000086329, -73.95928050000000553155], [489,739]],
            [[40.80931540000000268265, -73.95937419999999917763], [236,621]],
            [[40.80936309999999878073, -73.95935869999999567881], [218,520]],
            [[40.80935310000000271202, -73.95940450000000510045], [143,575]],
            [[40.80941140000000189048, -73.95934320000000639084], [180,429]],
            [[40.80943090000000239570, -73.95911789999999541578], [483,236]],
            [[40.80928719999999998436, -73.95909389999999916654], [685,455]],
            [[40.80933780000000155042, -73.95899640000000374584], [775,293]],
            [[40.80946360000000083801, -73.95927369999999712036], [212,284]],
            [[40.80931139999999857082, -73.95903239999999811971], [747,367]]
        ]
    },
    # "Columbia University Lawn": {
    #     "coordpairs": [
    #         [[40.807622, -73.961617], [900,353]],
    #         [[40.807015, -73.962079], [892,760]],
    #         [[40.807322, -73.963122], [410,824]],
    #         [[40.806750, -73.962983], [625,1077]]
    #     ]
    # }
}



#### IMPORTANT FUNCTIONS ####


## Version 1 for getting the trajectory ##
# Uses Numpy Polynomial fitting
# inputs: list of x coords, list of y coords
# output: coefs for equation
def get_traj_v1(x, y):
    # print(x, y)
    # any preprocessing of x and y pts (rn nothing)
    p = np.polyfit(x, y, deg=2)
    # p = np.polynomial.Polynomial.fit(x, y, deg=2).coef
    # technically you're not supposed to use polyfit but the replacement isn't as accurate
    
    # print(p)
    return list(p)[::-1]
    # return list(p)
    

## Version 2 for getting the trajectory ##
# Uses Scipy Curve fitting
# inputs: list of x coords, list of y coords
# output: coefs for equation
def get_traj_v2(x, y):

    def equ_format_4(x0, a, b, c, d, e): # customize what the equation would look like here
        return a * (x0 ** 0) + b * (x0 ** 1) + c * (x0 ** 2) + d * (x0**3) + e * (x0**4)

    def equ_format_2(x0, a, b, c): # customize what the equation would look like here
        return a * (x0 ** 0) + b * (x0 ** 1) + c * (x0 ** 2)
    
    # Fit a polynomial to the data
    popt, pcov = optimize.curve_fit(equ_format_2, x, y)

    return list(popt)


# a + bx + cx^2
# function returns a, b, and c

def get_traj(x, y):
    return get_traj_v2(x, y)


## Easy function to get an equation from the coefs ##
def get_equation_from_coefs(coefs_list, inde='y', depe='x', expo='^'):
    toprint = ""
    # toprint += "%s = "
    for almost_degree, coef in enumerate(coefs_list):
        toprint += "(%s * (%s%s%s)) + " % (coef, depe, expo, almost_degree)
    return toprint[:-3]

## Same as above but prints it ##
def print_equation_from_coefs(coefs_list, inde='y', depe='x', expo='^'):
    print(get_equation_from_coefs(coefs_list, inde=inde, depe=depe, expo=expo))



## Set up vars for the MQTT client ##
def setup(
        fbroker='broker.hivemq.com', 
        fport=1883, ftopicsend="ngi/1/detection/fromserver", 
        ftopicreceive="ngi/1/detection/toserver", 
        fclient_id=f'python-mqtt-{random.randint(0, 100)}'
    ):
    global broker, port, sendtopic, receivetopic, client_id
    broker = fbroker
    port = fport
    sendtopic = ftopicsend
    receivetopic = ftopicreceive
    client_id = fclient_id
    print(client_id, receivetopic)
    return broker, port, sendtopic, receivetopic, client_id
    
    
    
## Connects to the MQTT server ##
def connect_mqtt():
    def on_connect(client, userdata, flags, rc):
        if rc == 0:
            print("Connected to MQTT Broker!")
        else:
            print("Failed to connect, return code %d\n" % rc)

    def on_disconnect(client, userdata, rc):
        print("disconnedted!")


    client = mqtt_client.Client(client_id)
    client.on_disconnect = on_disconnect
    client.on_connect = on_connect
    client.connect(broker, port)
    return client


## Function to send a message to the recipient via MQTT ##
def send(client, data, verbose=False, topic_send = sendtopic):
    # msg = json.dumps(data)
    msg = data
    result = client.publish(topic_send, msg)
    # result: [0, 1]
    status = result[0]
    if status == 0:
        if verbose: print(f"{msg} was sent")
    else:
        print(f"Failed to send {msg} to {topic_send}")
    # if (verbose): print("Message Sent!")
    
    
## Function to simply receive MQTT messages and print them ##
# This function isn't used in any final code, but it is nice to have
# to understand how basic receiving works
def simple_receive(client, userdata, msg):

    message = msg.payload.decode()
    print("Message received:")
    print(message)
    
    return message

def simple_receive_v2(client, userdata, msg):

    message = msg.payload.decode()
    print("Message received:")
    print(message)
    msg = json.loads(message)
    curtime = datetime.fromtimestamp(msg['start_time'])
    curtimestr = str(curtime).replace('.', '_').replace(':', '_')
    with open('frames/sampleframes_yongjie_aug182023/frame_%s.json' % curtimestr, 'w') as file:
        json.dump(msg, file, indent=4)
    
    return message


## Function to simply send an inputted MQTT message ##
# This function isn't used in any final code, but it is nice to have
# to understand how basic sending works
def simple_send(client):
    while True:
        data = input("Whats the message you want to send: ")    

        send(client, data, verbose=True)


## Sets up receiver ##
# It's only one line but its an easier line to write the function name
def setup_receiver(client, receiver_topic = None):
    if (receiver_topic == None):
        receiver_topic = receivetopic
    client.subscribe(receiver_topic)
    
    
    
## PROCESSING EACH TXT FILE INTO A FRAME ##
# This version of the function is NOT in use
# This assumes the input is a json file, in the format:
# Input file format:
# {
#     "t": "12345147973", 
#     "i": 480, 
#     "1": "[vehicles,-90.16,NE,0.64,1298,1221,366,292]", 
#     "21": "[people,-99.91,N,0.67,1012,988,411,373]"
# }
def get_frame_from_file(path):
    if not os.path.exists(path): # This shouldn't happen in the server code
        time.sleep(0.5)
        print("%s does not exist! Exiting the program..." % path)
        quit()

    # print(f"reading message number {indx}...")
    data = dict()
    # format of data:
    # {
    #     "t": '12345147973', <-- seconds since epoch
    #     "i": 0, <-- frame id
    #     "o": [
    #         {'type': 'vehicle', 'id': 0, 'x': 1500, 'y': 2414},
    #         {'type': 'vehicle', 'id': 1, 'x': 1544.1145, 'y': 2432.43414}
    #         ...
    #     ]
    # }
    # t = time, i = index, o = objects
    current_time = int(time.time() * 1000)
    # print(indx)
    data["t"] = current_time # This will be overwritten
    data['o'] = []
    
    with open(path, "r") as file:
        ob_data = json.load(file)
        for i in ob_data:
            if (i == 'i' or i == 't' or i == 'timestamp'): data[i] = ob_data[i]
            else:
                veh_str = ob_data[i][1:-1]
                # assumed that veh_str looks like:
                # 'vehicles,-75.82,NE,0.39,804,758,912,817'
                veh = veh_str.split(",")
                try:
                    type, heading_degree, direction, speed, xbr, xtl, ybr, ytl = veh
                except Exception as e:
                    print(veh_str)
                id = int(i)
                x = (float(xbr) + float(xtl))/2 # avg the bounding box coords
                y = (float(ybr) + float(ytl))/2
                data['o'].append({'type': type, 'id': id, 'x': x, 'y': y})

    return data


def get_frame_from_file_v2(message):
    data = dict()
    # format of data:
    # {
    #     "t": '12345147973', <-- seconds since epoch
    #     "i": 0, <-- frame id
    #     "o": [
    #         {'type': 'vehicle', 'id': 0, 'x': 1500, 'y': 2414},
    #         {'type': 'vehicle', 'id': 1, 'x': 1544.1145, 'y': 2432.43414}
    #         ...
    #     ]
    # }
    # t = time, i = index, o = objects
    
    onlyrecognizing = ["vehicle"]
    data["t"] = message['time']
    data['o'] = []
    
    for ob in range(len(message['boxes'])):
        tlx, tly, brx, bry = message['boxes'][ob]
        
        
        
        # assumes labels comes in this format:
        # "id:30 vehicle 0.91",
        idstr, obtype, confidence = message['labels'][ob].split(" ")
        
        
        if (obtype not in onlyrecognizing): continue
        
        x = (tlx+brx)/2
        y = (tly+bry)/2
        id = int(idstr[3:])
        
        
        
        data['o'].append({
            'type': obtype, 
            'id': id, 
            'x': x, 
            'y': y
        })   
        
    return data     
        
        
def get_frame_from_file_v3(message):
    data = dict()
    # format of data:
    # {
    #     "t": '12345147973', <-- seconds since epoch
    #     "i": 0, <-- frame id
    #     "o": [
    #         {'type': 'vehicle', 'id': 0, 'x': 1500, 'y': 2414},
    #         {'type': 'vehicle', 'id': 1, 'x': 1544.1145, 'y': 2432.43414}
    #         ...
    #     ]
    # }
    # t = time, i = index, o = objects
    
    onlyrecognizing = ["vehicle"]
    data["t"] = message['start_time']
    data['o'] = {}

    # ids = []
    # for ob in message['labels']:
    for i in range(len(message['labels'])):
        ob = message['labels'][i]
        idstr, obtype, confidence = ob.split(" ")
        id = int(idstr[3:])
        
        box = message['boxes'][i]
        x1, y1, x2, y2 = box
        xcoord = (x1+x2)/2
        ycoord = (y1+y2)/2
        
        data['o'][id] = {
            'x': [xcoord],
            'y': [ycoord],
            'class': obtype
        }
        
    # ids.sort()
    
    # for ind, id in enumerate(ids):
    for i in range(len(message['traj_id'])):
        id = message['traj_id'][i]
        fcs = message['traj_tjs'][i]
        
        for fc in fcs:
            xfc, yfc = fc
            if (id not in data['o']):
                data['o'][id] = {
                    'x': [xfc],
                    'y': [yfc],
                    'class': '?'
                }
                print("?", end='')
            try:
                data['o'][id]['x'].append(xfc)
                data['o'][id]['y'].append(yfc)
            except:
                # print(message['labels'])
                # print(message['traj_id'])
                # print(id)
                print("SOMETHINGS BAD")
    print()
        
        
    return data    

## Get the coordinates from the frames processed
def get_coords_from_frames(these_frames, end_max=float('inf'), kickout=20):
    coords = {}
    # format for coords:
    # {
    #     0: {
    #         "x": [1, 2, 3, ...], <-- all the x coords for vehicle id 0
    #         "y": [2, 4, 6, ...], <-- all the y coords for vehicle id 0 
    #     },
    #     1: {
    #         "x": [...],
    #         "y": [...]
    #     },
    #     ...
    # }
    
    last_seen = {}
    
    # for frame in these_frames:
    for frame_id in range(max(0, len(these_frames)-end_max), len(these_frames)):
        frame = these_frames[frame_id]
        for ob in frame['o']:
            if (int(ob['id']) not in coords): 
                coords[int(ob['id'])] = {'x': [], 'y': [], 't': []}
            last_seen[int(ob['id'])] = frame_id
            coords[int(ob['id'])]['x'].append((ob['x']))
            coords[int(ob['id'])]['y'].append((ob['y']))
            coords[int(ob['id'])]['t'].append((frame['t']))
    
    for id in last_seen:
        if (len(these_frames) - last_seen[id] > kickout):
            del coords[id]
    return coords

def generate_traj_from_coords(coords):
    data = {'t': '', 'o': {}}
    # format for data:
    # {
    #     't': '11:43:02 2023-06-28',
    #     'o': {
    #           0 : [3.3e-15, 1.3e-16, 4.6e-16, 2, 5.5e-16], <-- coefs for the polynomial that vehicle id 0 most likely is following
    #           1 : [...]
    #      }
    # }
    for id in coords:
        # print(id)
        try:
            coefs = get_traj(coords[id]['x'], coords[id]['y'])
        except Exception as e:
            print("Exception occured")
            print(e)
            print("Making coefs [0] instead")
            coefs = [0]
        # print(coefs)
        data['o'][id] = coefs
    
    # print(data['o'])
    
    return data


## Generate Parametric Trajectories from the Veh coordinates dict
def generate_parametric_traj_from_coords(coords):
    data = {'t': '', 'o': {}}
    # format for data:
    # {
    #     't': '11:43:02 2023-06-28',
    #     'o': {
    #           0 : [3.3e-15, 1.3e-16, 4.6e-16, 2, 5.5e-16], <-- coefs for the polynomial that vehicle id 0 most likely is following
    #           1 : [...]
    #      }
    # }
    for id in coords:
        # print("###", id, "###")
        try:
            # print(id, np.array(coords[id]['t'])-coords[id]['t'][-1])
            xcoefs = get_traj(np.array(coords[id]['t'])-coords[id]['t'][-1], np.array(coords[id]['x']))
            ycoefs = get_traj(np.array(coords[id]['t'])-coords[id]['t'][-1], np.array(coords[id]['y']))
        except Exception as e: # usually happens if there's less than 5 datapoints
            # print("Exception occured at id %s" % id)
            # print(e)
            # print("Making coefs [0] instead")
            ycoefs = [0]
            xcoefs = [0]
            
            # print(np.array(coords[id]['t']), coords[id]['t'][0], np.array(coords[id]['x']))
            # input()
        # print(xcoefs, ycoefs)
        # print(ycoefs)
        data['o'][id] = {'x': xcoefs, 'y': ycoefs, 'offset': coords[id]['t'][0]}
    
    # print(data['o'])
    
    return data


## Gets future coords based on a trajectory ##
def get_parametric_numpy_data(xcoefs, ycoefs, s_future, offset, current_time, demo=False, persecond=10):
    xeq = get_equation_from_coefs(xcoefs, depe='t', expo='**')
    yeq = get_equation_from_coefs(ycoefs, depe='t', expo='**')
    # Example: xeq = "3*t**2 + 5*t**1 + -1*t**0" (the same as 3t^2 + 5t - 1)
    
    if demo: # for use with demo data
        offset = int(time.time())
    
    # print(">>", current_time, offset, current_time-offset)
        
    t = np.array(
            range(
                int(int(current_time-offset)*persecond), 
                int((int(current_time-offset)+s_future)*persecond)
            )
        )/persecond
    # Example: t = [0, 1, 2, 3, 4, 5]
    
    x_nump = eval(xeq)
    y_nump = eval(yeq)
    # eval() will run the xeq equation with respect to t, using the numpy array t for the calculations
    # should produce a numpy array
    # Example: x_nump = [-1, 7, 21, 41, 67, 99]
    # print("..", t, x_nump)
    return x_nump, y_nump


## Reads a json from a file ##
def read_json_file(pathname="trajectories/realtime_traj.json"):
    file = open(pathname, 'r')
    data = json.load(file)
    file.close()
    return data


## Reads a json from a file ##
def read_json_file_v2(pathname="trajectories/realtime_futurecoords.json"):
    file = open(pathname, 'r')
    data = json.load(file)
    file.close()
    return data


## Generates a random hexadecimal color
def random_color(id=time.time()):
    # Generate random RGB values in the range [0, 255]
    random.seed(id) # so that the colors dont keep changing every second 
    #                 (in server_v1.py the id isn't time but the vehicle id)
    r = random.randint(0, 255)
    g = random.randint(0, 255)
    b = random.randint(0, 255)
    
    # Convert RGB to hexadecimal format (#RRGGBB)
    hex_color = "#{:02x}{:02x}{:02x}".format(r, g, b)

    return hex_color




def get_time_in_seconds(time_string, date_string):
    # Parse the time string into hours, minutes, seconds, and milliseconds
    hours, minutes, seconds = map(int, map(float, time_string.split(':')))
    milliseconds = int(time_string.split('.')[-1]) if '.' in time_string else 0

    # Parse the date string into year, month, and day
    year, month, day = map(int, date_string.split('/'))
    # print(milliseconds)
    # Create a datetime object with the given year, month, day, hours, minutes, seconds, and microseconds
    dt = datetime(year, month, day, hours, minutes, seconds, milliseconds)

    # Calculate the number of seconds since the epoch (January 1, 1970)
    seconds_since_epoch = (dt - datetime(1970, 1, 1)).total_seconds()

    return seconds_since_epoch

def get_xy_from_latlong(lat, long, placename="W 120 at Amsterdam"):
    return get_xy_from_latlong_v2(lat, long, placename)


def get_xy_from_latlong_v1(lat, long, placename):
    start = time.time()
    places = {
        "W 120 at Amsterdam": {
            'origin': {
                # 'lat': 40 + (48/60) + (34/3600),
                # 'long': -73 - (57/60) - (33/3600),
                'lat': 40.809593,
                'long': -73.959274
            },
            'top': {
                'lat': 40.809551, 'long': -73.959071, 'y': 0
            },
            'bottom': {
                'lat': 40.809115, 'long': -73.959400, 'y': 1000
            },
            'left': {
                'lat': 40.809375, 'long': -73.959499, 'x': 400
            },
            'right': {
                'lat': 40.809047, 'long': -73.958756, 'x': 1700
            }
        },

    }
    place = places[placename]
    
    dy = place['bottom']['y'] - place['top']['y']
    dylat = place['bottom']['lat'] - place['top']['lat']
    dylong = place['bottom']['long'] - place['top']['long']
    
    dx = place['right']['x'] - place['left']['x']
    dxlat = place['right']['lat'] - place['left']['lat']
    dxlong = place['right']['long'] - place['left']['long']
    
    # [ogx - x][a b] + [oglat ] = [lat ]
    # [ogy - y][c d]   [oglong]   [long]
    
    # [ogx - x][a b] = [lat - oglat  ]
    # [ogy - y][c d]   [long - oglong]
    
    # [lat - oglat   = LAT ][a b]^-1 = [ogx - x = X]
    # [long - oglong = LONG][c d]      [ogy - y = Y]
    
    # [LAT ] ( 1 / )[d -b] = [X]
    # [LONG] (ad-bc)[-c a]   [Y]
    
    # (1/ad-bc)(LAT)
    
    LAT = lat - place['origin']['lat']
    LONG = long - place['origin']['long']
    
    print(LAT, LONG)
    
    a = dxlat / dx
    b = dylat / dy
    c = dxlong / dx
    d = dylong / dy
    
    print(a, b, c, d, sep="__")
    
    desc = 1/((a*d) - (b*c))
    aprime = d * desc
    bprime = b * (-1) * desc
    cprime = c * (-1) * desc
    dprime = a * desc
    
    X = (LAT * aprime) + (LONG * bprime)
    Y = (LAT * cprime) + (LONG * dprime)
    
    # X = (1/((a*d) - (b*c))) * ((LAT * d) + (LONG * b * -1))
    # Y = (1/((a*d) - (b*c))) * ((LAT * c * -1) + (LONG * a))
    
    x = X + place['left']['x']
    y = Y + place['top']['y']
    end=time.time()
    print("Time:", round(end-start, 3))
    # return x, y
    return x, y
    
    
    # 0,0 = 40.809444444444445,-73.95916666666668
    
    # dlat  -0.000437 = dy 1000
    # dlat  -0.000000437 = dy 1
    # dlong -0.000325 = dy 1000
    # dlong -0.000000325 = dy 1
    
    # y = 500, 
    #           lat  =  40.809552-0.0002185 = 40.8097705, -73.9589125
    #           long = -73.959075-0.0001625 = -73.9589125
    
    # x = 400+200,
    #           lat  = -0.0000002523076923101651 * 200 + 40.809375
    #           long =  0.000000571538461538414  * 200 + -73.959499
    
    # lat = 600 * -0.0000002523076923101651 + 700 * -0.000000437 + 40.809444444444445
    # long = 600 * 0.000000571538461538414 + 700 * -0.000000325 + -73.95916666666668
    
    
    
    # lat = y*0.0002185 + x*0.000dbhf
    

def get_xy_from_latlong_v2(lat, long, placename):
    global xy_latlong_model
    if (xy_latlong_model is None):
        xy_latlong_model = LinearRegression()
        xy_latlong_model.fit(
            places[placename]['latlong'],
            places[placename]['xy']
        )
        
    x,y = xy_latlong_model.predict([[lat, long]])[0]
    return x,y
    
def organizepoints(places):
    
    for placename in places:
        ll = []
        xy = []
        for pair in places[placename]['coordpairs']:
            ll.append(pair[0])
            xy.append(pair[1])
        
        places[placename]['latlong'] = ll
        places[placename]['xy'] = xy
    
    
def epoch_to_timestamp(
    epoch, 
    format = "%b %-d %Y, %H:%M:%S.%f"
):
    return datetime.fromtimestamp(epoch).strftime(format)
    
# organizepoints(places) 