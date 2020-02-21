#!/usr/bin/python3
import argparse
from time import sleep

from bcc import BPF


def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument('--interval', type=int, default=5, nargs='?')
    parser.add_argument('--count', type=int, default=-1, nargs='?')
    return parser.parse_args()


if __name__ == '__main__':
    args = parse_args()
    interval = args.interval
    count = args.count

    b = BPF(src_file='vfsreadlat.c')
    b.attach_kprobe(event='vfs_read', fn_name='do_entry')
    b.attach_kprobe(event='vfs_read', fn_name='do_return')

    loop = 0
    do_exit = 0
    while True:
        if count > 0:
            loop += 1
            if loop > count:
                exit()
        try:
            sleep(interval)
        except KeyboardInterrupt:
            do_exit = 1

        print()
        b['dist'].print_log2_hist('usecs')
        b['dist'].clear()
        if do_exit:
            exit()
