'''
Created on Apr 3, 2021

@author: ian
'''

import sys
import os
import yaml
import munch
from jinja2 import Template



TEMPLATES_DIRECTORY = "Templates"
OUTPUT_DIRECTORY = "Build"
SENSOR_CONFIG_FILE = "sensors.yaml"


def C_ize_Name(name):
    return name.replace(' ', '_').lower()

def NoneOnValueError(d, k):
    try:
        return d[k]
    except(KeyError):
        return None


class DAM():
    def __init__(self, hwconfig):
        self.hwconfig = hwconfig
        self.pins = []
        for pin in self.hwconfig['data_input_methods']['pins']:
            self.pins.append(pin)
        
        self.can_sensors = []
        for sensor in self.hwconfig['data_input_methods']['can_sensors']:
            self.can_sensors.append(sensor)



class AnalogSensor():
    def __init__(self, sensorID, name, outputs, analog):
        self.sensorID = sensorID
        self.name = C_ize_Name(name)
        self.outputs = outputs
        self.analog = analog
        self.table = self.analog['table'] 
        self.tableEntries = ([],[]) #entries in order (independent, dependent)
        self.numTableEntries = None
        if self.table != None:
            self.numTableEntries = int(len(self.table['entries'])/2)
            for i in range(self.numTableEntries):
                self.tableEntries[0].append(self.table['entries']["independent{}".format(i+1)])
                self.tableEntries[1].append(self.table['entries']["dependent{}".format(i+1)])
              
class CANSensor():
    def __init__(self, sensorID, name, outputs, byte_order, messages):
        self.sensorID = sensorID
        self.name = C_ize_Name(name)
        self.outputs = outputs
        self.byte_order = byte_order
        self.messages = messages
        self.numMessages = len(messages)
        self.runCoherenceCheck()
    def getOutputQuantization(self, output):
        if output in self.outputs:
            return self.outputs[output]['quantization']
        else:
            return None
    def getOutputOffset(self, output):
        if output in self.outputs:
            return self.outputs[output]['offset']
        else:
            return None
    def runCoherenceCheck(self):
        # TODO check for messages that output an output not listed or if outputs arent produced by messages
        pass
    
def main():
#     argv = sys.argv
#     if len(argv < 3):
#         print("Need 2 args: SensorDefFilePath.yaml HWConfigFilePath.yaml")
#         sys.exit()
     
    argv = ['','C:\\Users\\ian\\STM32CubeIDE\\workspace_1.3.0\\data-acquisition-module\\Gopher_Sense\\sensors.yaml',\
            'C:\\Users\\ian\\STM32CubeIDE\\workspace_1.3.0\\data-acquisition-module\\Setup\\hw_config.yaml']
    sensorFile = open(SENSOR_CONFIG_FILE)
    #configFile = open(argv[2])
    
    sensor_raw = yaml.full_load(sensorFile)
#     hwconfig_raw = yaml.full_load(configFile)
#     hwconfig_munch = munch.Munch(hwconfig_raw)
    sensors_munch = munch.Munch(sensor_raw)
    sensors = sensors_munch.sensors
    
    analog_sensors = []
    can_sensors = []
    for s in sensors:
        sensor = sensors[s]
        if 'analog' in sensor['sensor_type']:
            a = AnalogSensor(s, sensor['name_english'], sensor['outputs'], sensor['sensor_type']['analog'])
            analog_sensors.append(a)
        if 'CAN' in sensor['sensor_type']:
            c = CANSensor(s, sensor['name_english'], sensor['outputs'] , \
                          sensor['sensor_type']['CAN']['byte_order'], sensor['sensor_type']['CAN']['messages'])
            can_sensors.append(c)
    
    
    # write the sensor templates
    os.makedirs(OUTPUT_DIRECTORY, exist_ok=True)
    # Generate common header file
    h_filename = 'gopher_sense_TEMPLATES.h.jinja2'
    c_filename = 'gopher_sense_TEMPLATES.c.jinja2'
    with open(os.path.join(TEMPLATES_DIRECTORY, h_filename)) as file_:
        template = Template(file_.read())
        output = template.render(analog_sensors=analog_sensors, can_sensors=can_sensors)
        filename = "gopher_sense.h"
        with open(os.path.join(OUTPUT_DIRECTORY, filename), "w") as fh:
            fh.write(output)

    with open(os.path.join(TEMPLATES_DIRECTORY, c_filename)) as file_:
        template = Template(file_.read())
        output = template.render(analog_sensors=analog_sensors, can_sensors=can_sensors)
        filename = "gopher_sense.c"
        with open(os.path.join(OUTPUT_DIRECTORY, filename), "w") as fh:
            fh.write(output)

    

if __name__ == '__main__':
    main()
    print('done')
