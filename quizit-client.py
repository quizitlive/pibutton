#!/usr/bin/python
from gpiozero import LED, Button
from signal import pause

import websocket
import _thread
import time

import json
import requests

token = "REPLACE WITH YOUR TOKEN"

url = 'https://dev.quizit.net/hardware/answer'
referer = url
ws_url = 'wss://dev.quizit.net/ws/hw/'

button = [Button(4),Button(18),Button(17),Button(27)]
led = [LED(22),LED(23),LED(24),LED(5)]

BUTTON_COUNT = len(button)
LED_COUNT = len(led)

question_played = None

def set_all_leds(state):
    print ('setting all leds to {}'.format(state))
    if state:
        for i in range(LED_COUNT):
            led[i].on()
    else:
        for i in range(LED_COUNT):
            led[i].off()



def submit_answer(answer_id):
    print("button {} pressed ".format(answer_id))
    global question_played, state, start_time

    if state!='open':
        return False
    
    oldstate = state
    state = 'closed'

    end_time = time.time()
    elapsed_time = end_time - start_time
    print(elapsed_time)

    headers = {
        'referer': referer,
        'User-Agent': 'Mozilla/5.0 (Windows NT 6.1; WOW64; rv:28.0) Gecko/20100101 Firefox/28.0',
        'Accept': 'application/json, text/javascript, */*; q=0.01',
        'Content-Type': 'application/x-www-form-urlencoded; charset=UTF-8',
        'X-Requested-With': 'XMLHttpRequest',
        'Authentication': 'Bearer:{}'.format(token),
    }


    data = dict(action='answer',
                # psk=pre_shared_key,
                question_played_in_round=question_played,
                answer=answer_id,
                timer=elapsed_time,
#                csrfmiddlewaretoken=csrftoken
                )

    r = requests.post(url, data=data, allow_redirects=True, headers=headers)

    set_all_leds(0)

    result = json.loads(r.content.decode('utf-8'))
    print (result['success'])
    if 'close' in result:
        state = 'closed'
    else:
        state = oldstate
    if result['success']:
        print (answer_id)
        led[answer_id].on()
        return True
    return False


def on_message(ws, message):
    global state, question_played, start_time
    print ("receieved"+message)
    msg = json.loads(message)
    if 'type' in msg:
        if msg['type']=='open_answering':
            print ('open answering of {} for {}'.format(msg['question_played'],msg['time']))
            question_played=msg['question_played']
            state = 'open'
            start_time = time.time()
            set_all_leds(1)
        elif msg['type']=='close_answering':
            print ('stop answers')
            state = 'closed'
        elif msg['type']=='display':
            set_all_leds(0)
        else:
            pass

def on_error(ws, error):
    print (error)

def on_close(ws):
    print ("### closed ###")
#TODO restart or exit


def on_open(ws):
    print ("opening")


if __name__ == "__main__":
    #    websocket.enableTrace(True)
    state = 'idle'
    print ('setting up buttons')
    button[0].when_pressed = lambda: submit_answer(0)
    button[1].when_pressed = lambda: submit_answer(1)
    button[2].when_pressed = lambda: submit_answer(2)
    button[3].when_pressed = lambda: submit_answer(3)
#    for i in range(BUTTON_COUNT):
#        button[i].when_pressed = lambda: submit_answer(i)
#   

    ws = websocket.WebSocketApp(ws_url,
                                header=['Authentication: Bearer:{}'.format(token)],
                                on_message = on_message,
                                on_error = on_error,
                                on_close = on_close)
                                
    ws.on_open = on_open

    ws.run_forever()
    
    pause()
