#!/usr/bin/python3
import argparse
from collections import defaultdict
from time import sleep

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


def page_in_callback(cpu, data, size):
    page_in = b['page_in'].event(data)
    address = page_in.address >> addr_block_bits << addr_block_bits
    page_stats[address]['in'] += 1


def page_out_callback(cpu, data, size):
    page_out = b['page_out'].event(data)
    address = page_out.address >> addr_block_bits << addr_block_bits
    page_stats[address]['out'] += 1


def print_stats():
    for addr, count in page_stats.items():
        print(hex(addr), count)


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

    # reads process address space information, which happened before starting monitoring
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
    src_path = 'swapsnoop_addronly.c'
    src_text = load_src(src_path, template)
    b = BPF(text=src_text)
    print(f'Attached to kernel')

    page_stats = defaultdict(lambda: {'in': 0, 'out': 0})

    b['page_in'].open_perf_buffer(page_in_callback)
    b['page_out'].open_perf_buffer(page_out_callback)

    while True:
        try:
            b.perf_buffer_poll()
            print_stats()
            print('-' * 32)
            sleep(interval)
        except KeyboardInterrupt:
            exit()
