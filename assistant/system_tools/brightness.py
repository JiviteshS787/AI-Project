import screen_brightness_control as sbc

def brightness_up(step=10):
    current = sbc.get_brightness()[0]
    sbc.set_brightness(min(100, current + step))


def brightness_down(step=10):
    current = sbc.get_brightness()[0]
    sbc.set_brightness(max(0, current - step))


def set_brightness(level):
    level = max(0, min(100, level))
    sbc.set_brightness(level)
