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

def getSensorNameFromID(id, sensors):
    for sensor in sensors:
        if id == sensor.sensorID:
            return sensor.name
    return None


class Param():
    def __init__(self, param_name, id, filtered_params, buffer_size, producer, filter, dependency):
        self.param_name = param_name
        self.id = id
        self.filtered_params = filtered_params
        self.buffer_size = buffer_size
        self.producer = producer
        self.filter = filter #(type, value) tuple
        self.dependency = dependency

class Module():
    def __init__(self, name, id, adc_input, can_input, params, analog_sensors, can_sensors):
        self.analog_sensors = analog_sensors
        self.can_sensors = can_sensors
        
        self.name = name
        self.id = id
        self. adc_channels = adc_input
        self.can_input = can_input
        
        self.adc1_params = []
        self.adc2_params = []
        self.adc3_params = []
        
        self.can_params = []

        
        self.params = params
        for p in self.params:
            param = self.params[p]
            producer = param['produced_by']

            filtered_params = []
            if param['filter_subparams']:
                for f_p in param['filter_subparams']:
                    fp = param['filter_subparams'][f_p]
                    filteredP = Param(fp, fp['gophercan_id'] , [], 0, producer, (fp['filter_type'].upper(),fp['filter_value']), None)
                    filtered_params.append(filteredP)
            p = Param(p, param['gophercan_id'], filtered_params, param['buffering']['num_samples_buffered'], producer, None, param['depends_on'] )
            if ("ADC1" in producer):
                self.adc1_params.append(p)
            elif ("ADC2" in producer):
                self.adc2_params.append(p)
            elif ("ADC3" in producer):
                self.adc3_params.append(p)
            elif ("can" in producer):
                self.can_params.append(p)
        self.adc1_params.sort(key=lambda param:param.producer, reverse=True)
#         for p in self.adc1_params:
#             print(p.producer)
        self.adc2_params.sort(key=lambda param:param.producer, reverse=True)
#         for p in self.adc2_params:
#             print(p.producer)
        self.adc3_params.sort(key=lambda param:param.producer, reverse=True)
#         for p in self.adc3_params:
#             print(p.producer)
                
                
    def getSensorName(self, id):
        aid = None
        cid = None
        if id in self.adc_channels:
            aid = self.adc_channels[id]['sensor']
        if id in self.can_input:
            cid = self.can_input[id]['sensor']
        for asensor in self.analog_sensors:
            if asensor.sensorID == aid:
                return asensor.name
        for csensor in self.can_sensors:
            if csensor.sensorID == cid:
                return csensor.name
        return None
    
    def getDependencyMessageIndex(self, name, dependency):
        sensor = None
        for s in self.can_sensors:
            if s.name == name:
                sensor = s
                break
        if sensor == None:
            return None
        idx = 0
        for message in sensor.messages:
            if sensor.messages[message]['output_measured'] == dependency:
                return idx
            idx += 1
        return None

class Bucket():
    def __init__(self, id, frequency, params):
        self.id = id
        self.frequency = frequency
        self.params = params

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
    sensor_h_filename = 'gopher_sense_TEMPLATE.h.jinja2'
    sensor_c_filename = 'gopher_sense_TEMPLATE.c.jinja2'
    with open(os.path.join(TEMPLATES_DIRECTORY, sensor_h_filename)) as file_:
        template = Template(file_.read())
        output = template.render(analog_sensors=analog_sensors, can_sensors=can_sensors)
        filename = "gopher_sense.h"
        with open(os.path.join(OUTPUT_DIRECTORY, filename), "w") as fh:
            fh.write(output)

    with open(os.path.join(TEMPLATES_DIRECTORY, sensor_c_filename)) as file_:
        template = Template(file_.read())
        output = template.render(analog_sensors=analog_sensors, can_sensors=can_sensors)
        filename = "gopher_sense.c"
        with open(os.path.join(OUTPUT_DIRECTORY, filename), "w") as fh:
            fh.write(output)
            
    module = Module(hwconfig_munch.module_name, hwconfig_munch.gophercan_module_id, hwconfig_munch['data_input_methods']['adc_channels'], \
                    hwconfig_munch['data_input_methods']['can_sensors'], hwconfig_munch['parameters_produced'], analog_sensors, can_sensors)
    buckets = []

    hwconfig_c_file = 'hwconfig_TEMPLATE.c.jinja2'
    hwconfig_h_file = 'hwconfig_TEMPLATE.h.jinja2'
    with open(os.path.join(TEMPLATES_DIRECTORY, hwconfig_c_file)) as file_:
        template = Template(file_.read())
        output = template.render(module=module, buckets=buckets, configFileName=configFileName)
        filename = configFileName + ".c"
        with open(os.path.join(OUTPUT_DIRECTORY, filename), "w") as fh:
            fh.write(output)
    with open(os.path.join(TEMPLATES_DIRECTORY, hwconfig_h_file)) as file_:
        template = Template(file_.read())
        output = template.render(module=module, buckets=buckets, configFileName=configFileName)
        filename = configFileName + ".h"
        with open(os.path.join(OUTPUT_DIRECTORY, filename), "w") as fh:
            fh.write(output)
if __name__ == '__main__':
    main()
    print('done')
