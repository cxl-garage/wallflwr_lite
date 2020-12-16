from lora_utils import TTN, TinyLoRa
import busio
import digitalio
import board
import pandas as pd

# Set Pin Outs
i2c = busio.I2C(board.SCL, board.SDA)
spi = busio.SPI(board.SCK, MOSI=board.MOSI, MISO=board.MISO)
cs  = digitalio.DigitalInOut(board.D27)
rst = digitalio.DigitalInOut(board.D22)
irq = digitalio.DigitalInOut(board.D23) #16
reset = digitalio.DigitalInOut(board.D25)


device_info = pd.read_csv('../_device_info.csv')
devaddr = bytearray.fromhex(device_info['lora_devaddr'][0])
nwkey = bytearray.fromhex(device_info['lora_nwkey'][0])
app   = bytearray.fromhex(device_info['lora_appkey'][0])
ttn_config = TTN(devaddr, nwkey, app, country='US')

lora = TinyLoRa(spi, cs, irq, rst, ttn_config)

while 1:
    lora.receive(keep_listening = False,timeout = 1)
