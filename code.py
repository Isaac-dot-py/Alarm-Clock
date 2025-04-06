# use this command to do mp3 -> wav conversion
# ffmpeg -i orig.mp3 -f wav -bitexact -acodec pcm_s16le -ac 1 -ar 16000 orig.wav
# Sequence of time info: (tm_year, tm_mon, tm_mday, tm_hour, tm_min, tm_sec, tm_wday, tm_yday, tm_isdst)

import rtc  # type: ignore
import time  # type: ignore
import board  # type: ignore
import atexit  # type: ignore
import keypad  # type: ignore
import neopixel  # type: ignore
import digitalio  # type: ignore
from audiocore import WaveFile  # type: ignore
from audiopwmio import PWMAudioOut  # type: ignore
from tm1637_display import TM1637Display  # type: ignore

# allocate ram here
display = TM1637Display(board.GP0, board.GP1, length=4)
lights = neopixel.NeoPixel(board.GP3, 12)
lights.fill((0, 0, 0))
event = keypad.Event()  # reuseable
wv = WaveFile(open("orig.wav", "rb"))
rtc.RTC().datetime = time.struct_time((2025, 3, 31, 18, 6, 23, 0, 90, 1))

ALARM_TIME = (17, 34)  # 5:40 pm
DESCRIPTIONS = [
    "year (eg 2025)",
    "month (1-12)",
    "month day (1-31)",
    "hour (0-23)",
    "minute (0-59)",
    "second (0-59)",
    "week day (0-6) (monday is 0)",
    "year day (0-366)",
    "is dst (0-1)",
]


def scroll_text(text):
    """
    Scroll text on display.

    If text was "abcdef", it would display:
    1. abcd
    2. bcde
    3. cdef
    """
    if len(text) < 4:
        display.print(text)
        time.sleep(0.5)
        return
    for i in range(len(text) - 3):
        display.print(text[i : i + 4])
        time.sleep(0.5)


def input_num(desciption):
    scroll_text(desciption)
    pass  # TODO


def set_time():
    pass  # TODO


def play():
    audio = PWMAudioOut(board.GP2)
    audio.play(wv)
    try:
        while audio.playing:
            pass
    finally:
        audio.deinit()
        del audio
        speakerpin = digitalio.DigitalInOut(board.GP2)
        speakerpin.direction = digitalio.Direction.OUTPUT
        speakerpin.value = False
        speakerpin.deinit()
        del speakerpin


def gamma(r, g, b):
    # input and output range 0-255
    GAMMA_FACTOR = 2.8
    return (
        int((r / 255) ** GAMMA_FACTOR * 255),
        int((g / 255) ** GAMMA_FACTOR * 255),
        int((b / 255) ** GAMMA_FACTOR * 255),
    )


def interpolate_color(t: float) -> tuple[int, int, int]:
    """
    Interpolates between (0,0,0) -> (255,0,0) -> (0,0,255) -> (255,255,255)
    based on the input t in the range [0,1].
    """
    if not 0 <= t <= 1:
        raise ValueError("t must be in the range [0,1]")

    if t < 1 / 3:  # (0,0,0) -> (255,0,0)
        ratio = t / (1 / 3)
        return int(255 * ratio), 0, 0
    elif t < 2 / 3:  # (255,0,0) -> (0,0,255)
        ratio = (t - 1 / 3) / (1 / 3)
        return int(255 * (1 - ratio)), 0, int(255 * ratio)
    else:  # (0,0,255) -> (255,255,255)
        ratio = (t - 2 / 3) / (1 / 3)
        return int(255 * ratio), int(255 * ratio), 255


def sunrise():
    start_time = time.monotonic()
    STEP = 0.001
    WAIT_TIME = 0.57
    for t in range(1 / STEP):
        t *= STEP
        lights.fill(interpolate_color(t))
        time.sleep(WAIT_TIME)
    time.sleep(30)
    lights.fill((0, 0, 0))
    # print time elapsed in seconds
    print(time.monotonic() - start_time)


@atexit.register
def cleanup():
    lights.fill((0, 0, 0))
    lights.deinit()
    display.print("")
    display.deinit()


while True:
    display.print(f"{time.localtime().tm_hour%12}.{time.localtime().tm_min:02d}")
    if (
        time.localtime().tm_hour == ALARM_TIME[0]
        and time.localtime().tm_min == ALARM_TIME[1]
    ):
        sunrise()
        # play() TODO
    time.sleep(1)  # TODO
