#!/usr/bin/env python
# By Micha Nisani
# lib for Psemi Peregrine USB "hi speed usb interfase" , EK-600000
# controll Multi-throw Count RF Switch Evaluation Kit (EVK)
# SP12T: PE42512, PE42412, PE426412
# SUPORT TWO USB BOARDs: A AND B
# install ancoda3
# use https://www.anaconda.com/download/success
# set paths to anaconda Scripts and main install directory
# work with 2xx driver from windows 64,  and python wraper ftd2xx
# install:
# conda install conda-forge::ftd2xx

import os
import sys
import ctypes
import time
import winsound
import ftd2xx as ftd  # install from conda, https://pypi.org/project/ftd2xx/

# Beep
frequency = 2500  # Set Frequency To 2500 Hertz
duration = 500  # Set Duration To 1000 ms == 1 second
# pins defination
LED_USB_BOARD_OFF = 0b00001000 
LED_USB_BOARD_ON = 0b00000000
pattern0      = 0b00000000
delay_rf      = 1  # 1 sec to switch

LS_pin = 0b00100000 #  uses SEN3 , pin j15-13 , jp1 open , 
LS_pin_Zero = 0b00000000
V1_pin = 0b10000000 #  uses SDA  , pin j15-11 ,
V2_pin = 0b00000010 #  use SEN   , pin j15-9 ,
V3_pin = 0b00000100 #  uses SCL  , pin j15-7 ,
V4_pin = 0b00010000 #  uses SEN2 , pin j15-5,

# use only this USB boards, change this number is you switch boards
expected_serialA = b'A10NPUDA'
expected_serialB = b'A104VAF7'


'''
Table 7 • Truth Table for SP12T
LS(1) V4 V3 V2 V1 RFC–RF1 RFC–RF2 RFC–RF3 RFC–RF4 RFC–RF5 RFC–RF6 RFC–RF7 RFC–RF8 RFC–RF9 RFC–RF10 RFC–RF11 RFC–RF12
0     0  0  0  0   ON      OFF     OFF     OFF     OFF     OFF      OFF    OFF      OFF     OFF     OFF      OFF
0     1  0  0  0   OFF     ON      OFF     OFF     OFF     OFF      OFF    OFF      OFF     OFF     OFF      OFF
0     0  1  0  0   OFF     OFF     ON      OFF     OFF     OFF      OFF    OFF      OFF     OFF     OFF      OFF
0     1  1  0  0   OFF     OFF     OFF     ON      OFF     OFF      OFF    OFF      OFF     OFF     OFF      OFF
0     0  0  1  0   OFF     OFF     OFF     OFF     ON      OFF      OFF    OFF      OFF     OFF     OFF      OFF
0     1  0  1  0   OFF     OFF     OFF     OFF     OFF     ON       OFF    OFF      OFF     OFF     OFF      OFF
0     0  1  1  0   OFF     OFF     OFF     OFF     OFF     OFF      ON     OFF      OFF     OFF     OFF      OFF
0     1  1  1  0   OFF     OFF     OFF     OFF     OFF     OFF      OFF    ON       OFF     OFF     OFF      OFF
0     0  0  0  1   OFF     OFF     OFF     OFF     OFF     OFF      OFF    OFF      ON      OFF     OFF      OFF
0     1  0  0  1   OFF     OFF     OFF     OFF     OFF     OFF      OFF    OFF      OFF     ON      OFF      OFF
0     0  1  0  1   OFF     OFF     OFF     OFF     OFF     OFF      OFF    OFF      OFF     OFF     ON       OFF
0     1  1  0  1   OFF     OFF     OFF     OFF     OFF     OFF      OFF    OFF      OFF     OFF     OFF      ON
X(2)  0  0  1  1   OFF     OFF     OFF     OFF     OFF     OFF      OFF    OFF      OFF     OFF     OFF      OFF
Notes: 
1) LS has an internal 1 MΩ pull-up resistor to logic high. Connect LS to GND externally to generate a logic 0. Leaving LS floating will generate a 
logic 1.
2) LS = don’t care, V4 = 0, V3 = 0, V2 = V1 = 1, all ports are terminated to provide an all isolated state
'''


# RF board switch input to output
RFC_RF1 = (pattern0)
RFC_RF2 = (LS_pin_Zero | V4_pin)
RFC_RF3 = (LS_pin_Zero | V3_pin)
RFC_RF4 = (LS_pin_Zero | V4_pin  | V3_pin)
RFC_RF5 = (LS_pin_Zero | V2_pin)
RFC_RF6 = (LS_pin_Zero | V4_pin  | V2_pin)
RFC_RF7 = (LS_pin_Zero | V3_pin  | V2_pin)
RFC_RF8 = (LS_pin_Zero | V4_pin  | V3_pin | V2_pin)
RFC_RF9 = (LS_pin_Zero | V1_pin)
RFC_RF10= (LS_pin_Zero | V4_pin  | V1_pin)
RFC_RF11= (LS_pin_Zero | V3_pin  | V1_pin)
RFC_RF12= (LS_pin_Zero | V4_pin  | V3_pin | V1_pin)
ALL_ISOLATED = (LS_pin_Zero | V2_pin  | V1_pin)

#----------------------------------------------------------------------------------------------------
def INIT_USB_BoardS():
    #List all connected FTDI devices
    devices = ftd.listDevices()
    if devices is None:
        print("No FTDI devices found.")
        exit(-1)
    else:
         print("Connected FTDI devices:", devices)
    
    connected_dev = len(devices)
    print("detect -",connected_dev,"- Connected FTDI devices:")
    if ((connected_dev < 2) or (connected_dev > 2)):
        print("Please Connected only two FTDI devices:")
        exit(-1)
    # open the first and second devices in the list
    usb_deviceserialA = devices[0]
    usb_deviceserialB = devices[1]
    
    if ((usb_deviceserialA != expected_serialA) and (usb_deviceserialA != expected_serialB)):
        print("Do not detect correct serial number board A",usb_deviceserialA,"Expect- ",expected_serialA)
        exit(-1)
    if ((usb_deviceserialB != expected_serialB) and (usb_deviceserialB != expected_serialA)):
        print("Do not detect correct serial number board B",usb_deviceserialB,"Expect- ",expected_serialB)
        exit(-1)
        
    # setup that the boards will be always A or B
    if (usb_deviceserialA != expected_serialA):
        usb_deviceserialA = expected_serialA
    if (usb_deviceserialB != expected_serialB):
        usb_deviceserialB = expected_serialB
    usb_deviceA = ftd.openEx(usb_deviceserialA) # Defaults to OPEN_BY_SERIAL_NUMBER.
    usb_deviceB = ftd.openEx(expected_serialB) # Defaults to OPEN_BY_SERIAL_NUMBER.
    
    # Reset the devices
    usb_deviceA.resetDevice()
    usb_deviceB.resetDevice()
    print(usb_deviceA.getDeviceInfo())
    print(usb_deviceB.getDeviceInfo())
    async_bitbang_mode = 0x01
    BIT_MASK = 0xFF    # Bit mask for output D0..D7
    usb_deviceA.setBitMode(BIT_MASK, async_bitbang_mode)  # Set pin as output, and 1 =  async bitbang mode
    usb_deviceB.setBitMode(BIT_MASK, async_bitbang_mode)  # Set pin as output, and 1 =  async bitbang mode
    Select_RF_Ports(usb_deviceA,LED_USB_BOARD_ON)
    Select_RF_Ports(usb_deviceB,LED_USB_BOARD_ON)
    return(usb_deviceA,usb_deviceB)
    
    
#----------------------------------------------------------------------------------------------------
def Select_RF_Ports(usb_device,SEL_Pins):
    usb_device.write(bytes([SEL_Pins]))     # Set selected output to high
    time.sleep(delay_rf)


########################## TESTING ##############################################
# Test Programs
###***** maybe add boolens for operating system so when you try and open a device you 
#can do it right for the right OS. Linux cant use indexs to open (?) check linux 
#examples maybe?
def D2XXTest(usb_device):
    # Write a pattern to the pins
    for x in range(5):
        usb_device.write(bytes([LS_pin]))     # Set output high
        time.sleep(0.2)
        usb_device.write(bytes([pattern0]))     # Set output high
        time.sleep(0.2)
        usb_device.write(bytes([V1_pin]))     # Set output high
        time.sleep(0.2)
        usb_device.write(bytes([pattern0]))     # Set output high
        time.sleep(0.2)
        usb_device.write(bytes([V2_pin]))     # Set output high
        time.sleep(0.2)
        usb_device.write(bytes([pattern0]))     # Set output high
        time.sleep(0.2)
        usb_device.write(bytes([V3_pin]))     # Set output high
        time.sleep(0.2)
        usb_device.write(bytes([pattern0]))     # Set output high
        time.sleep(0.2)
        usb_device.write(bytes([V4_pin]))     # Set output high
        time.sleep(0.2)
        usb_device.write(bytes([pattern0]))     # Set output high
        time.sleep(0.2)
#---------------------------------------------------------------------------------
def Test_Switch_RF_Board(usb_device):
    Select_RF_Ports(usb_device,RFC_RF1)
    Select_RF_Ports(usb_device,RFC_RF2)
    Select_RF_Ports(usb_device,RFC_RF3)
    Select_RF_Ports(usb_device,RFC_RF4)
    Select_RF_Ports(usb_device,RFC_RF5)
    Select_RF_Ports(usb_device,RFC_RF6)
    Select_RF_Ports(usb_device,RFC_RF7)
    Select_RF_Ports(usb_device,RFC_RF8)
    Select_RF_Ports(usb_device,RFC_RF9)
    Select_RF_Ports(usb_device,RFC_RF10)
    Select_RF_Ports(usb_device,RFC_RF11)
    Select_RF_Ports(usb_device,RFC_RF12)
    Select_RF_Ports(usb_device,ALL_ISOLATED)
    
#---------------------------------------------------------------------------------- 
def Test_LED (usb_device): 
    for (x) in range (3):
        Select_RF_Ports(usb_device,LED_USB_BOARD_ON)
        time.sleep(0.1)
        Select_RF_Ports(usb_device,LED_USB_BOARD_OFF)
        time.sleep(0.1)
        

#----------------------MAIN--------------------------------------------------------------------------    
if __name__ == '__main__':
    print ("===== Python ftd2xx using driver D2XX Get Device Info Detail =====\n")
    usb_deviceA,usb_deviceB = INIT_USB_BoardS()
    #app = D2XXTest(usb_deviceA)
    #Test_Switch_RF_Board(usb_deviceA)
    #Test_Switch_RF_Board(usb_deviceB)
    
    Test_LED(usb_deviceA)
    Test_LED(usb_deviceB)

    usb_deviceA.close()
    print("@@@@==END==\n")
    winsound.Beep(frequency, duration)


