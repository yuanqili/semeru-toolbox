import os
import struct
import sys


def read_entry(path, offset, size=8):
    with open(path, 'rb') as f:
        f.seek(offset)
        return f.read(size)
        # return struct.unpack('Q', f.read(size))[0]


def get_pagemap_entry(pid, addr):
    """Read /proc/$pid/pagemap"""
    pagemap = f'/proc/{pid}/pagemap'
    if not os.path.isfile(pagemap):
        print(f'process {pid} does not exists')
        return

    page_size = os.sysconf('SC_PAGE_SIZE')
    pagemap_entry_size = 8
    offset = (addr // page_size) * pagemap_entry_size

    return read_entry(pagemap, offset)


def get_pfn(entry):
    return entry & 0x7FFFFFFFFFFFFF


def is_present(entry):
    return (entry & (1 << 63)) != 0


def is_file_page(entry):
    return (entry & (1 << 61)) != 0


def split_by_len(item, maxlen):
    return [item[ind:ind+maxlen] for ind in range(0, len(item), maxlen)]


def summary(pid, addr1, addr2):
    num_pages = (addr2 - addr1) // 0x1000

    pagemap = f'/proc/{pid}/pagemap'
    page_size = os.sysconf('SC_PAGE_SIZE')
    pagemap_entry_size = 8
    offset = (addr1 // page_size) * pagemap_entry_size
    print(f'offset: {offset}')

    with open(pagemap, 'rb') as f:
        f.seek(offset)
        entries = f.read(8 * num_pages)

    entries = bin(int.from_bytes(entries, byteorder=sys.byteorder))[2:]
    entries = split_by_len(entries, 64)

    pages_in = sum([0 if pfn[0] == '0' else 1 for pfn in entries])
    pages_out = len(entries) - pages_in
    ratio = pages_in / len(entries)

    rss = pages_in * 4096 // 1024
    swap = pages_out * 4096 // 1024

    print(f'virtual addr {hex(addr1)} to {hex(addr2)}')
    print(f'Rss:  {rss:8d} kB, {pages_in:8d} pages')
    print(f'Swap: {swap:8d} kB, {pages_out:8d} pages')
    print(f'ratio: {ratio * 100:.4f}% pages in')


if __name__ == '__main__':
    # _pid = sys.argv[1]
    # addr1 = int(sys.argv[2], 16)
    # addr2 = int(sys.argv[3], 16)
    # summary(_pid, addr1, addr2)

    summary(pid=11999, addr1=0x7f45c0000000, addr2=0x7f45d0000000)
    summary(pid=11999, addr1=0x7f45d0000000, addr2=0x7f45e0000000)
