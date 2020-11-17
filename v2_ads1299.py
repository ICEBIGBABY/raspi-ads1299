import spidev
import RPi.GPIO as GPIO
import time
from wiringpi import delay,delayMicroseconds
import threading
import scipy.io as sio
import datetime

PIN_DRDY = 6
PIN_RST = 13
PIN_CLKSEL = 19
PIN_START = 26
PIN_CS = 8

class Datapool:
    def __init__(self, name):
        self.name = name
        self.hex_data = []
        self.dec_data = []
        self.time_stamp = []
        self.status = []
        self.issaved = True
        self.isempty = True


datapool1 = Datapool('pool1')
datapool2 = Datapool('pool2')


spi = spidev.SpiDev()

def setup():
    # spi = spidev.SpiDev()
    spi.open(0,0)
    spi.max_speed_hz = 7800000 # 15600000   
    #spi.max_speed_hz = 3900000    
    #spi.max_speed_hz = 1953000
    spi.mode = 0b01
    #spi.cshigh = False
    spi.max_speed_hz = 3900000

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
    writeReg(0x01, 0x92)
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

def startConv():
    spi.writebytes([0x08, 0x10])

def stopConv():
    spi.writebytes([0x0A, 0x11])

def receiveData(datapool):
    #while 1:
    
    datapool.time_stamp.append(str(datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S.%f')))
    #print(id(datapool))
    for i in range(0,160):
        while 1:
            if GPIO.input(PIN_DRDY)==0:
                break
        #temp = spi.xfer([0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00]) 
        #temp = spi.xfer([0x000000, 0x000000, 0x000000, 0x000000, 0x000000, 0x000000, 0x000000, 0x000000, 0x000000]) 
        temp = spi.readbytes(27)
        #datapool.time_stamp.append(str(datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S.%f')))
        datapool.hex_data.append(temp) 
    #return temp

def dataConvert(datapool):
    for i in range(0,len(datapool.hex_data)):
        temp = []
        for j in range(0,9):
            if j==0:
                datapool.status.append( (datapool.hex_data[i][j]<<16) + (datapool.hex_data[i][j+1]<<8) + datapool.hex_data[i][j+2] )
            elif 0<j<9:
                #print((data_pool[i][3*j]<<16) + (data_pool[i][3*j+1]<<8) + data_pool[i][3*j+2] )
                #print( hex2dec( (data_pool[i][3*j]<<16) + (data_pool[i][3*j+1]<<8) + data_pool[i][3*j+2] ) )
                temp.append( hex2dec( (datapool.hex_data[i][3*j]<<16) + (datapool.hex_data[i][3*j+1]<<8) + datapool.hex_data[i][3*j+2] ) )
             #elif j==9:
             #   temp.append(data_pool[i][27])
        datapool.dec_data.append(temp)

def hex2dec(input_data):
    # wierd -    
    if input_data>0x7FFFFF:
        output_data = ((~input_data) +1)
        #print(output_data)
        output_data = float(output_data * (4.5) / 0x7FFFFF /24)
        #print(output_data)
    else:
        output_data = float(input_data * 4.5 / 0x7FFFFF /24)
    #output_data = float(output_data * 4.5 / 0x7FFFFF /24)
    return output_data

def saveData(datapool):
    sio.savemat(str(datetime.datetime.now())+'.mat', mdict={'status':datapool.status, 'data': datapool.dec_data, 'time_stamp': datapool.time_stamp})


def thread1():
    counter = 0
    data_pkg_number = 25
    #for k in range(0,25):
    while 1:
        if datapool1.isempty==True & datapool1.issaved==True:
            receiveData(datapool1)
            print(len(datapool1.hex_data))
            print(len(datapool2.hex_data))
            datapool1.isempty = False
            datapool1.issaved = False
            counter+=1
            print('1 received')
        elif datapool2.isempty==True & datapool2.issaved==True:
            receiveData(datapool2)
            print(len(datapool1.hex_data))
            print(len(datapool2.hex_data))
            datapool2.isempty = False
            datapool2.issaved = False
            counter+=1
            print('2 received')
        else:
            print('wait for saving data!')
        
        print(len(datapool1.hex_data))
        print(len(datapool2.hex_data))
        if counter==data_pkg_number:
            break

         
def thread2():
    #for k in range(0,5):
    counter = 0
    data_pkg_number = 25
    while 1:
        if datapool1.isempty==False & datapool1.issaved==False:
            #dataConvert(datapool1)
            #saveData(datapool1)
            datapool1.hex_data = []
            datapool1.dec_data = []
            datapool1.status = []
            datapool1.time_stamp = []

            datapool1.isempty = True
            datapool1.issaved = True
            counter+=1
            print('1 saved')
        elif datapool2.isempty==False & datapool2.issaved==False:
            #dataConvert(datapool2)
            #saveData(datapool2)
            datapool2.hex_data = []
            datapool2.dec_data = []
            datapool2.status = []
            datapool2.time_stamp = []
            datapool2.isempty = True
            datapool2.issaved = True
            print('2 saved')
            counter+=1

        if counter==data_pkg_number:
            break
        #else:
            #print('wait for receiving data!')

if __name__ == '__main__':
    #spi = spidev.SpiDev()
    setup()
    initialize()
    #writeReg(0x05, 0x60)
    readAllReg()
    startConv()

    t1 = threading.Thread(target=thread1, args=())
    t2 = threading.Thread(target=thread2, args=()) 
    t1.start()
    t2.start()
    #thread1()

    while 1:
        if t1.isAlive()==False & t2.isAlive()==False: 
        #if t2.isAlive()==False: 
            stopConv()
            GPIO.cleanup()
            break
