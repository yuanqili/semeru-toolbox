#include <iostream>
#include "ratio.h"


double pages_inmem_ratio(pid_t pid, unsigned long addr_start, unsigned long addr_end)
{
    std::string pagemap_path = "/proc/" + std::to_string(pid) + "/pagemap";
    unsigned long num_pages = (addr_end - addr_start) / 0x1000;

    FILE *pagemap = fopen(pagemap_path.c_str(), "rb");
    if (!pagemap) {
        std::cerr << "cannot open " << pagemap_path << std::endl;
        return -1;
    }

    uint64_t base_offset = addr_start / PAGE_SIZE * PAGEMAP_ENTRY;
    int status = fseek(pagemap, base_offset, SEEK_SET);
    if (status) {
        std::cerr << "cannot seek to " << base_offset << std::endl;
        return -1;
    }

    unsigned long num_pages_in = 0;
    unsigned long num_pages_swapped = 0;

    for (int j = 0; j < num_pages; j++) {
        uint64_t read_val = 0;
        unsigned char c_buf[PAGEMAP_ENTRY];
        for (int i = 0; i < PAGEMAP_ENTRY; i++) {
            int c = getc(pagemap);
            auto idx = i ? IS_BIG_ENDIAN : PAGEMAP_ENTRY - i - 1;
            c_buf[idx] = c;
        }
        for (unsigned char i : c_buf) {
            read_val = (read_val << 8) + i;
        }
        if (PG_PRESENT(read_val)) num_pages_in++;
        if (PG_SWAPPED(read_val)) num_pages_swapped++;
    }

    fclose(pagemap);
    return double(num_pages_in) / num_pages;
}
