#include <linux/mm.h>


struct page_counts {
    u64 page_in;
    u64 page_out;
};
BPF_HASH(page_stats, u64, struct page_counts);

int kprobe__handle_mm_fault(struct pt_regs *ctx,
                            struct vm_area_struct *vma,
                            unsigned long address,
                            unsigned int flags)
{
    u32 pid = bpf_get_current_pid_tgid();
    {{FILTER_PID}}

    u64 address_block;
    u32 offset = {{OFFSET}};
    address_block = address >> offset << offset;

    struct page_counts *count, zero = {};
    count = page_stats.lookup_or_try_init(&address_block, &zero);
    if (count)
        count->page_in += 1;

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

    u64 address_block;
    u32 offset = {{OFFSET}};
    address_block = address >> offset << offset;

    struct page_counts *count, zero = {};
    count = page_stats.lookup_or_try_init(&address_block, &zero);
    if (count)
        count->page_out += 1;

    return 0;
}
