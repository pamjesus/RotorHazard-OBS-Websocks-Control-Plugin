# RotorHazard-OBS-Websocks-Control-Plugin
 OBS websocks plugin for Rotorhazard to allow control recording at start and stop of the race.
 
 (This code had been in use in a local branch. Now migrated to own repo and make it public).

## Features
* Start/Stop OBS recording at every race. 
* Star recording before race starts (parameter in milliseconds)
* Restart connection to OBS in case of a failed call to the Webservice
* A start/stop recording failure raises a high-priority message in the front end.
 

## Compability
 V 1.0.0   It is compatible with RotorHazard since v3.2.0 (the start of plug-ins).
           This is temporary version; only while the existence of access to object SOCKET_IO.


## Install

Install dependencies. File available inside the plugin directory.

  pip install -r .\requirements.txt

Add the config "BS_WS", sample below, to the bottom of the config.json file.

```
{
"OBS_WS": {
	"ENABLED": true,
	"HOST": "127.0.0.1",
	"PORT": 4444,
	"PASSWORD": "YourPassword",
	"PRE_START": 2000
  }
}
```


Set your IP, port, and password.

This plug-in can be active/inactive by setting the parameter ENABLED accordingly.

The recording can be activated before the race starts by setting the parameter PRE_START with int value (milliseconds) to the start. Note, the waiting is done in intervals of 0,1 seconds.


### On the OBS app

Go to tools > obs-socket_sething

<img src="image/obs_01_menu.png" alt="drawing" width="600"/>

Then set the server port and the password. 

<img src="./image/Obs_02_sethings.png" alt="drawing" width="600"/>




