#!/usr/bin/python3
import argparse
from collections import defaultdict
from time import sleep, time

from bcc import BPF

from pyproc import ProcMonitor
from utils import load_src


def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument('-p', '--pid', type=int)
    parser.add_argument('--page_bits', type=int, default=12, help='page size in bits')
    parser.add_argument('--block_bits', type=int, default=28, help='block size in bits')
    parser.add_argument('--interval', type=float, default=1, help='interval of printing')
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
            # print(hex(block), hex(block + addr_block_size), page_stats_init[str(hex(block))])

    # loads BPF program and starts watching
    src_path = 'swapwatch.c'
    src_text = load_src(src_path, template)
    b = BPF(text=src_text)
    print(f'Attached to kernel')

    while True:
        page_stats = defaultdict(lambda: default_stats)

        page_in = b.get_table('page_in')
        for address_space, count in page_in.items():
            address = str(hex(address_space.value))
            page_stats[address]['in'] = count.value

        page_out = b.get_table('page_out')
        for address_space, count in page_out.items():
            address = str(hex(address_space.value))
            page_stats[address]['out'] = count.value

        print(time())
        address_keys = sorted(list(page_stats.keys()) + list(page_stats_init.keys()))
        for address in address_keys:
            count = (page_stats[address]['in'] + page_stats_init[address]['in'] - page_stats[address]['out'])
            ratio = max(count / addr_block_page_count, 0)  # TODO: total count is not accurate now
            print(f'{address} {ratio:.6f}')
            # print(f'{page_stats[address]["in"]} '
            #       f'{page_stats_init[address]["in"]} '
            #       f'{page_stats[address]["out"]} '
            #       f'{page_stats_init[address]["out"]} '
            #       f'count={count} '
            #       f'ratio={ratio * 100:.2f}')
        print('-' * 32)

        sleep(interval)
