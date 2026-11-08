// Test addition and the Carry flag on 4-bit register overflow
ORG 0x000
    LDM 15
    XCH R0
    LDM 2
    ADD R0
    HLT