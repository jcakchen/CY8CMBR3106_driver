#! /usr/bin/python


"""driver for CapSense sensor CY8CMBR3106"""

import sys
import time
import smbus
from i2c_device import I2CDevice
from _button import Button
import threading

class touch(I2CDevice):
    """ touch driver with interrupt """
    #/* Slave Address (Default) */
    MBR3_I2CADDR = 0x37

    printed = 0 #global flag for status button change

    #/* Register Offsets/sub addresses */#  
    REGMAP_ORIGIN = 0x00
    CTRL_CMD = 0x86   
    BTN_STAT = 0xAA
    SILIDER1_POSITION = 0xb0
    SILIDER2_POSITION = 0xb2
    PROX_STAT = 0xae
    #/* Below are the Command Codes used to configure MBR3*/#
    SAVE_CHECK_CRC = 0x02
    SW_RESET = 0xFF
    DEVICE_ID = 0X90
#/* Above are the Command Codes used to configure MBR3*/#
# The below configuration array enables 2 slider, 1 proximity and 1 button 
#   The INT HI enable                   
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


    # Global Variables 
    TOUCH_NONE = 0
    TOUCH_BUTTON = 1
    TOUCH_PROX = 2
    TOUCH_CW = 3
    TOUCH_CCW = 4
    # GPIO definitions (BCM)
    GPIO_BUTTON = 23
    def __init__(self,
                 address = MBR3_I2CADDR
                ):
        self.touch_state = None
        self.gpio_pin_int = Button(channel=self.GPIO_BUTTON,debounce_time=0.01)        
        self.buttonStat = None
        self.slider1Position = None
        self.slider2Position = None
        self.proxStat = None
        self._init_MBR3()
        self.gpio_interrupt_on = False
        self.gpio_interrupt_number = 0
        self.SP1_list = []
        self.SP2_list = []

    def _sendConfiguration(self, offset, count, data):
        # This function sends the 128 bytes of configuration array to MBR3 device over #
        # I2C(1). The 128 bytes of data are sent using a byte wise i2c data transfer   #
        # method/function call                                                         #

        for i in range(offset,(offset+count),1):
            retry = 1
            while(retry):
                try:
                    self.write_int8(i,data[i])
                    retry = 0
                except:
                    retry = retry + 1
                    time.sleep(0.05)
                    if(retry == 10):
                        print('ERROR: Failed to Send Configuration 10 times!! \n')
                        exit(0)

    def _applyConfig(self):
        # This function sends save& check CRC command, waits for some time to allow #
        # MBR3 device to save the 128 bytes of configuration data and then issue a  #
        # software reset to apply the new configuration                             #
        retry = 1
        while(retry):
            try:
                self.write_int8(self.CTRL_CMD,self.SAVE_CHECK_CRC)
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
                self.write_int8(self.CTRL_CMD,self.SW_RESET)
                retry = 0
                print ('SW_RESET command sent successfully!!' )
            except:
                retry = retry + 1
                if(retry == 10):
                    print('ERROR: Failed 10 times send COMMAMD SW_RESET!!')
                    sys.exit(0)
        return

    def _init_MBR3(self):
        self._sendConfiguration(self.REGMAP_ORIGIN,128,self.configData)
        print ('Configuration Sent Sucessfully!!')  
        # Provide this delay to allow the MBR device to save the 128 bytes   #
        # of configuration sent.                                             #
        time.sleep(1)  
        self._applyConfig()
        #Delay after sending the Reset command to allow for MBR3 boot
        time.sleep(0.5) 
        return

    def _gpio_int_callback(self):
        retry = 1
        while(retry):
            try:
                self.slider1Position = self.read_uint8(self.SILIDER1_POSITION)
                print('slider1Position %d' % self.slider1Position)
                self.slider2Position = self.read_uint8(self.SILIDER2_POSITION)
                print('slider2Position %d' % self.slider2Position)	
                self.buttonStat = self.read_uint8(self.BTN_STAT)
                print('buttonStat %d ' % self.buttonStat)
                self.proxStat = self.read_uint8(self.PROX_STAT)
                print('proxStat %d ' % self.proxStat)  
                self.gpio_interrupt_on = True
                retry = 0 
                return True
            except:
                retry = retry + 1
                if(retry == 10):
                    print(' Failed 10 times to Read BUtton Status!!') 
                    return  False  

    def _timer_callback(self):
        self.timer_on = False
        self.gpio_interrupt_number = 0

    def readStatus(self):
        """
        This thread will run parallely and updates the gloab variable "buttonStat" 
        So that other threads can use this button status and trigger activities    
        Call the callback whenever the gpio pin is interrupt.
        """
        self.gpio_interrupt_on = False
        self.gpio_interrupt_number = 0
        self.gpio_pin_int.on_press(self._gpio_int_callback)  
        while True:
            if self.gpio_interrupt_on:
                self.gpio_interrupt_on = False
                if self.slider1Position < 255 or self.slider2Position < 255:
                    if self.gpio_interrupt_number < 2:                 
                        if self.gpio_interrupt_number == 0:
                            if self.timer_on == False:
                                # set 1 second for detecting is slider continuous operation or not
                                timer = threading.Timer(1, self._timer_callback)
                                timer.start()  ####threads can only be started once 
                                self.timer_on = True  
                        if self.timer_on:
                            self.SP1_list[self.gpio_interrupt_number] = self.slider1Position
                            self.SP2_list[self.gpio_interrupt_number] = self.slider2Position
                        self.gpio_interrupt_number = self.gpio_interrupt_number + 1                          
                    else:
                        self.gpio_interrupt_number = 0
                        # Slide clockwise
                        if self.SP1_list[2] > self.SP1_list[1] or self.SP2_list[2] > self.SP2_list[1]:
                            self.touch_state =  self.TOUCH_CW
                        #slide anticlockwise
                        elif self.SP1_list[2] < self.SP1_list[1] or self.SP2_list[2] < self.SP2_list[1]:
                            self.touch_state =  self.TOUCH_CCW
                elif self.proxStat == 2:
                    self.touch_state =  self.TOUCH_PROX
                elif self.buttonStat == 2:
                    self.touch_state = self.TOUCH_BUTTON
                else:
                    self.state = self.TOUCH_NONE

if __name__ == "__main__":
    #global flag to stop the thread
    touch = touch(1)
    while 1:
        try:
            touch.readStatus()
        except KeyboardInterrupt:
                print('Received Keyboard Interrupt')
                print(' Exiting the Program')     
      
      
