#include "darija_runtime.h"

/* Generated C code from DarijaLang */

int factorial(int n) {
    int t1;
    int t3;
    int t2;
    int t0;

    t0 = n <= 1;
    if (!t0) goto endif2;
then0: ;
    return 1;
endif2: ;
    t1 = n - 1;
    t2 = factorial(t1);
    t3 = n * t2;
    return t3;
}

int bda(void) {
    int result;
    int t2;
    int t1;
    int t0;

    t0 = factorial(5);
    result = t0;
    tba3_str("Factorial of 5:");
    tba3(result);
    return 0;
}


/* Main stub for program entry */
int main(void) {
    return bda();
}
