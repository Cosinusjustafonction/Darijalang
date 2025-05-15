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

/**
 * Type definitions and aliases for DarijaLang built-in types
 */
 
/* Boolean type for DarijaLang */
typedef int boolDarija;
#define bssa7 1      /* true */
#define machibssa7 0  /* false */

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
