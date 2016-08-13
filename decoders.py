def watkins_str_fahrenheit_to_celcius(value, item=None):
    if item is None:
        raise RuntimeError("item is required")

    if isinstance(value, str):
        if value[-1] != 'F':
            raise ValueError("cannot decode value: {}".format(value))
        value = int(value[:-1])

    # Because of rounding to half degress we will return None in case it will
    # convert to a fahrenheit value that this decoder was called with. This is
    # very uggly but otherwise when user sets temperature to 37.5C it will get reset
    # to 38.0C as both 37.5C and 38.0C will round to 100F
    current = round(item() * 1.8 + 32)
    if current == value:
        return None

    # We will convert and round to nearest half degrees
    celcius = round((value - 32) / 1.8 / 0.5) * 0.5
    return celcius

def watkins_pump_speed(value, item=None):
    return int(value) + 1

def watkins_all_lights_on(value, item=None):
    return int(value) > 0
