# Jade Activate

## Install
```bash
$ cd pycli
$ python -m venv env
$ source ./env/bin/activate
$ pip install -r requirements.txt
```

## Setting up audio recording
```bash
$ pacmd load-module module-loopback latency_msec=5pav
$ pavucontrol 
# Input Devices
# Show All Input Devices
# Click the green check mark next to "Monitor of Built-in Audio Analog Stereo"
```

## Run
```bash
$ cd ./server && yarn start
```

```bash
$ cd ./client && yarn start
# open localhost:3000 in Chrome
```

```bash
$ cd pycli
$ source ./env/bin/activate
$ mpirun -np 4 python3 main.py
```

Run the android app