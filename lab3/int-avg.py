#!/usr/bin/python

import symex.z3str
import z3

## Construct two 32-bit integer values.  Do not change this code.
a = z3.BitVec('a', 32)
b = z3.BitVec('b', 32)

## Compute the average of a and b.  The initial computation we provided
## naively adds them and divides by two, but that is not correct.  Modify
## these lines to implement your solution for both unsigned (u_avg) and
## signed (s_avg) division.
##
## Watch out for the difference between signed and unsigned integer
## operations.  For example, the Z3 expression (x/2) performs signed
## division, meaning it treats the 32-bit value as a signed integer.
## Similarly, (x>>16) shifts x by 16 bits to the right, treating it
## as a signed integer.
##
## Use z3.UDiv(x, y) for unsigned division of x by y.
## Use z3.LShR(x, y) for unsigned (logical) right shift of x by y bits.
u_avg = z3.UDiv(a + b, 2)
s_avg = (a + b) / 2

## Do not change the code below.
# u_avg = a|b-(z3.LShR(a^b, 1)) failed!

# first div each integer,also with remainder,finally plus them
u_avg = z3.UDiv(a, 2) + z3.UDiv(b, 2) + (a%2+b%2)/2
# approach2: from hack's delight
u_avg = (a & b) + z3.LShR((a ^ b), 1)

#failed!
#s_avg = a/2 + b/2 + (((-1)*(a%2) if (a>>31==1) else (a%2))+((-1)*(b%2) if (b>>31==1) else (b%2)))/2
#s_avg = a/2 + b/2 + (a>>31+b>>31)/2
 
# from hack's delight again
s_avg = (a & b) + ((a ^ b) >> 1) 
s_avg = s_avg + (z3.LShR(s_avg, 31) & (a ^ b))

## To compute the reference answers, we extend both a and b by one
## more bit (to 33 bits), add them, divide by two, and shrink back
## down to 32 bits.  You are not allowed to "cheat" in this way in
## your answer.
az33 = z3.ZeroExt(1, a)
bz33 = z3.ZeroExt(1, b)
real_u_avg = z3.Extract(31, 0, z3.UDiv(az33 + bz33, 2))

as33 = z3.SignExt(1, a)
bs33 = z3.SignExt(1, b)
real_s_avg = z3.Extract(31, 0, (as33 + bs33) / 2)

def do_check(msg, e):
    print "Checking", msg, "using Z3 expression:"
    print "    " + str(e).replace("\n", "\n    ")
    solver = z3.Solver()
    solver.add(e)
    ok = solver.check()
    print "  Answer for %s: %s" % (msg, ok)

    if ok == z3.sat:
        m = solver.model()
        print "  Example solution:", m

do_check("unsigned avg", u_avg != real_u_avg)
do_check("signed avg", s_avg != real_s_avg)
