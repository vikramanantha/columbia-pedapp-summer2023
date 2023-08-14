# Pedestrian Collision Warning App
Vikram Anantha \
Summer 2023 \
Columbia University Internship \
Under Prof Sharon Di and Yongjie Fu

# Framework Version 1

## Server - Vehicle Side Code

`server_vehicleside_v1.py` \
Created July 15 2023

### PURPOSE ###
This file processes given json files which store data about where each vehicle
is, calculates trajectories for each vehicle, and saves it in an external file 
so that the other server code can read it and utilise it

The reason the server has 2 codes is because for the main server code, 
all the code runs only when there is a message to be received, so if the 
vehicle trajectories were to also only be calculated when the ped coords are received, 
that would increase latency

### OVERVIEW ###
Here is an overview of the code:
~~~
Run():
  Collect Vehicle Positions():
      Get all file names based on the format
      For each file name that hasn't already been processed:
          Get the Frame from the File and add it to the list
  Calculate Vehicle Trajectories():
      Get the coordinates from each frame
      Calculate a trajetory from that for each vehicle
  Store the Vehicle Traj():
      Store it in a json file
~~~


## Server - Pedestrian Side Code
`server_pedside_v1.py` \ 
Created July 13 2023

### PURPOSE ###
This file receives MQTT messages from the app containing pedestrian coordinates, 
processes trajectories, and sends back TTC of the pedestrian and the vehicle

### OVERVIEW ###

Here is a summary of each of the functions

~~~
Receive Coords():
  Read Pedestrian Coords
  Store the coords in an array
  Create a trajectory based on all the coords received
  Create future coords for the pedestrian based on the traj
  Read in the Vehicle Trajectories
  For each vehicle traj:
      Create future coords for the vehicle based on the traj
      Find intersection points between vehicle and pedestrian
      Store that
  If there are intersection points:
      Send the earliest TTC
  Otherwise
      Send that everything is fine
  Send the future coords of the vehicles and the pedestrian to the app

  Note: Everything is based in seconds
~~~

### LATENCIES ###
Just to know how fast everything is running \
All running on a 2022 M2 MacBook Air

Received Message --> Send Message [essentially `receive_ped_coords()`]: 0.0062s

~~~
Receive Coords():
  Read Pedestrian Coords
  Store the coords in an array
  Create a trajectory based on all the coords received
  Create future coords for the pedestrian based on the traj
  Read in the Vehicle Future Coordinates
  For each vehicle future coordinate:
      Find intersection points between vehicle and pedestrian
      Store that
  If there are intersection points:
      Send the earliest TTC
  Otherwise
      Send that everything is fine
  Send the future coords of the vehicles and the pedestrian to the app

  Note: Everything is based in seconds
~~~

# Framework Version 2

## Server - Pedestrian Side Code
`server_pedside_v2.py` \
Created Aug 9 2023

### PURPOSE ###

Since the COSMOS server already calculates the vehicle future coordinates, there is no need to redo that. Instead, read them in from the file (created by `server_vehicleside.py`), and compare them to the pedestrian future coordinates.

### OVERVIEW ###



## Server - Vehicle Side Code
`server_vehicleside_v2.py` \
Created Aug 9 2023

### PURPOSE ###

After learning what the official COSMOS vehicle information has, I learned that the vehicle future trajectories are already stored, meaning I can use that instead. 

This code takes those future coordinates and stores them into a file, for the other server code to read.

This extra code is used to reduce latency: if the pedestrian side server code had to receive MQTT messages from both the pedestrian app and the COSMOS system, this might increase latency for sending the warning back to the pedestrian. This way, the pedestrian side server code only has to read information in from a file when needed.


### OVERVIEW ###

Here is the overview of the code:

~~~
Run():
    Create MQTT Client(
        on_message = Process Future Coords():
                        Read in message
                        Store message in file
    )
~~~

## Server - Acting Cosmos Code
`server_actingcosmos_v2.py` \
Created Aug 10 2023

### PURPOSE ###

Because I don't have access to the official COSMOS MQTT messages, I saved some of the files, and created my own MQTT server to test the other server codes.


This code is meant to act as the official COSMOS server sending out data about the vehicles via MQTT.

**This code is NOT part of the main framework** but is only for testing purposes

