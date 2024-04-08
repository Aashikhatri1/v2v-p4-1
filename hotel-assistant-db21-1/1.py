
import pyautogui as pg
import time

def a():
    while True:
        end_call = pg.locateOnScreen("assets/buttons/end_call.png", confidence=0.98)
        if end_call:
            print("Call ended")
            break
        print('not found')
        time.sleep(0.1)


a()