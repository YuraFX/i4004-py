// Test subtraction and the specifics of the Borrow flag in the Intel 4004 architecture
ORG 0x000
    LDM 5
    XCH R0
    LDM 9
    SUB R0
    HLT