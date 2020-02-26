#include <linux/mm.h>

BPF_HASH(page_in, u64, u64);
BPF_HASH(page_out, u64, u64);

int kprobe__handle_mm_fault(struct pt_regs *ctx,
                            struct vm_area_struct *vma,
                            unsigned long address,
                            unsigned int flags)
{
    u32 pid = bpf_get_current_pid_tgid();
    {{FILTER_PID}}

    u64 address_block, *count, zero = 0;
    u32 offset = {{OFFSET}};
    address_block = address >> offset << offset;
    count = page_in.lookup_or_try_init(&address_block, &zero);
    if (count)
        (*count)++;

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

    u64 address_block, *count, zero = 0;
    u32 offset = {{OFFSET}};
    address_block = address >> offset << offset;
    count = page_out.lookup_or_try_init(&address_block, &zero);
    if (count)
        (*count)++;

    return 0;
}
