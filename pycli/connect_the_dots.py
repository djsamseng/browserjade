"""
When the environment is good (low stress)
connect the dots.
Starts in the womb - the parents inputs and outputs
connect the dots for the baby

Training problem. Init = tons of neurons all unconnected
Input image t=0 -> nothing
Input image t=10 -> desired output t=10
    Input image t=0 -> delay nodes t=0 to t=10 -> desired output t=10
"""
import asyncio
import base64
import cv2
import numpy as np
import socketio
import time
import torch

model_x = None
sio = None

device = "cuda" if torch.cuda.is_available() else "cpu"
print("Using {} device".format(device))

class CircularNeuralNetwork(torch.nn.Module):
    def __init__(self, num_inputs, num_outputs, num_state) -> None:
        super(CircularNeuralNetwork, self).__init__()
        self.flatten = torch.nn.Flatten()
        num_in = num_inputs + num_state
        num_out = num_outputs + num_state
        hidden_height = 200
        hidden_depth = 200
        layers = []
        for i in range(hidden_depth):
            layers.append(torch.nn.Linear(hidden_height, hidden_height))
            layers.append(torch.nn.ReLU())
        
        self.linear_relu_stack = torch.nn.Sequential(
            torch.nn.Linear(num_in, hidden_height),
            torch.nn.ReLU(),
            *layers,
            torch.nn.Linear(hidden_height, num_out),
            torch.nn.Sigmoid()
        )
    def forward(self, x):
        x = self.flatten(x)
        logits = self.linear_relu_stack(x)
        return logits

NUM_STATE = 150
NUM_INPUTS = 800 * 600 * 3
async def create_model():
    global model_x
    num_inputs = NUM_INPUTS
    num_outputs = 10
    num_state = NUM_STATE
    model_x = torch.rand((1, num_state + num_inputs))
    model = CircularNeuralNetwork(
        num_inputs=num_inputs,
        num_outputs=num_outputs,
        num_state=num_state).to(device)
    print("Created model with num_parameters:", len([p for p in model.parameters()]))
    loss_fn = torch.nn.MSELoss()
    optimizer = torch.optim.SGD(model.parameters(), lr=100)
    model.train()
    return model, loss_fn, optimizer


async def run_model(model, loss_fn, optimizer):
    itr = 0
    while True:
        itr += 1
        t_loop_begin = time.time()
        x_input = model_x.detach().clone().to(device)
        t_model0 = time.time()
        pred = model(x_input)
        t_model1 = time.time()
        # avoid cuda memory leak
        model_x[0, :NUM_STATE] = pred[0, :NUM_STATE].detach()
        model_y = pred.detach().clone()
        #model_y[0, NUM_STATE:] += 1
        loss = loss_fn(pred, model_y)
        if itr % 100 == 1:
            print("Loss:", loss)
            t_backprop0 = time.time()
            optimizer.zero_grad()
            loss.backward()
            optimizer.step()
            t_backprop1 = time.time()
        output = pred[0, NUM_STATE:]
        x = 800 * (output[0].item() + 1) / 2
        y = 600 * (output[1].item() + 1) / 2
        t_loop_end = time.time()
        if itr % 100 == 0:
            print(
                "Model:", t_model1 - t_model0, 
                "Total:", t_loop_end - t_loop_begin, 
                "Backprop:", t_backprop1 - t_backprop0
            )
            print(x, y)
        await sio.emit("mouseMove", {
            "x": x,
            "y": y,
        })
        await asyncio.sleep(0.01)

async def create_socket():
    global sio
    sio = socketio.AsyncClient()
    await sio.connect("http://localhost:4000")
    await sio.emit("startWebBrowser")
    await asyncio.sleep(2)
    await sio.emit("goto", "https://www.youtube.com/watch?v=n068fel-W9I")
    @sio.on("frame")
    async def on_frame(data):
        t0 = time.time()
        data = base64.b64decode(data)
        data = np.frombuffer(data, dtype=np.uint8)
        data = cv2.imdecode(data, flags=cv2.IMREAD_COLOR)
        size = min(data.size, NUM_INPUTS)
        model_x[0, NUM_STATE:NUM_STATE + size] = torch.from_numpy(data.flatten().copy())[:size] / 255.
        t1 = time.time()
        #print("on_frame took:", t1 - t0)
        cv2.imshow("frame", data)
        cv2.waitKey(5)


async def main():
    torch.manual_seed(0)
    model, loss_fn, optimizer = await create_model()
    await create_socket()
    await run_model(model, loss_fn, optimizer)

async def close():
    await asyncio.sleep(0.1)

def run_main():
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

if __name__ == "__main__":
    run_main()