from config import BUTTON_PINS, PULL_UP

class Input:
    def __init__(self):
        self._gpio_ok = False
        try:
            import RPi.GPIO as GPIO
            self.GPIO = GPIO
            if BUTTON_PINS:
                GPIO.setmode(GPIO.BCM)
                for pin in BUTTON_PINS.values():
                    GPIO.setup(pin, GPIO.IN,
                               pull_up_down=GPIO.PUD_UP if PULL_UP else GPIO.PUD_DOWN)
            self._gpio_ok = bool(BUTTON_PINS)
        except Exception:
            self._gpio_ok = False

    def read(self):
        if not self._gpio_ok:
            return {}
        states = {}
        for name, pin in BUTTON_PINS.items():
            val = self.GPIO.input(pin)
            pressed = (val == 0) if PULL_UP else (val == 1)
            states[name] = pressed
        return states

    def cleanup(self):
        if self._gpio_ok:
            self.GPIO.cleanup()
