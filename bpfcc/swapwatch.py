#!/usr/bin/python3
from time import sleep

from bcc import BPF
from bcc.utils import printb


def load_src(path, template):
    with open(path) as f:
        src = f.read()
    for k, v in template.items():
        src = src.replace(k, v)
    return src


if __name__ == '__main__':

    src_path = 'swapwatch.c'
    pid = 28886
    template = {'{{FILTER_PID}}': 'if (pid != %d) {return 0;}' % pid}
    src_text = load_src(src_path, template)

    b = BPF(text=src_text)

    while True:
        regions = b.get_table('region')
        for k, v in sorted(regions.items(), key=lambda p: p[0].value):
            printb(b'0x%lx %6d' % (k.value, v.value))
        print('-' * 32)
        sleep(1)
