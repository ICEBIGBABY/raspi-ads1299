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

PIN_DRDY = 6
PIN_RST = 13
PIN_CLKSEL = 19
PIN_START = 26
PIN_CS = 8


class Datapool:
    def __init__(self):
        self.pkgnum = 0
        self.dec_data = []
        self.time_stamp = []
        self.status = []
    def clear(self):
        self.dec_data = []
        self.time_stamp = []
        self.status = []


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
    writeReg(0x01, sample_rate)
    
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
    writeReg(0x0F, 0x00)
    writeReg(0x10, 0x00)
    writeReg(0x11, 0x00)
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
    spi.writebytes([0x08])

def stopConv():
    spi.writebytes([0x0A])

def receiveData(datapool, datalength):
    datapool.time_stamp.append(str(datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S.%f')))
    # counter=0
 
    for i in range(0,datalength):
        while 1:
            if GPIO.input(PIN_DRDY)==0:
                break
        spi.writebytes([0x12])
        temp = spi.readbytes(27)
    
        # a = [temp[3], temp[6], temp[9], temp[12], temp[15], temp[18], temp[21], temp[24] ]
        # if len( list( set( a )))!=1:
        #     print('No.',i)
        #     print('value is: ', temp)
            # counter=counter+1
        #     continue

        datapool.status.append( (temp[0]<<16) + (temp[1]<<8) + temp[2] )
        dataConvert(datapool, temp[3:27] )

    # newdatapool.dec_data = copy.deepcopy(datapool.dec_data)
    # checkData(datapool)
    # print('Counter', counter)
    
    # return datapool


def dataConvert(datapool,hex_data):
    temp = []
    # data = []
    for j in range(0,8):
        # data.append(  (hex_data[3*j]<<16) + (hex_data[3*j+1]<<8) + hex_data[3*j+2] ) 
        temp.append( hex2dec( (hex_data[3*j]<<16) + (hex_data[3*j+1]<<8) + hex_data[3*j+2] ) )
    # print(data)
    datapool.dec_data.append(temp)

def hex2dec(input_data):
    input_data = int(input_data)
    if input_data>0x7FFFFF:
        output_data = ((~input_data & (0x007FFFFF))+1)
        output_data = float(output_data * (-4.5) / 0x7FFFFF /24)
        # map_data = input_data - 0x1000000
    else:
        # map_data = input_data
        output_data = float(input_data * 4.5 / 0x7FFFFF /24)
    return output_data

def process_receive(q):
    # time_s = 10
    # for i in range(0,25*time_s):
    # i=0
    startConv()
    # while 1:
    for i in range(0,pkg_num):
        datapool = Datapool()
        datapool.pkgnum = i
        # i = i+1
        # print('receive')
        receiveData(datapool,pkg_length) # 40ms one pkg
        # print(datapool.dec_data)
        q.put(datapool)

        # senddata = (json.dumps(datapool.__dict__)).encode('utf-8')
        # print(len(senddata))
        # client.send( str(len(senddata)).encode('utf-8') )
        # client.send( senddata )

    stopConv()


def process_transfer(q):
    counter=0
    # time_s = 10
    print('start sending')
    all_data= []
    all_time_stamp = []
    while 1:
        if not q.empty():
            value = q.get(True)
            print(value.time_stamp)
            senddata = (json.dumps(value.__dict__)).encode('utf-8')
            # print(len(senddata))
            client.send( str(len(senddata)).encode('utf-8') )
            # print('1')
            client.send( senddata )
            print('sent')

            all_data.extend(value.dec_data)
            all_time_stamp.extend(value.time_stamp)
            counter = counter+1
        if counter == pkg_num:
            break
    print('done!')
    sio.savemat('4kheart.mat', mdict={'data': all_data, 'time_stamp': all_time_stamp})


client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
client.connect( ('10.28.251.182', 8080) )
# client.connect( ('127.0.0.1', 8080) )
# client.connect( ('10.28.254.184', 8080) )
print('connected!')
sample_rate = 0x96
pkg_length=125
pkg_num=2*60

if __name__ == '__main__':
    setup()
    initialize()
    readAllReg()
    # changeToTestSignal()

    p = multiprocessing.Pool()
    q = multiprocessing.Manager().Queue()


    # startConv()
    # # process_receive()
    # p1 = multiprocessing.Process(target=process_receive, args=(q,) )
    # p2 = multiprocessing.Process(target=process_transfer, args=(q,) )

    p.apply_async(func=process_receive, args=(q,) )
    p.apply_async(func=process_transfer, args=(q,) )


    p.close()


    p.join()
    GPIO.cleanup()

    # client.close()
    # p2.join()

