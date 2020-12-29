import spidev
import RPi.GPIO as GPIO
from wiringpi import delay,delayMicroseconds
import datetime

import socket
import json

import multiprocessing
import scipy.io as sio

import numpy as np
import copy

import _thread
import matplotlib.pyplot as plt

PIN_DRDY = 6
PIN_RST = 13
PIN_CLKSEL = 19
PIN_START = 26
PIN_CS = 8

channel = [ [] for i in range(8) ]


spi = spidev.SpiDev()

def setup():
    # spi = spidev.SpiDev()
    spi.open(0,0)
    # spi.max_speed_hz = 15600000   
    # spi.max_speed_hz = 7800000
    spi.max_speed_hz = 3900000
    # spi.max_speed_hz = 1953000
    spi.mode = 0b01
    #spi.cshigh = False

    delay(50)
    GPIO.setmode(GPIO.BCM)
    GPIO.setup(PIN_DRDY, GPIO.IN)
    GPIO.setup(PIN_RST, GPIO.OUT)
    GPIO.setup(PIN_START, GPIO.OUT)
    GPIO.setup(PIN_CLKSEL, GPIO.OUT)
    GPIO.setup(PIN_CS, GPIO.OUT)

    GPIO.output(PIN_RST, GPIO.HIGH)
    GPIO.output(PIN_START, GPIO.HIGH)
    GPIO.output(PIN_CLKSEL, GPIO.HIGH)
    GPIO.output(PIN_CS, GPIO.LOW)

    delay(200)
    GPIO.output(PIN_START, GPIO.LOW)
    delay(14)
    GPIO.output(PIN_CLKSEL, GPIO.LOW)
    GPIO.output(PIN_RST, GPIO.LOW)
    delay(7)
    GPIO.output(PIN_RST, GPIO.HIGH)

    delayMicroseconds(30)
    spi.writebytes([0x11])
    
    GPIO.output(PIN_RST, GPIO.LOW)
    delayMicroseconds(14)
    GPIO.output(PIN_RST, GPIO.HIGH)

    delayMicroseconds(12)
    spi.writebytes([0x11])
    delayMicroseconds(8)
    spi.writebytes([0x0A])
    delayMicroseconds(12)

def initialize():
    #writeReg(0x01, 0x92)
    writeReg(0x01, 0x96)
    
    writeReg(0x02, 0xC0)
    writeReg(0x03, 0xE0)
    writeReg(0x04, 0x00)

    writeReg(0x05, 0x60)
    writeReg(0x06, 0x60)
    writeReg(0x07, 0x60)
    writeReg(0x08, 0x60)
    writeReg(0x09, 0x60)
    writeReg(0x0A, 0x60)
    writeReg(0x0B, 0x60)
    writeReg(0x0C, 0x60)

    writeReg(0x0D, 0x00)
    writeReg(0x0E, 0x00)
    writeReg(0x0F, 0xFF) # FF 00
    writeReg(0x10, 0xFF)
    writeReg(0x11, 0xFF)
    # 0x12 and 0x13 are read-only Reg
    writeReg(0x14, 0x00)
    writeReg(0x15, 0x20) # enable SRB1
    writeReg(0x16, 0x00)
    writeReg(0x17, 0x00)

def readReg(address): 
    spi.writebytes([0x20|address, 0x00])
    temp = spi.xfer([0x00])
    print('%#x'%temp[0])
    return temp
   
def writeReg(address, value):
    spi.writebytes([0x40|address, 0x00, value])

def readAllReg():
    address = 0x20
    for i in range(0,24):
        readReg(address)
        address += 1

def changeToTestSignal():
    writeReg(0x02, 0xD0)

    writeReg(0x05, 0x65)
    writeReg(0x06, 0x65)
    writeReg(0x07, 0x65)
    writeReg(0x08, 0x65)
    writeReg(0x09, 0x65)
    writeReg(0x0A, 0x65)
    writeReg(0x0B, 0x65)
    writeReg(0x0C, 0x65)

def startConv():
    spi.writebytes([0x08, 0x10])

def stopConv():
    spi.writebytes([0x0A, 0x11])


def dataconvert(input_data):
    input_data = int(input_data)
    if input_data>0x7FFFFF:
        output_data = (~(input_data) & 0x007FFFFF ) + 1
        output_data = float(output_data * (-4.5) / 0x7FFFFF /24)
    else:
        output_data = float(input_data * 4.5 / 0x7FFFFF /24)
    return output_data


def process_receive():
    # time_s = 10
    # for i in range(0,25*time_s):
    startConv()
    # while 1:
    for i in range(0,250*60):
        while 1:
            if GPIO.input(PIN_DRDY)==0:
                break
        temp = spi.readbytes(27)
        data = []
        for j in range(1,9):
            data.append(  (temp[3*j]<<16) + (temp[3*j+1]<<8) + temp[3*j+2] ) 
            real = dataconvert((temp[3*j]<<16) + (temp[3*j+1]<<8) + temp[3*j+2] )
            channel[j-1].append(real)
        print(data)
    stopConv()



if __name__ == '__main__':
    setup()
    initialize()
    readAllReg()
    # changeToTestSignal()
    _thread.start_new_thread(process_receive, ())

    while 1:
        for i in range(len(channel)):
            if len(channel[0]) >=1000:
                plt.subplot(2,1,1)
                plt.plot(channel[0][-1000:])
                plt.subplot(2,1,2)
                plt.plot(channel[1][-1000:])
                # plt.subplot(8,1,3)
                # plt.plot(channel[2][-1000:])
                # plt.subplot(8,1,4)
                # plt.plot(channel[3][-1000:])
                # plt.subplot(8,1,5)
                # plt.plot(channel[4][-1000:])

                plt.pause(1)
                plt.clf()


    process_receive()
    sio.savemat('1209data.mat', mdict={'data1209': channel})

    GPIO.cleanup()


