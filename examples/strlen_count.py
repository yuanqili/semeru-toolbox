#!/usr/bin/python3
from time import sleep

from bcc import BPF


if __name__ == '__main__':
    b = BPF(src_file='strlen_count.c')
    # Attaches to library C (if this is the main program, use its pathname,
    # instruments the user-level function strlen(), and on execution calls our
    # C function count()
    b.attach_uprobe(name='c', sym='strlen', fn_name='count')

    try:
        sleep(99999999)
    except KeyboardInterrupt:
        pass

    print(f'{"count":10s} string')
    counts = b.get_table('counts')
    for k, v in sorted(counts.items(), key=lambda counts: counts[1].value):
        print(f'{v.value:10d} "{k.c.decode("utf-8")}"')
