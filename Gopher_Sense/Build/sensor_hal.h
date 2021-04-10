/*
 * dam_config.h
 *
 *  Created on: Mar 18, 2021
 *      Author: ian
 */

#ifndef INC_SENSOR_HAL_H_
#define INC_SENSOR_HAL_H_
#include "../../gophercan-lib/GopherCAN_structs.h"



typedef union
{
  U8_CAN_STRUCT;
  U16_CAN_STRUCT;
  U32_CAN_STRUCT;
  U64_CAN_STRUCT;
  S8_CAN_STRUCT;
  S16_CAN_STRUCT;
  S32_CAN_STRUCT;
  S64_CAN_STRUCT;
  FLOAT_CAN_STRUCT;
} GENERAL_PARAMETER;


// scales data according to a multiplicative quantization
// and additive offset
typedef struct
{
    float   quantization;
    float   offset;
} DATA_SCALAR;


typedef struct
{
    GENERAL_PARAMETER*  list;
    U16                 len;
} PARAM_LIST;



// describes a bucket of parameters
typedef struct
{
    U8          bucket_id;
    U8          frequency;
    PARAM_LIST  bucket;
} BUCKET;

typedef enum
{
    RATIOMETRIC_LINEAR = 0,
    ABSOLUTE_LINEAR = 1,
    TABULAR = 2
} OUTPUT_MODEL_TYPE;

typedef enum
{
    PSI = 0,
    VOLTS = 1,
    MILLIAMPS = 2,
    DEGREES_C = 3,
    DEGREES_F = 4,
    DEGREES_PER_SEC = 5,
    G = 6,
    MILLIMETERS = 7,
    OHMS = 8
} UNIT;

typedef struct
{
    UNIT    independent_unit;
    UNIT    dependent_unit;
    float*  independent_vars;
    float*  dependent_vars;
    U16     num_entries;
}TABLE;

typedef enum
{
    LSB = 0,
    MSB = 1
} BYTE_ORDER;


// how to turn raw data into useable measurments
typedef struct
{
    OUTPUT_MODEL_TYPE   type;
    UNIT                measurement_unit;
    float               low_bar;
    float               high_bar;
    float               low_bar_value;
    float               high_bar_value;
    float               supply_voltage;
    float               inline_resistance;
    TABLE*              table;
} OUTPUT_MODEL;

// what is this data?
typedef struct
{
    char         output_name[50];
    DATA_SCALAR  scalar;
    U8           data_size_bits;
} OUTPUT;


// describes an analog sensor
typedef struct
{
    char            sensor_id[50];
    OUTPUT_MODEL    model;
    OUTPUT          output;
} ANALOG_SENSOR;



typedef enum {
    HIGH_PASS = 0,
    LOW_PASS = 1
} FILTER_TYPE;


// describes how to filter a parameter
typedef struct
{
    GENERAL_PARAMETER   filtered_param;
    FILTER_TYPE         filter_type;
    U16                 filter_value;
} FILTERED_PARAM;


// link between gophercan parameter and analog sensor data
typedef struct
{
    GENERAL_PARAMETER   analog_param; // raw data
    ANALOG_SENSOR       analog_sensor;
    FILTERED_PARAM*     filter_subparams;
    U8                  num_filtered_subparams;
    U16                 samples_to_buffer;
} ANALOG_SENSOR_PARAM;


// describes how to interpret a part of a CAN sensor message
typedef struct
{
  U16       message_id;
  OUTPUT    output;
  U8        data_start;
  U8        data_end;
} SENSOR_CAN_MESSAGE;

// describes a CAN sensor
typedef struct
{
    char                sensor_id[50];
    BYTE_ORDER          byte_order;
    SENSOR_CAN_MESSAGE* messages;
    U8                  num_messages;
} CAN_SENSOR;


// link between gophercan parameter and CAN sensor data
typedef struct
{
    GENERAL_PARAMETER can_param; // raw data
    CAN_SENSOR        can_sensor;
    FILTERED_PARAM*   filter_subparams;
    U8                num_filtered_params;
    U16               samples_to_buffer;
} CAN_SENSOR_PARAM;





#endif /* INC_SENSOR_HAL_H_ */
