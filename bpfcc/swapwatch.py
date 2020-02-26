#!/usr/bin/python3
from time import sleep

from bcc import BPF


def load_src(path, template):
    with open(path) as f:
        src = f.read()
    for k, v in template.items():
        src = src.replace(k, v)
    return src


if __name__ == '__main__':

    pid = 23119
    address_block_bits = 30  # 28: 256MB, 30: 1GB
    page_size_bits = 12      # 4KB
    page_size = 2 ** page_size_bits
    address_block_size = 2 ** address_block_bits
    address_block_page_count = 2 ** (address_block_bits - page_size_bits)
    template = {
        '{{FILTER_PID}}': 'if (pid != %d) {return 0;}' % pid,
        '{{OFFSET}}': str(address_block_bits),
    }

    src_path = 'swapwatch.c'
    src_text = load_src(src_path, template)

    b = BPF(text=src_text)
    print(f'Attached to kernel')

    while True:

        page_in = b.get_table('page_in')
        page_in_stats = {}
        for address_space, count in page_in.items():
            address = str(hex(address_space.value))
            page_in_stats[address] = count.value

        page_out = b.get_table('page_out')
        page_out_stats = {}
        for address_space, count in page_out.items():
            address = str(hex(address_space.value))
            page_out_stats[address] = count.value

        page_stats = {}
        for address, count in page_in_stats.items():
            if not page_stats.get(address, None):
                page_stats[address] = {}
            page_stats[address]['in'] = count
        for address, count in page_out_stats.items():
            if not page_stats.get(address, None):
                page_stats[address] = {}
            page_stats[address]['out'] = count
        for address in sorted(page_stats.keys()):
            page_stats[address]['count'] = page_stats[address].get('in', 0) - page_stats[address].get('out', 0)
            page_stats[address]['ratio'] = page_stats[address]['count'] / address_block_page_count
            print(f'{address} '
                  f'{page_stats[address]["count"]:8d} '
                  f'{page_stats[address]["ratio"]*100:9.2f}')
        print('-' * 32)
        sleep(1)
