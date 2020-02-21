#!/usr/bin/python3

from bcc import BPF
from bcc.utils import printb

# from include/linux/blk_types.h
# We define it here since we are gonna use it in the python code.
# If we were using it in the BPF program, it should just work with
# appropriate includes.
REQ_WRITE = 1

program = """
#include <uapi/linux/ptrace.h>
#include <linux/blkdev.h>

BPF_HASH(start, struct request *);

void trace_start(struct pt_regs *ctx, struct request *req)
{
    u64 ts = bpf_ktime_get_ns();
    start.update(&req, &ts);
}

void trace_completion(struct pt_regs *ctx, struct request *req)
{
    u64 *tsp, delta;
    
    tsp = start.lookup(&req);
    if (tsp) {
        delta = bpf_ktime_get_ns() - *tsp;
        bpf_trace_printk(
            "%d %x %d\\n",
            req->__data_len, req->cmd_flags, delta / 1000
        );
        start.delete(&req);
    }
}
"""


if __name__ == '__main__':
    b = BPF(text=program)
    if BPF.get_kprobe_functions(b'blk_start_request'):
        b.attach_kprobe(event='blk_start_request', fn_name='trace_start')
    b.attach_kprobe(event='blk_mq_start_request', fn_name='trace_start')
    b.attach_kprobe(event='blk_account_io_completion', fn_name='trace_completion')

    print('%-15s %-2s %-7s %8s' % ('TIME(s)', 'T', 'BYTES', 'LAT(ms)'))
    while True:
        try:
            task, pid, cpu, flags, ts, msg = b.trace_fields()
            bytes_s, bflags_s, us_s = msg.split()
            if int(bflags_s, 16) & REQ_WRITE:
                type_s = b'W'
            elif bytes_s == '0':
                type_s = b'M'
            else:
                type_s = b'R'
            ms = float(int(us_s, 10)) / 1000
            printb(b'%-15.6f %-2s %-7s %8.2f' % (ts, type_s, bytes_s, ms))
        except KeyboardInterrupt:
            exit()
