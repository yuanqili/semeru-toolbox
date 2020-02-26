#include <linux/mm.h>

BPF_HASH(region, u64, u64);

int kprobe__handle_mm_fault(struct pt_regs *ctx,
                            struct vm_area_struct *vma,
                            unsigned long address,
                            unsigned int flags)
{
    u32 pid = bpf_get_current_pid_tgid();
    {{FILTER_PID}}

    u64 address_256mb, *ratio, zero = 0;
    address_256mb = address >> 28 << 28;
    ratio = region.lookup_or_try_init(&address_256mb, &zero);
    if (ratio)
        (*ratio)++;

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

    u64 address_256mb, *ratio, zero = 0;
    address_256mb = address >> 28 << 28;
    ratio = region.lookup_or_try_init(&address_256mb, &zero);
    if (ratio && *ratio > 0)
        (*ratio)--;

    return 0;
}
