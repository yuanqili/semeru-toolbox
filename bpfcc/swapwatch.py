#!/usr/bin/python3
from time import sleep
from multiprocessing import Process

from bcc import BPF

import numpy as np
import matplotlib.pyplot as plt
import plotext.plot as plx


def page_stat(cpu, data, size):
    global start
    global page_data
    event = b['page_in'].event(data)
    if start == 0:
        start = event.ts
    ts = (float(event.ts - start)) / 1e9

    # print('%-18.9f 0x%lx %-6d' % (ts, event.address, event.pid))
    page_data.append(event.address)


def bpf_poll():
    b.perf_buffer_poll()


if __name__ == '__main__':
    b = BPF(src_file='swapwatch.c')

    page_data = []
    start = 0
    b['page_in'].open_perf_buffer(page_stat)

    # try:
    #     while True:
    #         b.perf_buffer_poll()
    # except KeyboardInterrupt:
    #     pass
    #
    # hist = np.histogram(page_data, bins=64)
    # print(hist)

    Process(target=bpf_poll).start()

    do_exit = False
    while True:
        try:
            sleep(1)
        except KeyboardInterrupt:
            break

        b['fault_dist'].print_log2_hist('msecs')
        b['fault_dist'].clear()
        # b.perf_buffer_poll()
        print(len(page_data))

        if do_exit:
            break

    hist = np.histogram(page_data, bins=64)
    print(hist)
