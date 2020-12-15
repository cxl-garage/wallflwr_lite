from lora_utils import TTN, TinyLoRa

ttn_config = TTN(devaddr, nwkey, app, country='US')
lora = TinyLoRa(spi, cs, irq, rst, ttn_config)
lora.receive()
