# RotorHazard OBS Websocks Control Plugin
This system allows RotorHazard to communicate to [OBS Studio](https://obsproject.com/) video application and control the video remotely. The Rotohazard start race and stop race events will start and stop the video recording automatly.

This software is distributed as form of plugin to be added to the RotorHazard.

## Features
* Start/Stop OBS recording at every race. 
* Star recording before race starts (parameter in milliseconds)
* Restart connection to OBS in case of a failed call to the Webservice
* A start/stop recording failure raises a high-priority message in the front end.
 

## Compatibility between plugin and Rotohazard
 * Plugin version 1.x is compatible with RotorHazard version 3.2.x only.
 * Plugin version 2.x is compatible with Rotohazard starting at version 4.0.0. 

## Installation and Setup

The system is composed of a RotoHazard plugin and a software OBS studio for video recording.

### Install Plugin

Current version requires RotorHazard verion 4.0.0 or later. 

Copy the `obs_control` plugin into the `src/server/plugins` directory in your RotorHazard install.

Install dependencies. File available inside the plugin directory.

```
    pip install -r .\requirements.txt
```

### Configure Plugin

In RotorHazard's `config.json` file, add the following section.

```
"OBS_WS": {
	"ENABLED": true,
	"HOST": "127.0.0.1",
	"PORT": 4444,
	"PASSWORD": "YourPassword",
	"PRE_START": 2000
  }
```

Set your OBS parameters like IP, port, and password.

This plug-in can be active/inactive by setting the parameter ENABLED accordingly.

The recording can be activated before the race starts by setting the parameter PRE_START with int value (milliseconds) to the start. Note, the waiting is done in intervals of 0,1 seconds.


### On the OBS app

Go to tools > obs-socket_sething

<img src="image/obs_01_menu.png" alt="drawing" width="600"/>

Then set the server port and the password. 

<img src="./image/Obs_02_sethings.png" alt="drawing" width="600"/>
