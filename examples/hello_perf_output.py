#!/usr/bin/python3

from bcc import BPF

# define BPF program
prog = """
#include <linux/sched.h>

// Defines the C struct we'll use to pass data from kernel to userspace
struct data_t {
    u32 pid;
    u64 ts;
    char comm[TASK_COMM_LEN];
};
// Names our output channel, 'events'
BPF_PERF_OUTPUT(events);

int hello(struct pt_regs *ctx) {
    // Creates an empty data_t struct that we'll then populate
    struct data_t data = {};

    // Returns PID in the lower 32 bits, and TGID in the upper 32 bits
    // By directly setting this to a u32, we discard the upper 32 bits
    // For a multi-threaded app, the TGID will be the same 
    data.pid = bpf_get_current_pid_tgid();
    data.ts = bpf_ktime_get_ns();
    
    // Populates the first argument address with the current process name
    bpf_get_current_comm(&data.comm, sizeof(data.comm));
    
    // Submits the event for userspace to read via a perf ring buffer 
    events.perf_submit(ctx, &data, sizeof(data));

    return 0;
}
"""


def print_event(cpu, data, size):
    """Handles reading events from the events stream"""
    global start
    # Gets the event as a python object, auto-generated from the C declaration
    event = b['events'].event(data)
    if start == 0:
        start = event.ts
    time_s = (float(event.ts - start)) / 1e9
    print('%-18.9f %-16s %-6d %s' % (time_s, event.comm, event.pid, 'Hello, perf_output!'))


if __name__ == '__main__':

    b = BPF(text=prog)
    b.attach_kprobe(event=b.get_syscall_fnname('clone'), fn_name='hello')

    start = 0
    print('%-18s %-16s %-6s %s' % ('TIME(s)', 'COMM', 'PID', 'MESSAGE'))

    b['events'].open_perf_buffer(print_event)
    while True:
        b.perf_buffer_poll()
