// Test 6: Check subroutine calls and the operation of the 3-level stack (JMS and BBL)
ORG 0x000
    JMS sub1         // Call the subroutine (saves the return address on the stack)
    LDM 1            // We return here after BBL
    HLT              // Halt the processor
sub1:
    LDM 2            // Subroutine body
    BBL 0            // Return from the subroutine