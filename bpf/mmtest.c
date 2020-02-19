#include <stdio.h>
#include <stdlib.h>
#include <unistd.h>
#include <sys/types.h>

#define SIZE_BASE (1l)
#define SIZE      (SIZE_BASE * 1024 * 1024 * 1024)
#define OFF_STEP  (8 * 1024)

int main(int argc, char **argv)
{
    pid_t pid = getpid();
    printf("pid: %d\n", pid);

    int *mem = (int*)malloc(SIZE * sizeof(int));
    if (mem == NULL) {
        printf("malloc() failed, exits\n");
        exit(1);
    } else {
        printf("malloc() allocated, starts\n");
    }

    printf("loop 1 is about to starting, press any key to continue...");
    getchar();

    for (unsigned long i = 0; i < SIZE; i++)
        mem[i] = 0;

    printf("loop 1 done, loop 2 is about to starting, press any key to continue...");
    getchar();

    for (unsigned int offset = 0; offset < OFF_STEP; offset++) {
        for (unsigned long i = offset; i < SIZE; i += OFF_STEP)
            mem[i] = 1;
    }

    printf("done");
    getchar();

    return 0;
}
