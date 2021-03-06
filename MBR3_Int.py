#! /usr/bin/python

# A simple Python command line tool to CapSense Button Status on I2C IO Expander


import sys
import time
import smbus
import threading
from _button import Button

# GPIO definitions (BCM)
GPIO_BUTTON = 23

bus = smbus.SMBus(1)
#/* Slave Address (Default) */
SLAVE_ADDR = 0x37

#/* Global Variables */#
global stop
global buttonStat
global slider1Position
global slider2Position
global proxStat
global gpio_interrupt_on
global gpio_interrupt_number
global timer_on
global SP1_list
global SP2_list
global touch_state

TOUCH_NONE = 0
TOUCH_BUTTON = 1
TOUCH_PROX = 2
TOUCH_CW = 3
TOUCH_CCW = 4
#/* Register Offsets/sub addresses */#  
REGMAP_ORIGIN = 0x00
BTN_STAT = 0xAA
GPO_OUTPUT_STATE = 0x80
SENSOR_ID = 0x82
CTRL_CMD = 0x86
SILIDER1_POSITION = 0xb0
SILIDER2_POSITION = 0xb2
PROX_STAT = 0xae

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


def gpio_int_callback():
    global gpio_interrupt_on

    retry = 1
    while(retry):
        try:
            slider1Position = bus.read_byte_data(SLAVE_ADDR, SILIDER1_POSITION)
            #print('slider1Position %d' % slider1Position)
            slider2Position = bus.read_byte_data(SLAVE_ADDR, SILIDER2_POSITION)
            #print('slider2Position %d' % slider2Position)	
            buttonStat = bus.read_byte_data(SLAVE_ADDR, BTN_STAT)
            #print('buttonStat %d ' % buttonStat)
            proxStat = bus.read_byte_data(SLAVE_ADDR, PROX_STAT)
            #print('proxStat %d ' % proxStat)  
            gpio_interrupt_on = True           
            retry = 0   
            return   
        except:
            retry = retry + 1
            if(retry == 10):
                print(' Failed 10 times to Read BUtton Status!!')   

def _timer_callback():
    global timer_on
    global gpio_interrupt_number
    timer_on = False
    gpio_interrupt_number = 0
    print("_timer_callback")

def readStatus():
    global gpio_interrupt_on
    global gpio_interrupt_number
    global slider1Position
    global slider2Position
    global buttonStat
    global proxStat
    global timer_on
    global SP1_list
    global SP2_list
    global touch_state

    SP1_list = []
    SP2_list = []
    gpio_interrupt_on = False
    gpio_interrupt_number = 0
    gpio_pin_int = Button(channel=GPIO_BUTTON)
    gpio_pin_int.on_press(gpio_int_callback)  
    print("read status start")
    while True:
        if gpio_interrupt_on:
            print("interrupt on ")
            gpio_interrupt_on = False
            """
                if slider1Position < 255 or slider2Position < 255:
                                    
                    if gpio_interrupt_number == 0:
                        if timer_on == False:
                            # set 1 second for detecting is slider continuous operation or not
                            timer = threading.Timer(1, _timer_callback)
                            timer.start()  ####threads can only be started once 
                            timer_on = True  
                    if timer_on:
                        if gpio_interrupt_number == 0:     
                            SP1_list[0] = slider1Position
                            SP2_list[0] = slider2Position
                            gpio_interrupt_number = gpio_interrupt_number + 1   
                        elif gpio_interrupt_number == 1:     
                            SP1_list[1] = slider1Position
                            SP2_list[1] = slider2Position
                            gpio_interrupt_number = gpio_interrupt_number + 1                          
                        else:
                            gpio_interrupt_number = 0
                            # Slide clockwise
                            if SP1_list[1] > SP1_list[0] or SP2_list[1] > SP2_list[0]:
                                touch_state =  TOUCH_CW
                                print("TOUH_CW")
                            #slide anticlockwise
                            elif SP1_list[1] < SP1_list[0] or SP2_list[1] < SP2_list[0]:
                                touch_state =  TOUCH_CCW
                                print("TOUCH_CCW")
                elif proxStat == 2:
                    touch_state =  TOUCH_PROX
                    print("TOUCH_PROX")
                elif buttonStat == 2:
                    touch_state = TOUCH_BUTTON
                    print("TOUCH_BUTTON")
                else:
                    touch_state = TOUCH_NONE
                    print("TOUCH_NONE")
        """ 


if __name__ == "__main__":
    global stop
    global gpio_interrupt_on
    global gpio_interrupt_number
    global slider1Position
    global slider2Position
    global buttonStat
    global proxStat
    global timer_on
    global SP1_list
    global SP2_list
    global touch_state

    buttonStat = 0
    slider1Position = 0
    slider2Position = 0
    proxStat = 0
    SP1_list = []
    SP2_list = []
    timer_on = False
    gpio_interrupt_on = False
    gpio_interrupt_number = 0
    gpio_pin_int = Button(channel=GPIO_BUTTON)
    gpio_pin_int.on_press(gpio_int_callback)     
    #global flag to stop the thread
    stop = 0 
    init_MBR3()
    while 1:
        retry = 1
        if gpio_interrupt_on:
            print("interrupt on ")
            gpio_interrupt_on = False
            if slider1Position < 255 or slider2Position < 255:                      
                    if gpio_interrupt_number == 0 and timer_on == False:
                        # set 1 second for detecting is slider continuous operation or not
                        timer = threading.Timer(1, _timer_callback)
                        timer.start()  ####threads can only be started once 
                        timer_on = True
                        print("timer start") 
                    if timer_on:
                        if gpio_interrupt_number == 0:     
                            SP1_list.insert(0, slider1Position)
                            SP2_list.insert(0, slider2Position)
                            gpio_interrupt_number = gpio_interrupt_number + 1 
                            print("gpio_interrupt_number= 0")  
                        elif gpio_interrupt_number == 1:     
                            SP1_list.insert(1, slider1Position)
                            SP2_list.insert(1, slider2Position)
                            gpio_interrupt_number = gpio_interrupt_number + 1 
                            print("gpio_interrupt_number= 1")                           
                        else:
                            print("gpio_interrupt_number>1")  
                            gpio_interrupt_number = 0
                            # Slide clockwise
                            if SP1_list[1] > SP1_list[0] or SP2_list[1] > SP2_list[0]:
                                touch_state =  TOUCH_CW
                                print("TOUH_CW")
                            #slide anticlockwise
                            elif SP1_list[1] < SP1_list[0] or SP2_list[1] < SP2_list[0]:
                                touch_state =  TOUCH_CCW
                                print("TOUCH_CCW")
            if proxStat == 2:
                touch_state =  TOUCH_PROX
                print("TOUCH_PROX")
            if buttonStat == 2:
                touch_state = TOUCH_BUTTON
                print("TOUCH_BUTTON")
            else:
                touch_state = TOUCH_NONE
                print("TOUCH_NONE")
        #readStatus()
        time.sleep(0.2) 
      
      
