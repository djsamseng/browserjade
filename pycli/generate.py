
import numpy as np
from numba import cuda
from typing import Dict, NamedTuple

def make_gate(i):
    if i == 0:
        def gate(input, state):
            output = np.zeros_like(input)
            if state:
                output[0] = 1
            return output
        return gate
    else:
        def gate(input, state):
            output = np.zeros_like(input)
            if state:
                output[1] = 1
            return output
        return gate
        


def kernel(
    memory,
    chrome_video)->None:
    # try to recreate webcam_video etc. using memory
    for i in range(memory.shape[1]):
        for j in range(memory.shape[2]):
            for k in range(memory.shape[3]):
                memory[0, i, j, k] = chrome_video[i,j,k]

class IntelState:
    
    def __init__(
        self,
    ) -> None:
        memory_size = (1000, )
        self.__memory = cuda.to_device(
            np.array(memory_size)
        )

    def tick(
        self,
        webcam_video:"list[int]",
        webcam_audio:"list[int]",
        chrome_video:"list[int]",
        chrome_audio:"list[int]"
    ) -> NamedTuple("Return",
        mouseClickX=int,
        mouseClickY=int,
        mouseMoveX=int,
        mouseMoveY=int,
        audioOut="list[int]",
        videoOut="list[int]" # how did I recreate the input image? Dog + outside + grass + ...
    ):
        mouseClickX = -1
        mouseClickY = -1
        mouseMoveX = -1
        mouseMoveY = -1
        audioOut = []
        videoOut = []
        kernel[32, 32](
            self.__memory,
            chrome_video
        )
        return (
            mouseClickX,
            mouseClickY,
            mouseMoveX,
            mouseMoveY,
            audioOut,
            videoOut
        )

def do_jit():
    global kernel
    kernel = cuda.jit()(kernel)

