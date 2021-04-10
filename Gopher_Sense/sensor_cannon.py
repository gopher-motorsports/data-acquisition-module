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
PATH_SEP = "\\"
# C:\\Users\\ian\\STM32CubeIDE\\workspace_1.3.0\\data-acquisition-module\\Core\\Resources\\dam_hw_config.yaml

def C_ize_Name(name):
    return name.replace(' ', '_').lower()

def NoneOnValueError(d, k):
    try:
        return d[k]
    except(KeyError):
        return None


class Module():
    def __init__(self, ):
        pass


# convienient container for data
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
            self.numTableEntries = int(len(self.table['entries'])/2) #always even
            for i in range(self.numTableEntries):
                self.tableEntries[0].append(self.table['entries']["independent{}".format(i+1)])
                self.tableEntries[1].append(self.table['entries']["dependent{}".format(i+1)])
              
# convienient container for data
class CANSensor():
    def __init__(self, sensorID, name, outputs, byte_order, messages):
        self.sensorID = sensorID
        self.name = C_ize_Name(name)
        self.outputs = outputs
        self.byte_order = byte_order
        self.messages = messages
        self.numMessages = len(messages)
        self.runCoherenceCheck()
#     def getOutputQuantization(self, output):
#         if output in self.outputs:
#             return self.outputs[output]['quantization']
#         else:
#             return None
#     def getOutputOffset(self, output):
#         if output in self.outputs:
#             return self.outputs[output]['offset']
#         else:
#             return None
    def runCoherenceCheck(self):
        # TODO check for messages that output an output not listed or if outputs arent produced by messages
        pass
    
def main():
    argv = sys.argv
    if len(argv) < 2:
        print("Pass the path to the hardware config file: somepath\\some_module_hwconfig.yaml")
        sys.exit()
    
    sensorFile = open(SENSOR_CONFIG_FILE)
    configFile = open(argv[1])
    configFileName = argv[1].split(PATH_SEP)[-1].replace(".yaml", "")
    print(configFileName)
    sensor_raw = yaml.full_load(sensorFile)
    hwconfig_raw = yaml.full_load(configFile)
    hwconfig_munch = munch.Munch(hwconfig_raw)
    sensors_munch = munch.Munch(sensor_raw)
    sensors = sensors_munch.sensors
    
    
    # define sensor objects
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
    h_filename = 'gopher_sense_TEMPLATE.h.jinja2'
    c_filename = 'gopher_sense_TEMPLATE.c.jinja2'
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

    module = Module()
    

if __name__ == '__main__':
    main()
    print('done')
