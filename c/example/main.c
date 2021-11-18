#include <stdio.h>

#include "norm.h"

int main (int argc, char **argv) {
    if (argc < 2) {
        printf("nothing to normalize\n");
        return 1;
    }

    const char *normalized;
    char *z = argv[1];

    normalized = normalize_username(z);

    printf("%s\n", normalized);

    free((char*)normalized);

    return 0;
}
