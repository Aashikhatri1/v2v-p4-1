
import pyautogui as pg
import time


# import csv2json
# csv2json.convert_csv_to_json('data.csv')

end_call = pg.locateOnScreen("assets/buttons/end_call.png", confidence = 0.95)
time.sleep(5)
end_call_trial = pg.locateOnScreen("assets/buttons/end_call_trial.png", confidence = 0.98)
if end_call_trial:
    pg.click(end_call_trial)
    print('cl')
else:
    print('not found')
