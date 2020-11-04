import spidev
import time

spi = spidev.SpiDev()
spi.open(0,0)
spi.max_speed_hz = 3900000

spi.mode = 0b01
#spi.lsbfirst

to_send = [0x01, 0x02, 0x03]


#while 1:
for i in range(0,10):
    spi.xfer([0x01, 0x02, 0x03])
    #spi.writebytes(to_send)
    time.sleep(0.1)

