import asyncio
from asyncio.queues import QueueEmpty

from numpy.lib import emath
from requests.api import head
# pip install python-engineio==3.14.2 python-socketio[asyncio_client]==4.6.0

import socketio

import cv2
import base64
import json
import requests

from numba import cuda
import numpy as np
from mpi4py import MPI


sio = socketio.AsyncClient()


class AnsweringAI:
    def __init__(self) -> None:
        self.frame = np.zeros((600, 800, 3), dtype=np.uint8)
        self.question = None
        self.answers = None

    def tick(self):
        # Goal is to find the correct answer
        # Try different things until I get the correct answer
        # Associate the input with the correct answer
        # Not every tick will output an answer
        # Gets 5 seconds to ask 3 questions
        # If it didn't get it, penalize it and then put the correct
        # answer onto the output and then reward it
        # which is connecting the input to the output
        # Reward it heavily when it gets it correct
        # Then move on to the next question 
        # even if it didn't get it correct

        # Learn correlation between scrolling and the input frame
        # a little bit later

        # First show it letters S = S etc. (can do this on our own webpage)
        scroll_x = 0
        scroll_y = 0
        answer = ""
        return (
            scroll_x,
            scroll_y,
            answer,
        )

    def set_frame(self, frame):
        self.frame = frame

    def set_qa(self, question, answers):
        self.question = question
        self.answers = answers
        print("Question=" + question + " Correct Answers=" + str(answers))

TRAIN_LETTERS = True
TRAIN_WORDS = True
TRAIN_READ_ALONG = False
TRAIN_WIKIPEDIA = False
answeringAI = AnsweringAI()
    

@sio.on("frame")
async def on_frame(data):
    data = base64.b64decode(data)
    data = np.frombuffer(data, dtype=np.uint8)
    data = cv2.imdecode(data, flags=cv2.IMREAD_COLOR)
    cv2.imshow("frame", data)
    # (600, 800, 3) uint8
    cv2.waitKey(5)
    answeringAI.set_frame(data)

async def goto(url):
    ft = asyncio.get_event_loop().create_future()
    def cb():
        ft.set_result(True)
    await sio.emit("goto", url, callback=cb)
    await ft
    #headers = {'content-type': 'application/json'}
    #r = requests.post(SERVER_URL + "/goto", 
    #   headers=headers, data=json.dumps({ "url": url }))
    #print(r.status_code, r.reason)

async def watch_youtube():
    await goto("https://www.youtube.com/watch?v=n068fel-W9I")
    await asyncio.sleep(2)
    await sio.emit("mouseMove", {
        "x": 280,
        "y": 290
    })
    await sio.emit("mouseClick", {
        "x": 380,
        "y": 290
    })

async def train_letters():
    letters = []
    # ! # etc.
    for i in range(33, 47+1):
        letters.append(chr(i))
    # 0 to 9
    for i in range(48, 57+1):
        letters.append(chr(i))
    # : ; etc.
    for i in range(58, 65+1):
        letters.append(chr(i))
    # A to Z
    for i in range(65, 90+1):
        letters.append(chr(i))
    # [ ^ etc
    for i in range(91, 97+1):
        letters.append(chr(i))
    # a to z
    for i in range(97, 122):
        letters.append(chr(i))
    # { | etc.
    for i in range(122, 126+1):
        letters.append(chr(i))
    
    for letter in letters:
        await goto(
            SERVER_URL + "/letters?letter=" + letter)
        answers = [letter]
        answeringAI.set_qa("What letter is this?", answers)
        answer = "!"
        await sio.sleep(3)
        while answer not in answers:
            (
                scroll_x,
                scroll_y,
                answer,
            ) = answeringAI.tick()
            if scroll_x != 0 or scroll_y != 0:
                await sio.emit("scroll", { "x": scroll_x, "y": scroll_y })

            await sio.sleep(0.01)
        print("GOT CORRECT ANSWER!")

async def train_words():
    f = open("/usr/share/dict/american-english")
    lines = f.readlines()
    for line in lines:
        line = line.strip("\n")
        await goto(
            SERVER_URL + "/letters?letter=" + line)
        answers = [line]
        answeringAI.set_qa("What word is this?", answers)
        answer = "A"

        while answer not in answers:
            (
                scroll_x,
                scroll_y,
                answer,
            ) = answeringAI.tick()
            if scroll_x != 0 or scroll_y != 0:
                await sio.emit("scroll", { "x": scroll_x, "y": scroll_y })

            await sio.sleep(0.01)
        print("GOT CORRECT ANSWER!")

async def train_read_along():
    pass

async def train_wikipedia():
    # https://rajpurkar.github.io/SQuAD-explorer/
    f = open("./train-v2.0.json")
    js = json.loads(f.read())
    dat = js['data']
    assert(dat[0]['title'] == 'Beyoncé')
    test_data = []
    for cat in dat:
        cat_data = []
        for paragraph in cat['paragraphs']:
            qas = paragraph['qas']
            for qa in qas:
                if qa['is_impossible'] == False:
                    question = qa['question']
                    answers = [d['text'] for d in qa['answers']]
                    cat_data.append({
                        "question": question, 
                        "answers": answers
                    })
        test_data.append({
            "title": cat['title'],
            "qas": cat_data
        })
    
    
    while True:
        for cat in test_data:
            await goto(
                "https://en.wikipedia.org/wiki/" + cat['title'])
            for qa in cat['qas']:
                question = qa["question"]
                answers = qa["answers"]
                answeringAI.set_qa(question, answers)
                answer = "in the late 1990s"
                while answer not in answers:
                    (
                        scroll_x,
                        scroll_y,
                        answer,
                    ) = answeringAI.tick()
                    if scroll_x != 0 or scroll_y != 0:
                        await sio.emit("scroll", { "x": scroll_x, "y": scroll_y })

                    await sio.sleep(0.01)
                print("GOT CORRECT ANSWER!")

SERVER_URL = "http://localhost:4000"

async def main():
    await sio.connect(SERVER_URL)
    await sio.emit("startWebBrowser")
    await asyncio.sleep(2)
    if TRAIN_LETTERS:
        await train_letters()
    elif TRAIN_WORDS:
        await train_words()
    elif TRAIN_READ_ALONG:
        await train_read_along()
    elif TRAIN_WIKIPEDIA:
        await train_wikipedia()
    else:
        await watch_youtube()

    await sio.wait()

async def close():
    await asyncio.sleep(0.1)

def rank0():
    loop = asyncio.get_event_loop()
    try:
        loop.run_until_complete(
            main()
        )
    except KeyboardInterrupt as e:
        print("Keyboard Interrupt")
    finally:
        print("Cleaning up")
        loop.run_until_complete(
            close()
        )

        print("Exiting")

# pkill -9 python
# mpirun -np 3 python3 main.py
if __name__ == "__main__":
    rank = MPI.COMM_WORLD.Get_rank()
    if rank == 0:
        rank0()
