# Semeru Tools

### Usage

To start swap watch server, run the following script.

```sh
cd bpfcc
sudo python3 swapwatch.py -p <pid>
```

The `swapwatch.py` file will create a unix domain socket located `/tmp/trace-<pid>.uds`.
Upon connection, the server will send back a serialized json byte string of swap statistics.


### Example

To monitor pid 1540 swap statistics, start the server as

```sh
sudo python3 swapwatch.py -p 1540
``` 

Then, connects to it (using the example domain socket script below)

```py
pid = 1540
server_address = f'/tmp/trace-1540.uds'
sock = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
sock.connect(server_address)
data = sock.recv(1024)
print(data)
```

It will prints swap statistics sent back by the server

```
b'{
    "ts": 1585588176.703827, 
    "0x5643a0000000": {"count": 6171, "ratio": 0.0941619873046875}, 
    "0x7fed90000000": {"count": 296, "ratio": 0.0045166015625}, 
    "0x7feda0000000": {"count": 1672, "ratio": 0.0255126953125},
    "0x7fedb0000000": {"count": 2169, "ratio": 0.0330963134765625}, 
    "0x7fedc0000000": {"count": 5066, "ratio": 0.077301025390625}, 
    "0x7fedd0000000": {"count": 855, "ratio": 0.0130462646484375}, 
    "0x7fede0000000": {"count": 0, "ratio": 0.0}, 
    "0x7fedf0000000": {"count": 0, "ratio": 0.0}, 
    "0x7fee00000000": {"count": 0, "ratio": 0.0}, 
    "0x7fee10000000": {"count": 0, "ratio": 0.0}, 
    "0x7fee20000000": {"count": 0, "ratio": 0.0}, 
    "0x7fee30000000": {"count": 0, "ratio": 0.0},
    "0x7fee40000000": {"count": 0, "ratio": 0.0},
    "0x7fee50000000": {"count": 2395, "ratio": 0.0365447998046875}, 
    "0x7fee60000000": {"count": 2591, "ratio": 0.0395355224609375}, 
    "0x7fee70000000": {"count": 5089, "ratio": 0.0776519775390625}, 
    "0x7fee80000000": {"count": 8669, "ratio": 0.1322784423828125}, 
    "0x7ffe60000000": {"count": 27, "ratio": 0.00}
}'
```
