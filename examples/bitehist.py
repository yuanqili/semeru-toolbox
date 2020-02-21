#!/usr/bin/python3

from bcc import BPF
from time import sleep


prog = """
#include <uapi/linux/ptrace.h>
#include <linux/blkdev.h>

// a BPF map object that is a histogram
BPF_HISTOGRAM(dist);

// The prefix kprobe__ means the rest will be treated as a kernel function name
// that will be instrumented using kprobe
// @ctx: registers and BPF context
// @req: the first argument to the instrumented function, blk_account_io_completion
int kprobe__blk_account_io_completion(struct pt_regs *ctx, struct request *req)
{
    // Increments the histogram bucket index provided as the first argument by
    // one by default. Optionally, custom increments can be passed as the second
    // argument.
    dist.increment(bpf_log2l(req->__data_len / 1024));
    return 0;
}
"""

if __name__ == '__main__':
    b = BPF(text=prog)
    try:
        sleep(99999999)
    except KeyboardInterrupt:
        print()
    b['dist'].print_log2_hist('kbytes')
