/**
 * darija_runtime.h - DarijaLang Runtime Support (Phase 5)
 * 
 * Provides declarations for runtime functions used by DarijaLang programs.
 */

#ifndef DARIJA_RUNTIME_H
#define DARIJA_RUNTIME_H

#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <setjmp.h>

/* Define strdup for Windows environments that might not have it */
#ifdef _MSC_VER
#define strdup _strdup
#endif

/**
 * Type definitions and aliases for DarijaLang built-in types
 */
 
/* Boolean type for DarijaLang */
typedef int boolDarija;
#define bssa7 1      /* true */
#define machibssa7 0  /* false */

/* Exception handling support */
#define MAX_EXCEPTION_HANDLERS 32
extern jmp_buf __darija_jmp_buf[MAX_EXCEPTION_HANDLERS];
extern int __darija_handler_idx;
extern char* __darija_current_exception;

/* Push/pop exception handlers */
void __darija_push_handler(int id);
void __darija_pop_handler();
void __darija_throw(const char* message);

/* Runtime function declarations */

/**
 * tba3 - Print an integer value
 */
void tba3(int value);

/**
 * tba3_str - Print a string
 */
void tba3_str(const char* s);

/**
 * 9rahadi - Read an integer from stdin
 * Returns the integer value read
 */
int _9rahadi();

/**
 * _darija_exit - Exit the program with the specified code
 */
void _darija_exit(int code);

#endif /* DARIJA_RUNTIME_H */
