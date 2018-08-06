#! /usr/bin/python

# A simple Python command line tool to CapSense Button Status on I2C IO Expander


import sys
import time
import smbus
from _button import Button

# GPIO definitions (BCM)
GPIO_BUTTON = 23
gpio_button_int = Button(channel=GPIO_BUTTON)

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
    0x7F, 0x7F, 0x7F, 0x7F, 0x0D, 0x00, 0x00, 0x00,
    0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x01, 0x00,
    0x05, 0x00, 0x00, 0x02, 0x00, 0x02, 0x00, 0x00,
    0x00, 0x00, 0x00, 0x00, 0x00, 0x1E, 0x1E, 0x00,
    0x00, 0x1E, 0x1E, 0x00, 0x00, 0x00, 0x01, 0x01,
    0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00,
    0x00, 0x00, 0x00, 0x00, 0x04, 0x03, 0x01, 0x58,
    0x00, 0x37, 0x06, 0x00, 0x00, 0x05, 0x00, 0x00,
    0x00, 0x00, 0x00, 0x00, 0x00, 0x01, 0x00, 0x00,
    0x00, 0x25, 0x2D, 0x80, 0x00, 0x00, 0x00, 0x23,
    0x2D, 0x80, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00,
    0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00,
    0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x66, 0x6E
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
    
    applyConfig()
    
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

def on_button_pressed():
    retry = 1
    while(retry):
        try:
            slider1Position = bus.read_byte_data(SLAVE_ADDR, SILIDER1_POSITION)
            print('slider1Position %d' % slider1Position)
            slider2Position = bus.read_byte_data(SLAVE_ADDR, SILIDER2_POSITION)
            print('slider2Position %d' % slider2Position)	
            buttonStat = bus.read_byte_data(SLAVE_ADDR, BTN_STAT)
            print('buttonStat %d ' % buttonStat)
            addr = bus.read_byte_data(SLAVE_ADDR, 0x90)
            print(addr)               
            retry = 0   
            return   
        except:
            retry = retry + 1
            if(retry == 10):
                print(' Failed 10 times to Read BUtton Status!!')     

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
    gpio_button_int.on_press(on_button_pressed)  
    init_MBR3()
    while 1:
        retry = 1
        time.sleep(0.2) 
        while(retry):
            try:
                """
                slider1Position = bus.read_byte_data(SLAVE_ADDR, SILIDER1_POSITION)
                print('slider1Position %d' % slider1Position)
                slider2Position = bus.read_byte_data(SLAVE_ADDR, SILIDER2_POSITION)
                print('slider2Position %d' % slider2Position)	
                buttonStat = bus.read_byte_data(SLAVE_ADDR, BTN_STAT)
                print('buttonStat %d ' % buttonStat)
                addr = bus.read_byte_data(SLAVE_ADDR, 0x90)
                print(addr)
                """                
                retry = 0
   
            except KeyboardInterrupt:
                print('Received Keyboard Interrupt')
                print(' Exiting the Program')
                stop = 1       
            except:
                retry = retry + 1
                if(retry == 10):
                    print(' Failed 10 times to Read BUtton Status!!')
                    sys.exit()
    print('EXIT')
      
      
