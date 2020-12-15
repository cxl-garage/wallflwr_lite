# Copyright 2015, 2016 Ideetron B.V.
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU Lesser General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Lesser General Public License for more details.
#
# You should have received a copy of the GNU Lesser General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
#
# Modified by Brent Rubell for Adafruit Industries.
"""
`Adafruit_TinyLoRa`
====================================================
CircuitPython LoRaWAN implementation for use with
The Things Network.
* Author(s): adafruit
Implementation Notes
--------------------
**Hardware:**
* `Adafruit RFM95W LoRa Radio Transceiver Breakout <https://www.adafruit.com/product/3072>`_
**Software and Dependencies:**
* Adafruit CircuitPython firmware for the supported boards:
  https://github.com/adafruit/circuitpython/releases
* Adafruit's Bus Device library: https://github.com/adafruit/Adafruit_CircuitPython_BusDevice
"""

import time
from random import randint
from micropython import const
import adafruit_bus_device.spi_device
from adafruit_tinylora.adafruit_tinylora_encryption import AES

__version__ = "0.0.0-auto.0"
__repo__ = "https://github.com/adafruit/Adafruit_CircuitPython_TinyLoRa.git"

# RFM Module Settings
_MODE_SLEEP = const(0x00)
_MODE_LORA = const(0x80)
_MODE_STDBY = const(0x01)
_MODE_TX = const(0x83)
_TRANSMIT_DIRECTION_UP = const(0x00)
# RFM Registers
_REG_PA_CONFIG = const(0x09)
_REG_PREAMBLE_MSB = const(0x20)
_REG_PREAMBLE_LSB = const(0x21)
_REG_FRF_MSB = const(0x06)
_REG_FRF_MID = const(0x07)
_REG_FRF_LSB = const(0x08)
_REG_FEI_LSB = const(0x1E)
_REG_FEI_MSB = const(0x1D)
_REG_MODEM_CONFIG = const(0x26)
_REG_PAYLOAD_LENGTH = const(0x22)
_REG_FIFO_POINTER = const(0x0D)
_REG_FIFO_BASE_ADDR = const(0x80)
_REG_OPERATING_MODE = const(0x01)
_REG_VERSION = const(0x42)
_REG_PREAMBLE_DETECT = const(0x1F)
_REG_TIMER1_COEF = const(0x39)
_REG_NODE_ADDR = const(0x33)
_REG_IMAGE_CAL = const(0x3B)
_REG_RSSI_CONFIG = const(0x0E)
_REG_RSSI_COLLISION = const(0x0F)
_REG_DIO_MAPPING_1 = const(0x40)

# Freq synth step
_FSTEP = 32000000.0 / 524288


class TTN:
    """TTN Class
    """

    def __init__(self, dev_address, net_key, app_key, country="US"):
        """Interface for TheThingsNetwork
        :param bytearray dev_address: TTN Device Address.
        :param bytearray net_key: TTN Network Key.
        :param bytearray app_key: TTN Application Key.
        :param string country: TTN Region.
        """
        self.dev_addr = dev_address
        self.net_key = net_key
        self.app_key = app_key
        self.region = country

    @property
    def country(self):
        """Returns the TTN Frequency Country.
        """
        return self.region

    @property
    def device_address(self):
        """Returns the TTN Device Address.
        """
        return self.dev_addr

    @property
    def application_key(self):
        """Returns the TTN Application Key.
        """
        return self.app_key

    @property
    def network_key(self):
        """Returns the TTN Network Key.
        """
        return self.net_key

class TinyLoRa:
    """TinyLoRa Interface"""

    # SPI Write Buffer
    _BUFFER = bytearray(2)

    # pylint: disable=too-many-arguments
    def __init__(self, spi, cs, irq, rst, ttn_config, channel=None):
        """Interface for a HopeRF RFM95/6/7/8(w) radio module. Sets module up for sending to
        The Things Network.
        :param ~busio.SPI spi: The SPI bus the device is on
        :param ~digitalio.DigitalInOut cs: Chip select pin (RFM_NSS)
        :param ~digitalio.DigitalInOut irq: RFM's DIO0 Pin (RFM_DIO0)
        :param ~digitalio.DigitalInOut rst: RFM's RST Pin (RFM_RST)
        :param TTN ttn_config: TTN Configuration.
        :param int channel: Frequency Channel.
        """

        # The number of ACK retries before reporting a failure.
        self.ack_retries = 5
        # initialize sequence number counter for reliabe datagram mode
        self.sequence_number = 0

        self._irq = irq
        self._irq.switch_to_input()
        self._cs = cs
        self._cs.switch_to_output()
        self._rst = rst
        self._rst.switch_to_output()
        # Set up SPI Device on Mode 0
        self._device = adafruit_bus_device.spi_device.SPIDevice(
            spi, self._cs, baudrate=4000000, polarity=0, phase=0
        )
        self._rst.value = False
        time.sleep(0.0001)  # 100 us
        self._rst.value = True
        time.sleep(0.005)  # 5 ms
        # Verify the version of the RFM module
        self._version = self._read_u8(_REG_VERSION)
        if self._version != 18:
            raise TypeError("Can not detect LoRa Module. Please check wiring!")
        # Set Frequency registers
        self._rfm_msb = None
        self._rfm_mid = None
        self._rfm_lsb = None
        # Set datarate registers
        self._sf = None
        self._bw = None
        self._modemcfg = None
        self.set_datarate("SF7BW125")
        # Set regional frequency plan
        # pylint: disable=import-outside-toplevel
        if "US" in ttn_config.country:
            from adafruit_tinylora.ttn_usa import TTN_FREQS

            self._frequencies = TTN_FREQS
        elif ttn_config.country == "AS":
            from adafruit_tinylora.ttn_as import TTN_FREQS

            self._frequencies = TTN_FREQS
        elif ttn_config.country == "AU":
            from adafruit_tinylora.ttn_au import TTN_FREQS

            self._frequencies = TTN_FREQS
        elif ttn_config.country == "EU":
            from adafruit_tinylora.ttn_eu import TTN_FREQS

            self._frequencies = TTN_FREQS
        else:
            raise TypeError("Country Code Incorrect/Unsupported")
        # pylint: enable=import-outside-toplevel
        # Set Channel Number
        self._channel = channel
        self._tx_random = randint(0, 7)
        if self._channel is not None:
            # set single channel
            self.set_channel(self._channel)
        # Init FrameCounter
        self.frame_counter = 0
        # Set up RFM9x for LoRa Mode
        for pair in (
            (_REG_OPERATING_MODE, _MODE_SLEEP),
            (_REG_OPERATING_MODE, _MODE_LORA),
            (_REG_PA_CONFIG, 0xFF),
            (_REG_PREAMBLE_DETECT, 0x25),
            (_REG_PREAMBLE_MSB, 0x00),
            (_REG_PREAMBLE_LSB, 0x08),
            (_REG_MODEM_CONFIG, 0x0C),
            (_REG_TIMER1_COEF, 0x34),
            (_REG_NODE_ADDR, 0x27),
            (_REG_IMAGE_CAL, 0x1D),
            (_REG_RSSI_CONFIG, 0x80),
            (_REG_RSSI_COLLISION, 0x00),
        ):
            self._write_u8(pair[0], pair[1])
        # Give the lora object ttn configuration
        self._ttn_config = ttn_config

    def __enter__(self):
        return self

    def __exit__(self, exception_type, exception_value, traceback):
        self.deinit()

    def deinit(self):
        """Deinitializes the TinyLoRa object properties and pins."""
        self._irq = None
        self._rst = None
        self._cs = None
        self.frame_counter = 0
        self._rfm_msb = None
        self._rfm_mid = None
        self._rfm_lsb = None
        self._sf = None
        self._bw = None
        self._modemcfg = None


    ## From RFM69
    def listen(self):
        """Listen for packets to be received by the chip.  Use :py:func:`receive` to listen, wait
           and retrieve packets as they're available.
        """
        # Like RadioHead library, turn off high power boost if enabled.
        if self._tx_power >= 18:
            self._write_u8(_REG_TEST_PA1, _TEST_PA1_NORMAL)
            self._write_u8(_REG_TEST_PA2, _TEST_PA2_NORMAL)
        # Enable payload ready interrupt for D0 line.
        self.dio_0_mapping = 0b01
        # Enter RX mode (will clear FIFO!).
        self.operation_mode = RX_MODE

    def send_data(self, data, data_length, frame_counter, timeout=2):
        """Function to assemble and send data
           :param data: data to send
           :param data_length: length of data to send
           :param frame_counter: frame counter variable, declared in code.py.
           :param timeout: TxDone wait time, default is 2.
        """
        # data packet
        enc_data = bytearray(data_length)
        lora_pkt = bytearray(64)
        # copy bytearray into bytearray for encryption
        enc_data[0:data_length] = data[0:data_length]
        # encrypt data (enc_data is overwritten in this function)
        self.frame_counter = frame_counter
        aes = AES(
            self._ttn_config.device_address,
            self._ttn_config.app_key,
            self._ttn_config.network_key,
            self.frame_counter,
        )
        enc_data = aes.encrypt(enc_data)
        # append preamble to packet
        lora_pkt[0] = const(_REG_DIO_MAPPING_1)
        lora_pkt[1] = self._ttn_config.device_address[3]
        lora_pkt[2] = self._ttn_config.device_address[2]
        lora_pkt[3] = self._ttn_config.device_address[1]
        lora_pkt[4] = self._ttn_config.device_address[0]
        lora_pkt[5] = 0
        lora_pkt[6] = frame_counter & 0x00FF
        lora_pkt[7] = (frame_counter >> 8) & 0x00FF
        lora_pkt[8] = 0x01
        # set length of LoRa packet
        lora_pkt_len = 9
        # load encrypted data into lora_pkt
        lora_pkt[lora_pkt_len : lora_pkt_len + data_length] = enc_data[0:data_length]
        # recalculate packet length
        lora_pkt_len += data_length
        # Calculate MIC
        mic = bytearray(4)
        mic = aes.calculate_mic(lora_pkt, lora_pkt_len, mic)
        # load mic in package
        lora_pkt[lora_pkt_len : lora_pkt_len + 4] = mic[0:4]
        # recalculate packet length (add MIC length)
        lora_pkt_len += 4
        self.send_packet(lora_pkt, lora_pkt_len, timeout)

    def send_packet(self, lora_packet, packet_length, timeout):
        """Sends a LoRa packet using the RFM Module
          :param bytearray lora_packet: assembled LoRa packet from send_data
          :param int packet_length: length of LoRa packet to send
          :param int timeout: TxDone wait time.
        """
        # Set RFM to standby
        self._write_u8(_MODE_STDBY, 0x81)
        # wait for RFM to enter standby mode
        time.sleep(0.01)
        # switch interrupt to txdone
        self._write_u8(0x40, 0x40)
        # check for multi-channel configuration
        if self._channel is None:
            self._tx_random = randint(0, 7)
            self._rfm_lsb = self._frequencies[self._tx_random][2]
            self._rfm_mid = self._frequencies[self._tx_random][1]
            self._rfm_msb = self._frequencies[self._tx_random][0]
        # Set up frequency registers
        for pair in (
            (_REG_FRF_MSB, self._rfm_msb),
            (_REG_FRF_MID, self._rfm_mid),
            (_REG_FRF_LSB, self._rfm_lsb),
            (_REG_FEI_LSB, self._sf),
            (_REG_FEI_MSB, self._bw),
            (_REG_MODEM_CONFIG, self._modemcfg),
            (_REG_PAYLOAD_LENGTH, packet_length),
            (_REG_FIFO_POINTER, _REG_FIFO_BASE_ADDR),
        ):
            self._write_u8(pair[0], pair[1])
        # fill the FIFO buffer with the LoRa payload
        for k in range(packet_length):
            self._write_u8(0x00, lora_packet[k])
        # switch RFM to TX operating mode
        self._write_u8(_REG_OPERATING_MODE, _MODE_TX)
        # wait for TxDone IRQ, poll for timeout.
        start = time.monotonic()
        timed_out = False
        while not timed_out and not self._irq.value:
            if (time.monotonic() - start) >= timeout:
                timed_out = True
        # switch RFM to sleep operating mode
        self._write_u8(_REG_OPERATING_MODE, _MODE_SLEEP)
        if timed_out:
            raise RuntimeError("Timeout during packet send")

    ## From RFM69

    def send_with_ack(self, data):
        """Reliable Datagram mode:
           Send a packet with data and wait for an ACK response.
           The packet header is automatically generated.
           If enabled, the packet transmission will be retried on failure
        """
        if self.ack_retries:
            retries_remaining = self.ack_retries
        else:
            retries_remaining = 1
        got_ack = False
        self.sequence_number = (self.sequence_number + 1) & 0xFF
        while not got_ack and retries_remaining:
            self.identifier = self.sequence_number
            self.send(data, keep_listening=True)
            # Don't look for ACK from Broadcast message
            if self.destination == _RH_BROADCAST_ADDRESS:
                got_ack = True
            else:
                # wait for a packet from our destination
                ack_packet = self.receive(timeout=self.ack_wait, with_header=True)
                if ack_packet is not None:
                    if ack_packet[3] & _RH_FLAGS_ACK:
                        # check the ID
                        if ack_packet[2] == self.identifier:
                            got_ack = True
                            break
            # pause before next retry -- random delay
            if not got_ack:
                # delay by random amount before next try
                time.sleep(self.ack_wait + self.ack_wait * random.random())
            retries_remaining = retries_remaining - 1
            # set retry flag in packet header
            self.flags |= _RH_FLAGS_RETRY
        self.flags = 0  # clear flags
        return got_ack

    ## From RFM69
    def receive(self, *, keep_listening=True, with_ack=False, timeout=None, with_header=False):
        """Wait to receive a packet from the receiver. If a packet is found the payload bytes
           are returned, otherwise None is returned (which indicates the timeout elapsed with no
           reception).
           If keep_listening is True (the default) the chip will immediately enter listening mode
           after reception of a packet, otherwise it will fall back to idle mode and ignore any
           future reception.
           All packets must have a 4 byte header for compatibilty with the
           RadioHead library.
           The header consists of 4 bytes (To,From,ID,Flags). The default setting will  strip
           the header before returning the packet to the caller.
           If with_header is True then the 4 byte header will be returned with the packet.
           The payload then begins at packet[4].
           If with_ack is True, send an ACK after receipt (Reliable Datagram mode)
        """
        timed_out = False
        if timeout is None:
            timeout = self.receive_timeout
        if timeout is not None:
            # Wait for the payload_ready signal.  This is not ideal and will
            # surely miss or overflow the FIFO when packets aren't read fast
            # enough, however it's the best that can be done from Python without
            # interrupt supports.
            # Make sure we are listening for packets.
            self.listen()
            start = time.monotonic()
            timed_out = False
            while not timed_out and not self.payload_ready():
                if (time.monotonic() - start) >= timeout:
                    timed_out = True
        # Payload ready is set, a packet is in the FIFO.
        packet = None
        # save last RSSI reading
        self.last_rssi = self.rssi
        # Enter idle mode to stop receiving other packets.
        self.idle()
        if not timed_out:
            # Read the length of the FIFO.
            fifo_length = self._read_u8(_REG_FIFO)
            # Handle if the received packet is too small to include the 4 byte
            # RadioHead header and at least one byte of data --reject this packet and ignore it.
            if fifo_length > 0:  # read and clear the FIFO if anything in it
                packet = bytearray(fifo_length)
                self._read_into(_REG_FIFO, packet, fifo_length)

            if fifo_length < 5:
                packet = None
            else:
                if (
                    self.node != _RH_BROADCAST_ADDRESS
                    and packet[0] != _RH_BROADCAST_ADDRESS
                    and packet[0] != self.node
                ):
                    packet = None
                # send ACK unless this was an ACK or a broadcast
                elif (
                    with_ack
                    and ((packet[3] & _RH_FLAGS_ACK) == 0)
                    and (packet[0] != _RH_BROADCAST_ADDRESS)
                ):
                    # delay before sending Ack to give receiver a chance to get ready
                    if self.ack_delay is not None:
                        time.sleep(self.ack_delay)
                    # send ACK packet to sender (data is b'!')
                    self.send(
                        b"!",
                        destination=packet[1],
                        node=packet[0],
                        identifier=packet[2],
                        flags=(packet[3] | _RH_FLAGS_ACK),
                    )
                    # reject Retries if we have seen this idetifier from this source before
                    if (self.seen_ids[packet[1]] == packet[2]) and (
                        packet[3] & _RH_FLAGS_RETRY
                    ):
                        packet = None
                    else:  # save the packet identifier for this source
                        self.seen_ids[packet[1]] = packet[2]
                if (
                    not with_header and packet is not None
                ):  # skip the header if not wanted
                    packet = packet[4:]
        # Listen again if necessary and return the result packet.
        if keep_listening:
            self.listen()
        else:
            # Enter idle mode to stop receiving other packets.
            self.idle()
        return packet

    def set_datarate(self, datarate):
        """Sets the RFM Datarate
        :param datarate: Bandwidth and Frequency Plan
        """
        data_rates = {
            "SF7BW125": (0x74, 0x72, 0x04),
            "SF7BW250": (0x74, 0x82, 0x04),
            "SF8BW125": (0x84, 0x72, 0x04),
            "SF9BW125": (0x94, 0x72, 0x04),
            "SF10BW125": (0xA4, 0x72, 0x04),
            "SF11BW125": (0xB4, 0x72, 0x0C),
            "SF12BW125": (0xC4, 0x72, 0x0C),
        }
        try:
            self._sf, self._bw, self._modemcfg = data_rates[datarate]
        except KeyError:
            raise KeyError("Invalid or Unsupported Datarate.")

    def set_channel(self, channel):
        """Sets the RFM Channel (if single-channel)
        :param int channel: Transmit Channel (0 through 7).
        """
        self._rfm_msb, self._rfm_mid, self._rfm_lsb = self._frequencies[channel]

    def _read_into(self, address, buf, length=None):
        """Read a number of bytes from the specified address into the
        provided buffer. If length is not specified (default) the entire buffer
        will be filled.
        :param bytearray address: Register Address.
        :param bytearray buf: Data Buffer for bytes.
        :param int length: Buffer length.
        """
        if length is None:
            length = len(buf)
        with self._device as device:
            # Strip out top bit to set 0 value (read).
            self._BUFFER[0] = address & 0x7F
            # pylint: disable=no-member
            device.write(self._BUFFER, end=1)
            device.readinto(buf, end=length)

    def _read_u8(self, address):
        """Read a single byte from the provided address and return it.
        :param bytearray address: Register Address.
        """
        self._read_into(address, self._BUFFER, length=1)
        return self._BUFFER[0]

    def _write_u8(self, address, val):
        """Writes to the RFM register given an address and data.
        :param bytearray address: Register Address.
        :param val: Data to write.
        """
        with self._device as device:
            self._BUFFER[0] = address | 0x80  # MSB 1 to Write
            self._BUFFER[1] = val
            # pylint: disable=no-member
            device.write(self._BUFFER, end=2)
