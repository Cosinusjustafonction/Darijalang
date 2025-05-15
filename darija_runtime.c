/* Define _DEFAULT_SOURCE for strdup availability with glibc */
#define _DEFAULT_SOURCE 
/* Enable features in POSIX standard - needed for strdup */
#define _POSIX_C_SOURCE 200809L

/* To ensure strdup is defined on windows */
#ifdef _WIN32
#define _CRT_SECURE_NO_WARNINGS
#endif

/**
 * darija_runtime.c - DarijaLang Runtime Support (Phase 5)
 * 
 * Implements runtime functions used by DarijaLang programs.
 */

#include "darija_runtime.h"
#include <string.h>  // Add this for string functions including strdup

/* Exception handling globals */
jmp_buf __darija_jmp_buf[MAX_EXCEPTION_HANDLERS];
int __darija_handler_idx = 0;
char* __darija_current_exception = NULL;

/* Push exception handler to the stack */
void __darija_push_handler(int id) {
    if (__darija_handler_idx < MAX_EXCEPTION_HANDLERS) {
        __darija_handler_idx++;
    } else {
        fprintf(stderr, "Error: Too many nested try blocks\n");
        exit(1);
    }
}

/* Pop exception handler from the stack */
void __darija_pop_handler() {
    if (__darija_handler_idx > 0) {
        __darija_handler_idx--;
    }
}

/* Throw an exception */
void __darija_throw(const char* message) {
    if (__darija_handler_idx > 0) {
        /* Store the exception message - use a custom safe_strdup if needed */
        #ifdef _MSC_VER  /* For Microsoft Visual C++ */
        __darija_current_exception = _strdup(message);
        #else
        __darija_current_exception = strdup(message);  /* Note: this leaks memory */
        #endif
        
        /* Jump to the nearest catch block */
        longjmp(__darija_jmp_buf[__darija_handler_idx - 1], 1);
    } else {
        /* Uncaught exception */
        fprintf(stderr, "Uncaught exception: %s\n", message);
        exit(1);
    }
}

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
