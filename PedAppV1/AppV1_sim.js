// Vikram Anantha
// Columbia Summer Internship 2023
// Mentored under Prof Sharon Di, Yongjie Fu

// This is Version 1 of the Pedestrian App

// Latencies (Tested where server.py was on Wifi Network, App.js same network, phone on cellular):
// Coords Sent -> Processed Warning Message: 0.34 seconds
// Coords Sent -> Process Diagram Info: 0.52 seconds

import Paho from "paho-mqtt";

import { useState, useEffect } from "react";
import * as React from "react";
import { StyleSheet, Text, View, Vibration, Platform, Dimensions, ImageBackground } from 'react-native';
import { Svg, Circle, Line } from 'react-native-svg';
import { Audio } from 'expo-av';
import * as Location from 'expo-location';

////// VARS TO CHANGE //////

const coords_interval_ms = 1000
const receivetopic = "vikram/columbia/summer2023/fromserver/" + ped_id
const sendtopic = "vikram/columbia/summer2023/toserver"
const yongjiesendtopic = "_______"

// var testingTime = 0;

var client;
var ped_id = parseInt(Math.random() * 100);
var futureData = []
var realtimeData = []
var templocation = {
  timestamp: null,
  coords: {
    latitude: null,
    longitude: null,
    speed: null
  }
};
var lasttimestamp = 0
var placename = ""


const vibration_pattern = {
  'android': [
    0, 500, 250, 250, 250 // wait 0s, vibrate .5s, wait .25s, vibrate .25s, wait .25s
  ],
  'ios': [
    0, 250 // wait 0s, vibrate, wait .25s
  ]
}
const alive_chart = {
  0: {
    text: "So far so good",
    color: "#47c906"
  },
  1: {
    text: "DANGER DANGER COLLISION INCOMING",
    color: "#c90606"
  },
  2: {
    text: "Connecting to Server",
    color: "#ffd012"
  },
  3: {
    text: "No Server Connection",
    color: "#033dfc"
  },
}

const ScatterPlot = props => {
  
  var gridSizeW = 100;
  var gridSizeH = 100;

  const leftbound = 0
  const upbound = 0
  const rightbound = 832
  const downbound = 832
  var bgimagepath = './assets/intersection_v4.jpg';
  placename = "W 120 at Amsterdam"

  // const leftbound = 0
  // const upbound = 0
  // const rightbound = 1284
  // const downbound = 1386
  // var bgimagepath = './assets/columbia_lawn_v1.png';
  // var placename = "Columbia University Lawn"


  const scale = (rightbound-leftbound) / props.width
  gridSizeH = gridSizeH / scale;
  gridSizeW = gridSizeW / scale;
  const height = parseInt((downbound - upbound) / scale)
  const width = props.width
  // console.log(width, height, scale)
  const intervalsW = parseInt(width / gridSizeW);
  const intervalsH = parseInt(height / gridSizeH);


  return (
    <ImageBackground 
    source={require(bgimagepath)} 
    resizeMode="cover" 
    style={{flex: 1,
      justifyContent: 'center',
      // width:parseInt(width),
      height:height
      }}
    imageStyle={{opacity:0.4}}>
      <Svg style={styles.graph}>


        {Array.from(Array(intervalsW+1)).map((_, index) => (
          <Line
            key={`vertical-${index}`}
            x1={index * gridSizeW}
            y1={0}
            x2={index * gridSizeW}
            y2={height} // Adjust this based on your desired graph height
            stroke="gray"
            strokeWidth="0.25"
          />
        ))}


        {Array.from(Array(intervalsH+1)).map((_, index) => (
          <Line
            key={`horizontal-${index}`}
            x1={0}
            y1={index * gridSizeH}
            x2={width} // Adjust this based on your desired graph width
            y2={index * gridSizeH}
            stroke="gray"
            strokeWidth="0.25"
          />
        ))}


        {props.futuredata.map((vehicle, dataindex) => (
          vehicle.map((point, index) => (
            <Circle
            key={index}
            cx={(point.x - leftbound) / scale}
            cy={(point.y - upbound) / scale}
            r={1}
            fill={point.color}
          />
          ))
          
        ))}

        {props.realtimedata.map((point, dataindex) => (
          <Circle
          key={dataindex}
          cx={(point.x - leftbound) / scale}
          cy={(point.y - upbound) / scale}
          r={3}
          fill={point.color}
        />
        
        ))}
      </Svg>
    </ImageBackground>
  );
}

var isPlaying = false;

const App = () => {

  const [good, setalive] = useState(2);
  const [coordsx, updateCoordsX] = useState(400)
  const [coordsy, updateCoordsY] = useState(0)

  const [graphWidth, changeGraphWidth] = useState(Dimensions.get("window").height)
  const [graphHeight, changeGraphHeight] = useState(Dimensions.get("window").height)

  const [sound, setSound] = React.useState();
  // var sound = React.useRef(new Audio.Sound());
  // const [isPlaying, setIsPlaying] = useState(false);

  const [location, setLocation] = useState({
    timestamp: null,
    coords: {
      latitude: null,
      longitude: null,
      speed: null
    }
  });
  const [errorMsg, setErrorMsg] = useState(null);

  async function playSound() {
    if (isPlaying == false) {
      console.log('Loading Sound');
      const {sound} = await Audio.Sound.createAsync( require('./assets/alarm.mp3') );
      setSound(sound);
      // sound = _sound

      console.log('Playing Sound');
      await sound.playAsync();
      // setIsPlaying(true);
      isPlaying = true
    }
  }
  async function stopSound() {
    // console.log(sound)
    // console.log(isPlaying)
    // if (isPlaying) {
    //   await sound.unloadAsync()
    // }
    // isPlaying = false
  }



  function receive(msg) { 
    if (msg.destinationName === receivetopic) {
    lasttimestamp = Date.now()/1000
    // console.log(msg)
    var message = "";
    try {
      // Parse the JSON string into a JavaScript object
      message = JSON.parse(msg.payloadString);
    } catch (error) {
      console.log(msg.payloadString)
      console.error('Error parsing JSON:', error);
    }
    // console.log(message)
    

    if (message['status'] === "bad") {
      Vibration.vibrate(vibration_pattern[Platform.OS])      
      // console.log("BAD")
      setalive(1)
      playSound()
    }
    else if (message['status'] === "good") {
      Vibration.cancel()
      // console.log("GOOD")
      setalive(0)
      stopSound()
    }
    else if (message['status'] === 'info') {
      futureData = []
      realtimeData = []
      message['future']['ped'].forEach((_, ind) => {
        futureData.push(message['future']['ped'][ind])
      })
      message['future']['veh'].forEach((_, ind) => {
        futureData.push(message['future']['veh'][ind])
      })
      message['realtime']['ped'].forEach((_, ind) => {
        realtimeData.push(message['realtime']['ped'][ind])
      })
      message['realtime']['veh'].forEach((_, ind) => {
        realtimeData.push(message['realtime']['veh'][ind])
      })
    }
    // if (message['strange'] == 1) {
    //   console.log(Date.now()/1000 - testingTime)
    // }

    // var curtime = Date.now()/1000

    // // if (temp_coords_x > 600) {
    // //   testingTime = Date.now()/1000
    // // }

    
    // try {
    // // console.log("ti " + templocation.timestamp);
    // // console.log("la " + templocation.coords.latitude);
    // // console.log("lo " + templocation.coords.longitude);
    // // console.log("sp " + templocation.coords.speed);
    // send_coords_latlong(
    //     client, 
    //     templocation.coords.latitude, 
    //     templocation.coords.longitude, 
    //     curtime,
    //     placename
    // )
    // } catch {
    // console.log("Location hasn't been allowed yet")
    // }
  }}

  useEffect(() => {
    client = new Paho.Client(
      "broker.hivemq.com",
      Number(8000),
      `python-mqtt-${ped_id}`
    );
    client.connect( 
      {
        onSuccess: () => { 
        console.log("Connected!");
        client.subscribe(receivetopic);
        client.onMessageArrived = receive;
      },
      onFailure: () => {
        console.log("Failed to connect!"); 
        setalive(3)
      }
      }
    );
    (async () => {
      let { status } = await Location.requestForegroundPermissionsAsync();
      if (status !== 'granted') {
        setErrorMsg('Permission to access location was denied');
        return;
      }

      // Get the initial location
      let initialLocation = await Location.getCurrentPositionAsync({
        // accuracy: Accuracy.High,
        enableHighAccuracy: true
      });
      setLocation(initialLocation);
      // console.log(initialLocation)
      templocation = initialLocation


      const intervalId = setInterval(async () => {
        let updatedLocation = await Location.getCurrentPositionAsync({});
        setLocation(updatedLocation);
        templocation = updatedLocation
        // console.log(templocation.timestamp + ", a")
        // console.log(templocation.coords.speed + ", d")
        // updatedLocation.remove();

      }, coords_interval_ms);

      return () => {
        clearInterval(intervalId);
      };

      // const locationListener = await Location.watchPositionAsync(
      //   { timeInterval: coords_interval_ms },
      //   (newLocation) => {
      //     setLocation(newLocation);
      //     templocation = newLocation
      //     console.log(templocation.timestamp + ", b")
      //     console.log(templocation.coords.speed + ", c")
      //     locationListener.remove();
      //   }
      // );

      // return () => {
      //   if (locationListener) {
      //     locationListener.remove();
      //   }
      // };

      
    })();
    const interval = setInterval(() => {
    //   var curtime = Date.now()/1000

    //   // if (temp_coords_x > 600) {
    //   //   testingTime = Date.now()/1000
    //   // }

      
    //   try {
    //     // console.log("ti " + templocation.timestamp);
    //     // console.log("la " + templocation.coords.latitude);
    //     // console.log("lo " + templocation.coords.longitude);
    //     // console.log("sp " + templocation.coords.speed);
    //     send_coords_latlong(
    //       client, 
    //       templocation.coords.latitude, 
    //       templocation.coords.longitude, 
    //       curtime,
    //       placename
    //     )
    //   } catch {
    //     console.log("Location hasn't been allowed yet")
    //   }

      // send_coords(client, temp_coords_x, temp_coords_y, curtime)
      // temp_coords_x += 20.3
      // temp_coords_y += 0
      // temp_coords_x = Math.round(temp_coords_x*100)/100
      // temp_coords_y = Math.round(temp_coords_y*100)/100
      // updateCoordsX(temp_coords_x)
      // updateCoordsY(temp_coords_y)
      // console.log(curtime - lasttimestamp)
      if (lasttimestamp != 0 && curtime - lasttimestamp >= 10) {
        setalive(3)
      }
      

    }, coords_interval_ms);
    return () => clearInterval(interval);
  }, [])

  function send_coords_latlong(c, lat, long, time, place) {

    const message = new Paho.Message((
      ped_id + "," + 
      lat + "," + 
      long + "," + 
      time + "," +
      place
    ).toString());

    message.destinationName = sendtopic;

    try {
      c.send(message);
    } catch {
      console.log("Failed to send message. Try refreshing?")
    }

  }

  function send_yongjie_ping(c, time) {

    const message = new Paho.Message((
      ped_id + "," + 
      "0" + "," + 
      "0" + "," + 
      time + "," +
      ""
    ).toString());

    message.destinationName = yongjiesendtopic;

    try {
      c.send(message);
    } catch {
      console.log("Failed to send message. Try refreshing?")
    }

  }

  return (
    <View style={styles.container}>
      <View style={{height: '40%', alignItems: 'center', justifyContent: 'center',}}>
        <Text style={{color: alive_chart[good]['color'], fontSize: 50}}>
          {alive_chart[good]['text']}
        </Text>
      </View>
      <View style={{height: '50%', alignItems: 'center', justifyContent: 'center'}} onLayout={(event) => {
      var {x, y, width, height} = event.nativeEvent.layout;
      changeGraphHeight(height)
      changeGraphWidth(width)}}>
        <ScatterPlot 
          gridSize={10}
          futuredata={futureData}
          realtimedata={realtimeData}
          width={graphWidth}
          height={graphHeight}
        />
        <Text>Real Time Graph of Trajectories</Text>
      </View>
      <View style={{height: '10%', alignItems: 'center', justifyContent: 'center',}}>
        <Text>
          Your Coords: ({location.coords.latitude}, {location.coords.longitude}) {'\n'}
          Timestamp: {location.timestamp}
        </Text>
      </View>
    </View>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: '#fff',
    alignItems: 'center',
    justifyContent: 'center',
  },
  graph: {
    flex: 1,
    width: 300,
  },
  image: {
    flex: 1,
    justifyContent: 'center',
    width:300,
    height:'61%'
  },
});

export default App