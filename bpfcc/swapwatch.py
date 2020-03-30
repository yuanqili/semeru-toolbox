#!/usr/bin/python3
import argparse
import json
import os
import socket
from collections import defaultdict
from time import ctime, time

from bcc import BPF

from pyproc import ProcMonitor
from utils import load_src


def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument('-p', '--pid', type=int)
    parser.add_argument('--page_bits', type=int, default=12, help='page size in bits')
    parser.add_argument('--block_bits', type=int, default=28, help='block size in bits')
    parser.add_argument('--interval', type=float, default=0.5, help='interval of printing')
    return parser.parse_args()


if __name__ == '__main__':

    args = parse_args()

    pid = args.pid
    page_size_bits = args.page_bits
    addr_block_bits = args.block_bits
    interval = args.interval

    page_size = 2 ** page_size_bits
    addr_block_size = 2 ** addr_block_bits
    addr_block_page_count = 2 ** (addr_block_bits - page_size_bits)
    template = {
        '{{FILTER_PID}}': 'if (pid != %d) {return 0;}' % pid,
        '{{OFFSET}}': str(addr_block_bits),
    }
    default_stats = {'in': 0, 'out': 0, 'count': 0, 'ratio': 0}

    print(f'Attached to kernel')

    # reads process address space information, which happened before starting monitoring
    print(f'Initializing...')
    pm = ProcMonitor(pid)
    smaps = pm.smaps()
    page_stats_init = defaultdict(lambda: default_stats)
    for item in smaps:
        addr_block_start = item['address_start'] >> addr_block_bits << addr_block_bits
        addr_block_end = item['address_end'] >> addr_block_bits << addr_block_bits
        block_range = list(range(addr_block_start, addr_block_end + 1, addr_block_size))
        for block in block_range:
            if str(hex(block)) in page_stats_init:
                continue
            block_stat = pm.pagemap(block, block + addr_block_size)
            page_stats_init[str(hex(block))] = block_stat

    # loads BPF program and starts watching
    src_path = 'swapwatch.c'
    src_text = load_src(src_path, template)
    b = BPF(text=src_text)

    # creates domain socket and starts listening
    server_address = f'/tmp/trace-{pid}.uds'
    try:
        os.unlink(server_address)
    except OSError:
        if os.path.exists(server_address):
            raise
    sock = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
    sock.bind(server_address)
    sock.listen(1)

    print(f'Tracing...')
    while True:
        print('listening...')
        conn, client = sock.accept()
        print('accepted')

        print(ctime())
        ts = time()

        page_stats_delta = {}
        for addr, count in b['page_stats'].items():
            page_stats_delta[str(hex(addr.value))] = {
                'in': count.page_in,
                'out': count.page_out
            }
        address_spaces = list(set(list(page_stats_delta.keys()) + list(page_stats_init.keys())))
        address_spaces.sort()

        payload = {'ts': ts}
        for addr in address_spaces:
            page_in_init = page_stats_init.get(addr, default_stats)['in']
            page_out_init = page_stats_init.get(addr, default_stats)['out']
            page_in_delta = page_stats_delta.get(addr, default_stats)['in']
            page_out_delta = page_stats_delta.get(addr, default_stats)['out']
            count = max(page_in_init + page_in_delta - page_out_delta, 0)
            ratio = count / addr_block_page_count
            payload[addr] = {
                'count': count,
                'ratio': ratio
            }
            print(f'{addr} {count:7d} {ratio * 100:8.4f}')
        print('-' * 32)

        conn.sendall(str.encode(json.dumps(payload)))
