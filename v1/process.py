#!/usr/bin/env python
"""
This is an interactive ICS process simulation with ModbusTCP interface
Please, refer to original Github Page for additional information
https://github.com/akiUp/ICSonPySim

By Zakir Supeyev 2020 zakir.supeyev@gmail.com
Based on Pymodbus library example code

//-----Modbus Coils Offsets (read\write)
mot_start, address: 100, boolean, Start button, 1 to activate, returns to 0 after activation
mot_stop, address: 110, boolean, Stop button, 1 to activate, returns to 0 after activation
valve_state, address: 120, boolean 0-Closed 1-Open (Controlled by start/stop logic)
mat_auto, address:130, boolean, 1-Pump automatic mode(by setpoints), 0 - manual mode
//-----Modbus input status (Discrete Inputs) Offsets(read only)
mot_run, address: 100, boolean, 1 running, 0 stop
mot_trip, address: 110, boolean, Motor trip state, cause: Tank full, Valve closed, Random trip (1 of 10000)
//-----Modbus Input Register Offsets (read only)
mot_load, address: 100; Uint16, range:0-100, random motor load simulation
flowm_flow, address: 110, Uint16, range:0-10, flow value depending on mot_load 
tank_level, address: 120, Uint16, range:0-65500, 65000 value trips the motor, has constant (random of 4) drainage flow
tank_drain,  address: 130; Uint16, Random drain by process
//-----Modbus Holding Register Offsets (read\write)
tank_Hi, address: 100; Uint16, adjustable Hi level setpoint, for turning motor OFF in AUTO mode
tank_Lo, address: 110; Uint16, adjustable Lo level setpoint, for turning motor ON in AUTO mode
"""
# --------------------------------------------------------------------------- #
# import the modbus libraries we need
# --------------------------------------------------------------------------- #
import random
from pymodbus.server.asynchronous import StartTcpServer
from pymodbus.device import ModbusDeviceIdentification
from pymodbus.datastore import ModbusSparseDataBlock
from pymodbus.datastore import ModbusSlaveContext, ModbusServerContext
#from pymodbus.transaction import ModbusRtuFramer, ModbusAsciiFramer

# --------------------------------------------------------------------------- #
# import the twisted libraries we need
# --------------------------------------------------------------------------- #
from twisted.internet.task import LoopingCall

# --------------------------------------------------------------------------- #
# configure the service logging
# --------------------------------------------------------------------------- #
import logging
logging.basicConfig()
log = logging.getLogger()
log.setLevel(logging.INFO) # set to logging.DEBUG if you need more details in console output

# --------------------------------------------------------------------------- #
# define your callback process
# --------------------------------------------------------------------------- #


def Process(mbcontext):
	""" The stateless function simulates water threatment process and updates modbus register values accordingly
	"""
#------------------------------------------------
#Mapping register values to corresponding variables 
#1-coils, 2-discrete inputs, 4 - input registers, 3 - holding registers, 
#------------------------------------------------
	context = mbcontext[0] #mapping function argument to internal variable
	slave_id = 0x00 #Slave ID is selected as 0
	#motor pump variables
	mot_load = context[slave_id].getValues(4, 100, count=1)  #load of the motor
	mot_trip = context[slave_id].getValues(2, 110, count=1)  #motor tripping state variable
	mot_run = context[slave_id].getValues(2, 100, count=1) #motor 'RUN' state variable
	mot_auto = context[slave_id].getValues(1, 130, count=1)  #Auto-Manual mode toggle
	mot_randerr = 0  #motor random error (not implemented)
	mot_start = context[slave_id].getValues(1, 100, count=1) #100 
	mot_stop = context[slave_id].getValues(1, 110, count=1) #110 
	valve_state = context[slave_id].getValues(1, 120, count=1) #120  #intentionally making it externally writable for process attack scenarios

	#Flow meter variable
	flowm_flow = context[slave_id].getValues(4, 110, count=1)
 
	#Tank variables
	tank_level = context[slave_id].getValues(4, 120, count=1)  #Tank level 0=empty (read from register)
	tank_drain = context[slave_id].getValues(4, 130, count=1) #tank drain flowmeter readings
	tank_HH = 65500  #tank maximum capacity (HiHi alarm)
	''' Tank setpoints intentionally set externally writable to adjust process and possible process attacks'''
	tank_Hi = context[slave_id].getValues(3, 100, count=1)  #Motor stop Setpoint capacity (Hi alarm)
	tank_Lo = context[slave_id].getValues(3, 110, count=1)  #Motor start Setpoint capacity (Hi alarm)


#-------------------------
#Start of Process logic
#-------------------------
	if mot_run[0]==True: #-----checking running state and running process if True
		mot_start[0] = False  #reset start signal to 0
		#mot_randerr = random (10000)  # random error function for motor
		mot_load[0] = 60+random.randint(0, 4)*10  # simulate random motor load 
		flowm_flow[0] = int(mot_load[0]/10)  # simulate flow dependency on motor load
		tank_level[0] = int(tank_level[0])+int(flowm_flow[0])  #simulate tank filling dependency from flow
          
     #tripping motor on valve state      
		if valve_state[0] == False: 
			#ifdef Debug
			log.warning('Valve trip!')
			#endif
			flowm_flow[0] = 0  #no flow due to motor trip
			mot_load[0]= 0  #no load due to motor trip
			mot_run[0] = 0  #Reset RUN condition
			mot_trip[0] = True  #motor trip bit on
			valve_state[0] = False #fail-close valve simulation

     #tripping on full condition(HiHi trip) 
		if tank_level[0]>tank_HH: 
			#ifdef Debug
			log.warning('Tank overflow trip!') 
			#endif
			flowm_flow[0] = 0  #no flow due to motor trip
			mot_load[0] = 0  #no load due to motor trip
			mot_run[0] = 0  #Reset RUN condition
			mot_trip[0] = True  #motor trip bit on
			valve_state[0] = False #fail-close valve simulation

    #-----Stop signal routine in process(maybe redundant, need to rethink in next rev) 
		if mot_stop[0] == True: 
			#ifdef Debug
			log.info('STOP signal recieved') 
			#endif
			mot_run[0] = False  #stopping motor
			flowm_flow[0] = 0  #no flow due to motor stop
			mot_load[0] = 0  #no load due to motor stop
			valve_state[0] = False #fail-close valve simulation
			mot_stop[0] = False  #reset stop signal to 0        
			mot_auto[0] = False  #reset operation to manual

    #-----Stop by setpoint routine in Auto Mode (stopping motor if tank level above Tank Hi value)
		if mot_auto[0] == True and tank_level[0] >= tank_Hi[0]: 
			#ifdef Debug
			log.info('Stopping on Hi setpoint') 
			#endif
			mot_run[0] = False  #stopping motor
			flowm_flow[0] = 0  #no flow due to motor stop
			mot_load[0] = 0  #no load due to motor stop
			valve_state[0] = False #fail-close valve simulation
			mot_stop[0] = False  #reset stop signal to 0 

	else:   #wrapper in case of motor not running
		if mot_start[0] == True: #motor starting routine
			log.info('START signal recieved, starting motor') 
			mot_stop[0] = False  #reset stop signal to 0 if set to avoid failstart
			mot_run[0] = True  #assign start coil status to RUN state
			mot_trip[0] = False  #reset error bit in case of error shutdown
			valve_state[0] = True  #trigger opening valve

   #-----Start by setpoint routine in Auto Mode(starting motor if tank level below Tank Lo value)
		if mot_auto[0] == True and tank_level[0] <= tank_Lo[0]: 
			if mot_trip[0] == False: #check that motor not tripped
				log.info('Starting motor by Lo setpoint') 
				mot_run[0] = True  #assign start coil status to RUN state
				valve_state[0] = True  #trigger opening valve
    
   #placeholder for process stopping logic
	if mot_stop[0] == True: #-----Stop signal routine
		log.info('STOP signal recieved') 
		mot_run[0] = False  #stopping motor
		mot_auto[0] = False  #reset operation to manual
		mot_trip[0] = False  #reset trip status
		mot_stop[0] = False #reset stop signal to 0    

   #placeholder for tank drain logic
	if tank_level[0]>6:
		tank_level[0]=int(tank_level[0])-int(tank_drain[0])  #constant random drain if tank is not empty 
		tank_drain[0] = random.randint(0, 6) #Drain value for next iteration

   #---------------------------------
   #Update registers with new values
   #---------------------------------
	#update coils
	context[slave_id].setValues(1, 100, mot_start)
	context[slave_id].setValues(1, 110, mot_stop)
	context[slave_id].setValues(1, 120, valve_state)
	context[slave_id].setValues(1, 130, mot_auto)
	#update discrete inputs
	context[slave_id].setValues(2, 100, mot_run)
	context[slave_id].setValues(2, 110, mot_trip)
	#update input registers
	context[slave_id].setValues(4, 100, mot_load)
	context[slave_id].setValues(4, 110, flowm_flow)
	context[slave_id].setValues(4, 120, tank_level)
	context[slave_id].setValues(4, 130, tank_drain)
   #Values output to monitor process state, if not required change to log.debug along with setting logging level to info
	log.info(f"Process values:Motor running: {mot_run[0]} |Auto mode: {mot_auto[0]} |Motor load: {mot_load[0]} |Flow: {flowm_flow[0]} |Tank level: {tank_level[0]} |Tank drain: {tank_drain[0]} |Start signal: {mot_start[0]} |Stop signal: {mot_stop[0]}") 

def run_simulation_server():
    # ----------------------------------------------------------------------- # 
    # initialize your data store
    # ----------------------------------------------------------------------- # 
    
    store = ModbusSlaveContext(
        co=ModbusSparseDataBlock({100: 0, 110: 0, 120: 0, 130: 0,}),#initiate Coils
        di=ModbusSparseDataBlock({100: 0, 110: 0}), #initiate discrete inputs
        ir=ModbusSparseDataBlock({100: 0, 110: 0, 120:0, 130:0}), #initiate input registers
        hr=ModbusSparseDataBlock({100: 60000, 110: 10000}), zero_mode=True) #initiate holding registers
    context = ModbusServerContext(slaves=store, single=True)
    
    # ----------------------------------------------------------------------- # 
    # initialize the server information
    # ----------------------------------------------------------------------- # 
    identity = ModbusDeviceIdentification()
    identity.VendorName = 'akiUP'
    identity.ProductCode = 'IOP'
    identity.VendorUrl = 'https://github.com/akiUp/ICSonPySim'
    identity.ProductName = 'ICSonPy'
    identity.ModelName = 'ICS Simulation'
    identity.MajorMinorRevision = '0.0.1'
    
    # ----------------------------------------------------------------------- # 
    # run the Modbus Server with looping call of simulation
    # ----------------------------------------------------------------------- # 
    time = 0.1  # process frequency delay in seconds, increase if you want to slow down the process
    loop = LoopingCall(f=Process, mbcontext=(context,)) # Main caleer function continiously calls the Process() function
    loop.start(time, now=False) # initially delay by time
    StartTcpServer(context, identity=identity, address=("127.0.0.1", 502))


if __name__ == "__main__":
    run_simulation_server()

