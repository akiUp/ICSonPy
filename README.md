# ICSonPy
> Realtime Process Simulation of Plant Water Supply Unit

> Simulation Generates logically correct Modbus signals of Water Supply facility using Python with ModbusTCP interface

> Simulation uses https://github.com/riptideio/pymodbus lybrary

> Python script could run on any Linux system with python 3.6 and above (Kali Linux, Ubuntu, Debian) should also run on Raspberry Pi like boards

> Simulation can be used for HMI and PLC's Modbus interface card testing with realtime values and for ICS security research

> The project is a migration of https://github.com/akiUp/ICSUnitSim project from Arduino like platform.

## Version history
- V1 Project migrated from arduino/ESP32 platform

## Table of Contents
- [Version history](#Version)
- [Simulation setup](#Simulation)
- [HMI Example](#HMI)
- [Virtual process P&ID](#Virtual)
- [Modbus addressing](#Modbus)
- [Credits](#Credits)


## Simulation Setup

>The Modbus server implementation requires super user rights

copy the process.py script into user area like /home/kali/

to run the server use below command from script directory
```shell
sudo python3 process.py
```

by default server will start on current machine ip and port 502

## HMI Visualization Example

For simple Modbus values reading/writing/monitoring you could use python scripts from my Modbus_Bruteforce repo https://github.com/akiUp/modbus_bruteforce

Current HMI Example is designed on Ignition SCADA by Inductive Automation

<a href="https://github.com/akiUp/ICSUnitSim/tree/master/HMI_Project"> HMI_Project folder</a> contains latest backup of Ignition HMI Project, restore it into you Ignition setup for below result. 

<a href="https://github.com/akiUp/ICSUnitSim"><img src="https://github.com/akiUp/ICSUnitSim/blob/master/v02/img/ICSonChip.gif" title="HMI demo" alt="HMI Demo"></a>

Free trial versions of HMI software like RapidSCADA, Ignition and Advantech are available on internet.

## Virtual process's P&ID

<a href="https://github.com/akiUp/ICSUnitSim"><img src="https://github.com/akiUp/ICSUnitSim/blob/master/v02/img/ICSUnitSimP%26IDv02.png" title="Simulation P&ID" alt="Simulation P&ID"></a>

## Modbus addressing

> !Important!: Modbus library uses 0 based adressing

- ***Modbus Coils Offsets (read\write)***
```shell
mot_start, address: 100, boolean, Start button, 1 to activate, returns to 0 after activation

mot_stop, address: 110, boolean, Stop button, 1 to activate, returns to 0 after activation

valve_state, address: 120, boolean 0-Closed 1-Open (Controlled by start/stop logic)

mat_auto, address:130, boolean, 1-Pump automatic mode(by setpoints), 0 - manual mode
```
- ***Modbus input status (Discrete Inputs) Offsets(read only)***
```shell
mot_run, address: 100, boolean, 1 running, 0 stop
mot_trip, address: 110, boolean, Motor trip state, cause: Tank full, Valve closed, Random trip (1 of 10000)
```
- ***Modbus Input Register Offsets (read only)***
```shell
mot_load, address: 100; Uint16, range:0-100, random motor load simulation

flowm_flow, address: 110, Uint16, range:0-10, flow value depending on mot_load 

tank_level, address: 120, Uint16, range:0-65000, 65000 value trips the motor, has constant (random of 4) drainage flow

tank_drain,  address: 130; Uint16, Random drain by process
```
- ***Modbus Holding Register Offsets (read\write)***
```shell
tank_Hi, address: 100; Uint16, adjustable Hi level setpoint, for turning motor OFF in AUTO mode

tank_Lo, address: 110; Uint16, adjustable Lo level setpoint, for turning motor ON in AUTO mode
```

## Credits
- Based on Pymodbus's "Updating server" example script
- Inductive Automation's Ignition SCADA used for HMI Design https://inductiveautomation.com/ignition/
