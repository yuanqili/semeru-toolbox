#include <iostream>
#include "ratio.h"


int main(int argc, char **argv)
{
    if (argc != 4) {
        std::cout << "usage: ./ratio <pid> <addr_start> <addr_end>" << std::endl;
        return -1;
    }
    auto pid = std::stoi(argv[1]);
    auto addr_start = std::stol(argv[2], nullptr, 16);
    auto addr_end = std::stol(argv[3], nullptr, 16);

    auto ratio = pages_inmem_ratio(pid, addr_start, addr_end);
    std::cout << ratio << std::endl;
    return 0;
}
