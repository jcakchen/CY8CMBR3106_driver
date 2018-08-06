#! /usr/bin/python

# A simple Python command line tool to CapSense Button Status on I2C IO Expander


import sys
import time
import smbus


#------------------------------------------------------------#
#/* CY8CMBR3116 Register Map Offset Address */               #
#REGMAP_ORIGIN			= 0x00
#SENSOR_PATTERN			= 0x00
#FSS_EN					= 0x02
#TOGGLE_EN				= 0x04
#LED_ON_EN				= 0x06
#SENSITIVITY0			= 0x08
#SENSITIVITY1			= 0x09
#SENSITIVITY2			= 0x0A
#SENSITIVITY3			= 0x0B
#BASE_THRESHOLD0		= 	0x0C
#BASE_THRESHOLD1		= 	0x0D
#FINGER_THRESHOLD2		= 0x0E
#FINGER_THRESHOLD3		= 0x0F
#FINGER_THRESHOLD4		= 0x10
#FINGER_THRESHOLD5		= 0x11
#FINGER_THRESHOLD6		= 0x12
#FINGER_THRESHOLD7		= 0x13
#FINGER_THRESHOLD8		= 0x14
#FINGER_THRESHOLD9		= 0x15
#FINGER_THRESHOLD10		= 0x16
#FINGER_THRESHOLD11		= 0x17
#FINGER_THRESHOLD12		= 0x18
#FINGER_THRESHOLD13		= 0x19
#FINGER_THRESHOLD14		= 0x1A
#FINGER_THRESHOLD15		= 0x1B
#SENSOR_DEBOUNCE		= 	0x1C
#BUTTON_HYS				= 0x1D
#BUTTON_BUT				= 0x1E
#BUTTON_LBR				= 0x1F
#BUTTON_NNT				= 0x20
#BUTTON_NT				= 0x21
#PROX_EN				= 	0x26
#PROX_CFG				= 0x27
#PROX_CFG2				= 0x28
#PROX_TOUCH_TH0			= 0x2A
#PROX_TOUCH_TH1			= 0x2C
#PROX_HYS				= 0x30
#PROX_BUT				= 0x31
#PROX_LBR				= 0x32
#PROX_NNT				= 0x33
#PROX_NT				= 	0x34
#PROX_POSITIVE_TH0		= 0x35
#PROX_POSITIVE_TH1		= 0x36
#PROX_NEGATIVE_TH0		= 0x39
#PROX_NEGATIVE_TH1		= 0x3A
#LED_ON_TIME			= 	0x3D
#BUZZER_CFG				= 0x3E
#BUZZER_ON_TIME			= 0x3F
#GPO_CFG				= 	0x40
#PWM_DUTYCYCLE_CFG0		= 0x41
#PWM_DUTYCYCLE_CFG1		= 0x42
#PWM_DUTYCYCLE_CFG2		= 0x43
#PWM_DUTYCYCLE_CFG3		= 0x44
#PWM_DUTYCYCLE_CFG4		= 0x45
#PWM_DUTYCYCLE_CFG5		= 0x46
#PWM_DUTYCYCLE_CFG6		= 0x47
#PWM_DUTYCYCLE_CFG7		= 0x48
#SPO_CFG				= 	0x4C
#DEVICE_CFG0			= 	0x4D
#DEVICE_CFG1			= 	0x4E
#DEVICE_CFG2			= 	0x4F
#I2C_ADDR				= 0x51
#REFRESH_CTRL			= 0x52
#STATE_TIMEOUT			= 0x55
#SLIDER_CFG				= 0x5D
#SLIDER1_CFG			= 	0x61
#SLIDER1_RESOLUTION		= 0x62
#SLIDER1_THRESHOLD		= 0x63
#SLIDER2_CFG			= 	0x67
#SLIDER2_RESOLUTION		= 0x68
#SLIDER2_THRESHOLD		= 0x69
#SLIDER_DEBOUNCE		= 	0x6F
#SLIDER_BUT				= 0x70
#SLIDER_LBR				= 0x71
#SLIDER_NNT				= 0x72
#SLIDER_NT				= 0x73
#CONFIG_CRC				= 0x7E
#GPO_OUTPUT_STATE		= 0x80
#SENSOR_ID				= 0x82
#CTRL_CMD				= 0x86
#BUTTON_STATUS			= 0xAA

#/* Command Codes */
#CMD_NULL				= 0x00
#SAVE_CHECK_CRC         =  0x02
#CALC_CRC               =  0x03
#LOAD_FACTORY           =  0x04
#LOAD_PRIMARY           =  0x05
#LOAD_SECONDARY         =  0x06
#SLEEP                  =  0x07
#CLEAR_LATCHED_STATUS   =  0x08
#CMD_RESET_PROX0_FILTER	= 0x09
#CMD_RESET_PROX1_FILTER	= 0x0A
#ENTER_CONFIG_MODE      =  0x0B
#EXIT_CONTROL_RUN       =  0xFE
#SW_RESET               =  0xFF


bus = smbus.SMBus(1)

#/* Slave Address (Default) */
SLAVE_ADDR = 0x37

#/* Global Variables */#
global stop
global buttonStat
global slider1Position
global slider2Position

printed = 0 #global flag for status button change

#/* Register Offsets/sub addresses */#  
REGMAP_ORIGIN = 0x00
BTN_STAT = 0xAA
GPO_OUTPUT_STATE = 0x80
SENSOR_ID = 0x82
CTRL_CMD = 0x86
BUTTON_STATUS = 0xAA
SILIDER1_POSITION = 0xb0
SILIDER2_POSITION = 0xb2

#/* Below are the Command Codes used to configure MBR3*/#

CMD_NULL = 0x00
SAVE_CHECK_CRC = 0x02
CALC_CRC = 0x03
LOAD_FACTORY = 0x04
LOAD_PRIMARY = 0x05
LOAD_SECONDARY = 0x06
SLEEP = 0x07
CLEAR_LATCHED_STATUS = 0x08
CMD_RESET_PROX0_FILTER = 0x09
CMD_RESET_PROX1_FILTER = 0x0A
ENTER_CONFIG_MODE = 0x0B
EXIT_CONTROL_RUN = 0xFE
SW_RESET = 0xFF

#/* Above are the Command Codes used to configure MBR3*/#


#/* The below configuration array enables all 4 buttons and Water tolerance    #
#   The Proximity Sensor and Buzzer is disabled                             */ #
configData = [
    0xC3, 0x3F, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00,
    0x00, 0x00, 0x00, 0x00, 0x80, 0x80, 0x7F, 0x7F,
    0x7F, 0x7F, 0x7F, 0x7F, 0x7F, 0x7F, 0x7F, 0x7F,
    0x7F, 0x7F, 0x7F, 0x7F, 0x03, 0x00, 0x00, 0x00,
    0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x01, 0x00,
    0x05, 0x00, 0x00, 0x02, 0x00, 0x02, 0x00, 0x00,
    0x00, 0x00, 0x00, 0x00, 0x00, 0x1E, 0x1E, 0x00,
    0x00, 0x1E, 0x1E, 0x00, 0x00, 0x00, 0x01, 0x01,
    0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00,
    0x00, 0x00, 0x00, 0x00, 0x00, 0x03, 0x01, 0x08,
    0x00, 0x37, 0x06, 0x00, 0x00, 0x0A, 0x00, 0x00,
    0x00, 0x00, 0x00, 0x00, 0x00, 0x01, 0x00, 0x00,
    0x00, 0x25, 0x2D, 0x80, 0x00, 0x00, 0x00, 0x23,
    0x2D, 0x80, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00,
    0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00,
    0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x2D, 0xE9
]


   
def sendConfiguration(address, offset, count, data):
    # This function sends the 128 bytes of configuration array to MBR3 device over #
    # I2C(1). The 128 bytes of data are sent using a byte wise i2c data transfer   #
    # method/function call                                                         #

    for i in range(offset,(offset+count),1):
        retry = 1
        while(retry):
            try:
                #print i, data[i]
                bus.write_byte_data(address,i,data[i])
                retry = 0
            except:
                retry = retry + 1
                time.sleep(0.05)
                if(retry == 10):
                    print('ERROR: Failed to Send Configuration 10 times!! \n')
                    exit(0)


def applyConfig():
    # This function sends save& check CRC command, waits for some time to allow #
    # MBR3 device to save the 128 bytes of configuration data and then issue a  #
    # software reset to apply the new configuration                             #

    retry = 1
    while(retry):
        try:
            bus.write_byte_data(SLAVE_ADDR,CTRL_CMD,SAVE_CHECK_CRC)
            retry = 0
            print ('SAVE_CHECK_CRC command sent successfully!!' )
        except:
            retry = retry + 1
            if(retry == 10):
                print('ERROR: Failed to send COMMAMD SAVE_CHECK_CRC 10 times !!')
                sys.exit(0)
    time.sleep(0.05)

    retry = 1
    while(retry):
        try:
            bus.write_byte_data(SLAVE_ADDR,CTRL_CMD,SW_RESET)
            retry = 0
            print ('SW_RESET command sent successfully!!' )
        except:
            retry = retry + 1
            if(retry == 10):
                print('ERROR: Failed 10 times send COMMAMD SW_RESET!!')
                sys.exit(0)
    return


def readStatus():
    # This thread will run parallely and updates the gloab variable "buttonStat" #
    # So that other threads can use this button status and trigger activities    #
    global buttonStat
    global slider1Position
    global slider2Position
    global stop
    while 1:
        retry = 1
        while(retry):
            try:
                slider1Position = bus.read_byte_data(SLAVE_ADDR, SILIDER1_POSITION)
                slider2Position = bus.read_byte_data(SLAVE_ADDR, SILIDER2_POSITION)
                buttonStat = bus.read_byte_data(SLAVE_ADDR, BTN_STAT)
                #print(buttonStat)
                retry = 0
   
        except KeyboardInterrupt:
            print('Received Keyboard Interrupt')
            print(' Exiting the Program')
            stop = 1
            return(0)
         
        except:
            retry = retry + 1
            if(retry == 10):
                print(' Failed 10 times to Read BUtton Status!!')
                sys.exit()

            
         
def init_MBR3():
    a = 0
    delay = 0.05
    sendConfiguration(SLAVE_ADDR, REGMAP_ORIGIN,128,configData)
    print ('Configuration Sent Sucessfully!!')
    
    # Provide this delay to allow the MBR device to save the 128 bytes   #
    # of configuration sent.                                             #
    time.sleep(1)
    
    #applyConfig()
    
    #Delay after sending the Reset command to allow for MBR3 boot
    time.sleep(0.5) 
    
    return


def displayButtonStat():
    try:
        if( slider1Position <255):
            print(' slider1 is TOUCHED \n' )

        if( slider2Position <255):
            print(' slider2 is TOUCHED \n' )      
       
    except KeyboardInterrupt:
        print('Received Keyboard Interrupt')
        print('Exiting th Program')
        stop = 1
    return
   
  
if __name__ == "__main__":
    global stop
    global slider1Position
    global slider2Position
    global buttonStat
    buttonStat = 0
    slider1Position = 0
    slider2Position = 0
    
    #global flag to stop the thread
    stop = 0 
    init_MBR3()
        
    try:
        while(1):
            slider1Position = bus.read_byte_data(SLAVE_ADDR, SILIDER1_POSITION)
            print('slider1Position %d' % slider1Position)
            slider2Position = bus.read_byte_data(SLAVE_ADDR, SILIDER2_POSITION)  
            print('slider2Position %d' % slider2Position)	
            buttonStat = bus.read_byte_data(SLAVE_ADDR, BTN_STAT)
            print('buttonStat %d' % buttonStat)
            time.sleep(0.2) 
            
    except KeyboardInterrupt:
        print('Received Keyboard Interrupt')
        print('Exiting the Program')
        stop = 1     
    print('EXIT')
      
      
