#include <linux/mm.h>

struct page_in_t {
    u64 address;
};

struct page_out_t {
    u64 address;
};

BPF_PERF_OUTPUT(page_in);
BPF_PERF_OUTPUT(page_out);

int kprobe__handle_mm_fault(struct pt_regs *ctx,
                            struct vm_area_struct *vma,
                            unsigned long address,
                            unsigned int flags)
{
    u32 pid = bpf_get_current_pid_tgid();
    {{FILTER_PID}}

    struct page_in_t stat = {};
    stat.address = address;
    page_in.perf_submit(ctx, &stat, sizeof(stat));
    return 0;
}

int kprobe__try_to_unmap_one(struct pt_regs *ctx,
                             struct page *page,
                             struct vm_area_struct *vma,
                             unsigned long address,
                             void *arg)
{
    u32 pid = bpf_get_current_pid_tgid();
    {{FILTER_PID}}

    struct page_out_t stat = {};
    stat.address = address;
    page_out.perf_submit(ctx, &stat, sizeof(stat));
    return 0;
}
