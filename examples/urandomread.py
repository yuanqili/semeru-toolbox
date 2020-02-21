#!/usr/bin/python3

from bcc import BPF


prog = """
// Instrument the kernel tracepoint random:urandom_read. They have a stable API,
// and thus are recommend to use instead of kprobes, wherever possible. You can
// run `perf list` for a list of tracepoints.
// Linux >= 4.7 is required to attach BPF programs to tracepoints.
TRACEPOINT_PROBE(random, urandom_read)
{
    // arg is from /sys/kernel/debug/tracing/events/random/urandom_read/format
    // arg is auto-populated to be a structure of the tracepoint arguments
    bpf_trace_printk("%d\\n", args->got_bits);
    return 0;
}
"""


if __name__ == '__main__':
    b = BPF(text=prog)
    print('%-18s %-16s %-6s %s' % ('TIME(s)', 'COMM', 'PID', 'GOTBITS'))

    while True:
        try:
            task, pid, cpu, flags, ts, msg = b.trace_fields()
        except ValueError:
            continue
        print('%-18.9f %-16s %-6d %s' % (ts, task, pid, msg))
