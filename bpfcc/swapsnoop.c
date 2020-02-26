#include <linux/mm.h>

struct page_in_t {
    u32 pid;
    u64 ts;
    u64 address;
};

struct page_out_t {
    u32 pid;
    u64 ts;
    u64 address;
};

BPF_HASH(start, u32);
BPF_HISTOGRAM(fault_dist);
BPF_PERF_OUTPUT(page_in);
BPF_PERF_OUTPUT(page_out);

int kprobe__handle_mm_fault(struct pt_regs *ctx,
                            struct vm_area_struct *vma,
                            unsigned long address,
                            unsigned int flags)
{
    struct page_in_t stat = {};

    stat.pid = bpf_get_current_pid_tgid();
    stat.ts = bpf_ktime_get_ns();
    stat.address = address;

    start.update(&stat.pid, &stat.ts);
    page_in.perf_submit(ctx, &stat, sizeof(stat));

    return 0;
}

int kretprobe__handle_mm_fault(struct pt_regs *ctx)
{
    u32 pid;
    u64 *tsp, delta;

    pid = bpf_get_current_pid_tgid();
    tsp = start.lookup(&pid);
    if (tsp) {
        delta = bpf_ktime_get_ns() - *tsp;
        fault_dist.increment(bpf_log2l(delta));
        start.delete(&pid);
    }

    return 0;
}

int kprobe__try_to_unmap_one(struct pt_regs *ctx,
                             struct page *page,
                             struct vm_area_struct *vma,
                             unsigned long address,
                             void *arg)
{
    struct page_out_t stat = {};

    stat.pid = bpf_get_current_pid_tgid();
    stat.ts = bpf_ktime_get_ns();
    stat.address = address;

    page_out.perf_submit(ctx, &stat, sizeof(stat));

    return 0;
}
