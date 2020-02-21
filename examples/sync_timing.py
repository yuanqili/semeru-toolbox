#!/usr/bin/python3

from bcc import BPF


program = """
#include <uapi/linux/ptrace.h>

BPF_HASH(last);

int do_trace(struct pt_regs *ctx) {
    u64 ts, *tsp, delta, key = 0;

    // attempt to read stored timestamp
    tsp = last.lookup(&key);
    if (tsp != 0) {
        delta = bpf_ktime_get_ns() - *tsp;
        if (delta < 1000000000) {
            // output if time is less than 1 second
            bpf_trace_printk("%d\\n", delta / 1000000);
        }
        last.delete(&key);
    }

    // update stored timestamp
    ts = bpf_ktime_get_ns();
    last.update(&key, &ts);
    return 0;
}
"""


if __name__ == '__main__':
    b = BPF(text=program)
    b.attach_kprobe(event=b.get_syscall_fnname('sync'), fn_name='do_trace')

    start = 0
    while True:
        task, pid, cpu, flags, ts, ms = b.trace_fields()
        if start == 0:
            start = ts
        ts = ts - start
        print(f'[{ts:.6f}] multiple syncs detected, last {ms.decode()}ms ago')
