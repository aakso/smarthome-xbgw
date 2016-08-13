import logging
from struct import pack, unpack
LOG = logging.getLogger(__name__)

def watkins_set_temp_relative(value, item=None):
    '''Sets Watkins target temperature. The unit expects target temperature as
    relative value from current target temperature.

    Temperature is accepted by the dia application as an unsigned short integer.
    The relative temperature is encoded to short int as two bytes in big-endian.
    The first byte is allways 0xFF and the second is two's complement of the
    relative temperature. 

    Example: -5 would be 0xFFFB which is 65531 in short int
             +5 would be 0xFF05 which is 65285 in short int'''

    TEMP_BOUNDS = (26, 40)

    if item is None:
        raise RuntimeError("item is required")

    # Find out the relative value
    prev = item.prev_value()
    new = item()
    if not (new >= TEMP_BOUNDS[0] and new <= TEMP_BOUNDS[1]):
        raise RuntimeError("invalid temperature, out of bounds")
    adjust = int((new - prev) / 0.5)

    LOG.debug("watkins_set_temp_relative: prev: {} new: {} adjust steps: {}".format(prev,new,adjust))

    return unpack('>H', pack('>Bb', 0xff, adjust))[0]

def watkins_set_all_lights(value, item=None):
    '''Turn boolean value into set_mz_light compatible value.

    Value is encoded as short int in big endian. First byte is 0x04 and the
    second is 0x11 for SWITCH-ON and 0x10 for SWITCH-OFF.
    
    The exact logic of this is unknown.
    '''

    return unpack('>H', pack('>BB', 0x04, 0x10 + bool(value)))[0]

def old_f_watkins_set_temp_relative(value, item=None):
    '''Sets Watkins target temperature. The unit expects target temperature as
    relative value from current target temperature.

    Temperature is accepted by the dia application as an unsigned short integer.
    The relative temperature is encoded to short int as two bytes in big-endian.
    The first byte is allways 0xFF and the second is two's complement of the
    relative temperature. 

    Example: -5 would be 0xFFFB which is 65531 in short int
             +5 would be 0xFF05 which is 65285 in short int'''

    def celcius_to_fahrenheit(value):
        return round(value * 1.8 + 32)

    if item is None:
        raise RuntimeError("item is required")

    # Find out the relative value
    prev = celcius_to_fahrenheit(item.prev_value())
    new = celcius_to_fahrenheit(item())
    adjust = new - prev

    LOG.debug("watkins_set_temp_relative: prev: {} new: {} adjust: {}".format(prev,new,adjust))

    return unpack('>H', pack('>Bb', 0xff, adjust))[0]

def old_inc_watkins_set_temp_relative(value, item=None):
    '''Sets Watkins target temperature. The unit expects target temperature as
    relative value from current target temperature.

    Temperature is accepted by the dia application as an unsigned short integer.
    The relative temperature is encoded to short int as two bytes in big-endian.
    The first byte is allways 0xFF and the second is two's complement of the
    relative temperature. 

    Example: -5 would be 0xFFFB which is 65531 in short int
             +5 would be 0xFF05 which is 65285 in short int'''

    PLUS = unpack('>H', pack('>Bb', 0xff, 1))[0]
    MINUS = unpack('>H', pack('>Bb', 0xff, -1))[0]

    def celcius_to_fahrenheit(value):
        return round(value * 1.8 + 32)

    if item is None:
        raise RuntimeError("item is required")

    # Find out the relative value
    prev = celcius_to_fahrenheit(item.prev_value())
    new = celcius_to_fahrenheit(item())
    adjust = new - prev

    LOG.debug("watkins_set_temp_relative: prev: {} new: {} adjust: {}".format(prev,new,adjust))

    if adjust > 0:
        return [PLUS] * abs(adjust)
    else:
        return [MINUS] * abs(adjust)
