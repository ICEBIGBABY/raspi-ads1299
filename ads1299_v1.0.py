import spidev
import RPi.GPIO as GPIO
from wiringpi import delay,delayMicroseconds
import datetime

import socket
import json

import multiprocessing
# import numpy as np


class Ads1299:
    PIN_DRDY = 6
    PIN_RST = 13
    # PIN_CLKSEL = 19
    PIN_START = 26
    # PIN_CS = 8

    def __init__(self, PIN_CS=19, spinum=0, ):
        self.PIN_CS = PIN_CS

        self.spi = spidev.SpiDev(0,spinum)
        self.spi.mode = 0b01
        self.spi.max_speed_hz = 3900000

    def global_setup(self):
        delay(50)
        GPIO.setmode(GPIO.BCM)
        GPIO.setup(PIN_DRDY, GPIO.IN)
        GPIO.setup(PIN_RST, GPIO.OUT)
        GPIO.setup(PIN_START, GPIO.OUT)
        # GPIO.setup(PIN_CLKSEL, GPIO.OUT)
        GPIO.setup(self.PIN_CS, GPIO.OUT)

        GPIO.output(PIN_RST, GPIO.HIGH)
        GPIO.output(PIN_START, GPIO.HIGH)
        GPIO.output(self.PIN_CS, GPIO.HIGH)
        # GPIO.output(PIN_CS, GPIO.LOW)

        delay(200)
        GPIO.output(PIN_START, GPIO.LOW)
        delay(14)
        GPIO.output(self.PIN_CS, GPIO.LOW)
        GPIO.output(PIN_RST, GPIO.LOW)
        delay(7)
        GPIO.output(PIN_RST, GPIO.HIGH)

        delayMicroseconds(30)
        spi.writebytes([0x11])
        
        GPIO.output(PIN_RST, GPIO.LOW)
        delayMicroseconds(14)
        GPIO.output(PIN_RST, GPIO.HIGH)


    def initialize(self):
        GPIO.output(self.PIN_CS, GPIO.LOW)
        delayMicroseconds(12)
        spi.writebytes([0x11])
        delayMicroseconds(8)
        spi.writebytes([0x0A])
        delayMicroseconds(12)
        GPIO.output(self.PIN_CS, GPIO.HIGH)

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
        writeReg(0x0F, 0x00)
        writeReg(0x10, 0x00)
        writeReg(0x11, 0x00)
        # 0x12 and 0x13 are read-only Reg
        writeReg(0x14, 0x00)
        writeReg(0x15, 0x20) # enable SRB1
        writeReg(0x16, 0x00)
        writeReg(0x17, 0x00)
    
    def readReg(self, address): 
        GPIO.output(self.PIN_CS, GPIO.LOW)
        spi.writebytes([0x20|address, 0x00])
        temp = spi.xfer([0x00])
        GPIO.output(self.PIN_CS, GPIO.HIGH)
        print('%#x'%temp[0])
    return temp
   
    def writeReg(self, address, value):
        GPIO.output(self.PIN_CS, GPIO.LOW)
        spi.writebytes([0x40|address, 0x00, value])
        GPIO.output(self.PIN_CS, GPIO.HIGH)

    def readAllReg(self):
        address = 0x20
        for i in range(0,24):
            readReg(address)
            address += 1

    def changeToTestSignal(self):
        writeReg(0x02, 0xD0)

        writeReg(0x05, 0x65)
        writeReg(0x06, 0x65)
        writeReg(0x07, 0x65)
        writeReg(0x08, 0x65)
        writeReg(0x09, 0x65)
        writeReg(0x0A, 0x65)
        writeReg(0x0B, 0x65)
        writeReg(0x0C, 0x65)

    def startConv(self):
        GPIO.output(self.PIN_CS, GPIO.LOW)
        spi.writebytes([0x08, 0x10])
        GPIO.output(self.PIN_CS, GPIO.HIGH)

    def stopConv(self):
        GPIO.output(self.PIN_CS, GPIO.LOW)
        spi.writebytes([0x0A, 0x11])
        GPIO.output(self.PIN_CS, GPIO.HIGH)
        
    def receiveOneData(self):
        while 1:
            if GPIO.input(PIN_DRDY)==0:
                break
        
        spirecv = spi.readbytes(27)
        status = (spirecv[0]<<16) + (spirecv[1]<<8) + spirecv[2]

        dec_data = []
        for j in range(1,9):
            dec_data.append( self.hex2dec( (spirecv[3*j]<<16) + (spirecv[3*j+1]<<8) + spirecv[3*j+2] ) )
        return dec_data,status

    def hex2dec(input_data):
        # wierd -    
        if input_data>0x7FFFFF:
            map_data = input_data - 0x1000000
        else:
            map_data = input_data
        output_data = float(map_data * 4.5 / 0x7FFFFF /24)
        return output_data
    
    def receiveData(self, pkglength, datalength, q):
        all_dec_data = []
        all_status = []
        self.startConv()
        GPIO.output(self.PIN_CS, GPIO.LOW)
        for k in range(0, datalength, pkglength)
            time_stamp = str(datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S.%f'))
            for i in range(0,pkglength):
                dec_data,status = self.receiveOneData()
                all_dec_data.append(dec_data)
                all_status.append(status)
            datapool = Datapool()
            datapool.pkgnum = k
            datapool.time_stamp = time_stamp
            datapool.dec_data = all_dec_data
            datapool.status = all_status
            q.put(datapool)
            del datapool
        GPIO.output(self.PIN_CS, GPIO.HIGH)
        self.stopConv()


class Datapool:
    def __init__(self):
        self.pkgnum = 0
        self.dec_data = []
        self.time_stamp = []
        self.status = []


def process_transfer(pkgnum, q):
    print('start sending')
    counter = 0
    while 1:
        if not q.empty():
            value = q.get(True)
            senddata = (json.dumps(value.__dict__)).encode('utf-8')
            print(len(senddata))
            client.send( str(len(senddata)).encode('utf-8') )
            client.send( senddata )

            counter = counter+1
            if counter == pkgnum:
                break




pkgnum = 10
pkglength = 125

chip1 = Ads1299(19, 0)
chip1.global_setup()
chip1.initialize()
chip1.changeToTestSignal()
chip1.readAllReg()

chip2 = Ads1299(19, 1)
chip2.initialize()
chip2.readAllReg()

# client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
# # client.connect( ('127.0.0.1', 8080) )
# # client.connect( ('10.28.215.181', 8080) )
# # client.connect( ('10.28.230.244', 8080) )
# print('connected!')

# p = multiprocessing.Pool()
# q = multiprocessing.Manager().Queue()

# p.apply_async(func=process_transfer, args=(pkgnum, q,) )
# chip1.receiveData(pkglength, datalength=pkgnum*pkglength, q)

# p.close()

# p.join()
# client.close()

GPIO.cleanup()


