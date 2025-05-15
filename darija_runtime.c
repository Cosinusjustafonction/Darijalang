/**
 * darija_runtime.c - DarijaLang Runtime Support (Phase 5)
 * 
 * Implements runtime functions used by DarijaLang programs.
 */

#include "darija_runtime.h"

/**
 * tba3 - Print an integer value
 */
void tba3(int value) {
    printf("%d\n", value);
}

/**
 * tba3_str - Print a string
 */
void tba3_str(const char* s) {
    if (s == NULL) {
        puts("null");
    } else {
        puts(s);
    }
}

/**
 * 9rahadi - Read an integer from stdin
 * Returns the integer value read
 */
int _9rahadi() {
    int value;
    if (scanf("%d", &value) != 1) {
        fprintf(stderr, "Error: failed to read integer input\n");
        return 0;
    }
    return value;
}

/**
 * _darija_exit - Exit the program with the specified code
 */
void _darija_exit(int code) {
    exit(code);
}
