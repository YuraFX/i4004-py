// Test 5: Check decimal correction (DAA) when working with binary-coded decimal numbers
ORG 0x000
    LDM 8
    XCH R0
    LDM 8
    ADD R0           // 8 + 8 = 16. In 4 bits this is 0, CY flag = 1.
    DAA              // Adds 6: ACC = 6, CY remains 1.
    HLT