#! /usr/bin/env micropython

# Micropython driver for the DS3231 RTC Module

# Inspiration from work done by Mike Causer (mcauser) for the DS1307
# https://github.com/mcauser/micropython-tinyrtc-i2c/blob/master/ds1307.py

# The MIT License (MIT)
#
# Copyright (c) 2020 Willem Peterse
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in
# all copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN
# THE SOFTWARE.

from micropython import const

DATETIME_REG    = const(0) # 7 bytes
ALARM1_REG      = const(7) # 5 bytes
ALARM2_REG      = const(11) # 4 bytes
CONTROL_REG     = const(14)
STATUS_REG      = const(15)
AGING_REG       = const(16)
TEMPERATURE_REG = const(17) # 2 bytes


def dectobcd(decimal):

    return (decimal // 10) << 4 | (decimal % 10)

def bcdtodec(bcd):

    return ((bcd >> 4) * 10) + (bcd & 0x0F)


class DS3231:

    FREQ_1      = const(1)
    FREQ_1024   = const(2)
    FREQ_4096   = const(3)
    FREQ_8192   = const(4)
    SQW_32K     = const(1)

    AL1_EVERY_S     = const(15) # Alarm every second
    AL1_MATCH_S     = const(14) # Alarm when seconds match (every minute)
    AL1_MATCH_MS    = const(12) # Alarm when minutes, seconds match (every hour)
    AL1_MATCH_HMS   = const(8) # Alarm when hours, minutes, seconds match (every day)
    AL1_MATCH_DHMS  = const(0) # Alarm when day|wday, hour, min, sec match (specific wday / mday) (once per month/week)

    AL2_EVERY_M     = const(7) # Alarm every minute on 00 seconds
    AL2_MATCH_M     = const(6) # Alarm when minutes match (every hour)
    AL2_MATCH_HM    = const(4) # Alarm when hours and minutes match (every day)
    AL2_MATCH_DHM   = const(0) # Alarm when day|wday match (once per month/week)

    def __init__(self, i2c, addr=0x68):
        self.i2c = i2c
        self.addr = addr
        self._timebuf = bytearray(7) # Pre-allocate a buffer for the time data
        self._buf = bytearray(1) # Pre-allocate a single bytearray for re-use
        self._al1_buf = bytearray(4)
        self._al2buf = bytearray(3)

    def datetime(self, datetime=None):

        if datetime is None:
            self.i2c.readfrom_mem_into(self.addr, DATETIME_REG, self._timebuf)
            # 0x00 - Seconds    BCD
            # 0x01 - Minutes    BCD
            # 0x02 - Hour       0 12/24 AM/PM/20s BCD
            # 0x03 - WDay 1-7   0000 0 BCD
            # 0x04 - Day 1-31   00 BCD
            # 0x05 - Month 1-12 Century 00 BCD
            # 0x06 - Year 0-99  BCD (2000-2099)
            seconds = bcdtodec(self._timebuf[0])
            minutes = bcdtodec(self._timebuf[1])

            if (self._timebuf[2] & 0x40) >> 6: # Check for 12 hour mode bit
                hour = bcdtodec(self._timebuf[2] & 0x9f) # Mask out bit 6(12/24) and 5(AM/PM)
                if (self._timebuf[2] & 0x20) >> 5: # bit 5(AM/PM)
                    # PM
                    hour += 12
            else:
                # 24h mode
                hour = bcdtodec(self._timebuf[2] & 0xbf) # Mask bit 6 (12/24 format)

            weekday = bcdtodec(self._timebuf[3]) # Can be set arbitrarily by user (1,7)
            day = bcdtodec(self._timebuf[4])
            month = bcdtodec(self._timebuf[5] & 0x7f) # Mask out the century bit
            year = bcdtodec(self._timebuf[6]) + 2000

            if self.OSF():
                print("WARNING: Oscillator stop flag set. Time may not be accurate.")

            return (year, month, day, weekday, hour, minutes, seconds, 0) # Conforms to the ESP8266 RTC (v1.13)

        # Set the clock
        try:
            self._timebuf[3] = dectobcd(datetime[6]) # Day of week
        except IndexError:
            self._timebuf[3] = 0
        try:
            self._timebuf[0] = dectobcd(datetime[5]) # Seconds
        except IndexError:
            self._timebuf[0] = 0
        self._timebuf[1] = dectobcd(datetime[4]) # Minutes
        self._timebuf[2] = dectobcd(datetime[3]) # Hour + the 24h format flag
        self._timebuf[4] = dectobcd(datetime[2]) # Day
        self._timebuf[5] = dectobcd(datetime[1]) & 0xff # Month + mask the century flag
        self._timebuf[6] = dectobcd(int(str(datetime[0])[-2:])) # Year can be yyyy, or yy
        self.i2c.writeto_mem(self.addr, DATETIME_REG, self._timebuf)
        self._OSF_reset()
        return True

    def square_wave(self, freq=None):

        if freq is None:
            return self.i2c.readfrom_mem(self.addr, CONTROL_REG, 1)[0]

        if not freq:
            # Set INTCN (bit 2) to 1 and both ALIE (bits 1 & 0) to 0
            self.i2c.readfrom_mem_into(self.addr, CONTROL_REG, self._buf)
            self.i2c.writeto_mem(self.addr, CONTROL_REG, bytearray([(self._buf[0] & 0xf8) | 0x04]))
        else:
            # Set the frequency in the control reg and at the same time set the INTCN to 0
            freq -= 1
            self.i2c.readfrom_mem_into(self.addr, CONTROL_REG, self._buf)
            self.i2c.writeto_mem(self.addr, CONTROL_REG, bytearray([(self._buf[0] & 0xe3) | (freq << 3)]))
        return True

    def alarm1(self, time=None, match=AL1_MATCH_DHMS, int_en=True, weekday=False):

        if time is None:
            # TODO Return readable string
            self.i2c.readfrom_mem_into(self.addr, ALARM1_REG, self._al1_buf)
            return self._al1_buf

        if isinstance(time, int):
            time = (time,)

        a1m4 = (match & 0x08) << 4
        a1m3 = (match & 0x04) << 5
        a1m2 = (match & 0x02) << 6
        a1m1 = (match & 0x01) << 7

        dydt = (1 << 6) if weekday else 0 # day / date bit

        self._al1_buf[0] = dectobcd(time[0]) | a1m1 # second
        self._al1_buf[1] = (dectobcd(time[1]) | a1m2) if len(time) > 1 else a1m2 # minute
        self._al1_buf[2] = (dectobcd(time[2]) | a1m3) if len(time) > 2 else a1m3 # hour
        self._al1_buf[3] = (dectobcd(time[3]) | a1m4 | dydt) if len(time) > 3 else a1m4 | dydt # day (wday|mday)

        self.i2c.writeto_mem(self.addr, ALARM1_REG, self._al1_buf)

        # Set the interrupt bit
        self.alarm_int(enable=int_en, alarm=1)

        # Check the alarm (will reset the alarm flag)
        self.check_alarm(1)

        return self._al1_buf

    def alarm2(self, time=None, match=AL2_MATCH_DHM, int_en=True, weekday=False):

        if time is None:
            # TODO Return readable string
            self.i2c.readfrom_mem_into(self.addr, ALARM2_REG, self._al2buf)
            return self._al2buf

        if isinstance(time, int):
            time = (time,)

        a2m4 = (match & 0x04) << 5 # masks
        a2m3 = (match & 0x02) << 6
        a2m2 = (match & 0x01) << 7

        dydt = (1 << 6) if weekday else 0 # day / date bit

        self._al2buf[0] = dectobcd(time[0]) | a2m2 if len(time) > 1 else a2m2 # minute
        self._al2buf[1] = dectobcd(time[1]) | a2m3 if len(time) > 2 else a2m3 # hour
        self._al2buf[2] = dectobcd(time[2]) | a2m4 | dydt if len(time) > 3 else a2m4 | dydt # day

        self.i2c.writeto_mem(self.addr, ALARM2_REG, self._al2buf)

        # Set the interrupt bits
        self.alarm_int(enable=int_en, alarm=2)

        # Check the alarm (will reset the alarm flag)
        self.check_alarm(2)

        return self._al2buf

    def alarm_int(self, enable=True, alarm=0):

        if alarm in (0, 1):
            self.i2c.readfrom_mem_into(self.addr, CONTROL_REG, self._buf)
            if enable:
                self.i2c.writeto_mem(self.addr, CONTROL_REG, bytearray([(self._buf[0] & 0xfa) | 0x05]))
            else:
                self.i2c.writeto_mem(self.addr, CONTROL_REG, bytearray([self._buf[0] & 0xfe]))

        if alarm in (0, 2):
            self.i2c.readfrom_mem_into(self.addr, CONTROL_REG, self._buf)
            if enable:
                self.i2c.writeto_mem(self.addr, CONTROL_REG, bytearray([(self._buf[0] & 0xf9) | 0x06]))
            else:
                self.i2c.writeto_mem(self.addr, CONTROL_REG, bytearray([self._buf[0] & 0xfd]))

        return self.i2c.readfrom_mem(self.addr, CONTROL_REG, 1)

    def check_alarm(self, alarm):

        self.i2c.readfrom_mem_into(self.addr, STATUS_REG, self._buf)
        if (self._buf[0] & alarm) == 0:
            # Alarm flag not set
            return False

        # Clear alarm flag bit
        self.i2c.writeto_mem(self.addr, STATUS_REG, bytearray([self._buf[0] & ~alarm]))
        return True

    def output_32kHz(self, enable=True):

        status = self.i2c.readfrom_mem(self.addr, STATUS_REG, 1)[0]
        if enable:
            self.i2c.writeto_mem(self.addr, STATUS_REG, bytearray([status | (1 << 3)]))
        else:
            self.i2c.writeto_mem(self.addr, STATUS_REG, bytearray([status & (~(1 << 3))]))

    def OSF(self):

        return bool(self.i2c.readfrom_mem(self.addr, STATUS_REG, 1)[0] >> 7)

    def _OSF_reset(self):

        self.i2c.readfrom_mem_into(self.addr, STATUS_REG, self._buf)
        self.i2c.writeto_mem(self.addr, STATUS_REG, bytearray([self._buf[0] & 0x7f]))

    def _is_busy(self):

        return bool(self.i2c.readfrom_mem(self.addr, STATUS_REG, 1)[0] & (1 << 2))
