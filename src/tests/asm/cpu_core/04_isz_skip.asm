// Test 4: Check the ISZ instruction (increment with skipping the next instruction when it wraps to zero)
ORG 0x000
    LDM 15
    XCH R0           // R0 = 15 (0x0F)
    ISZ R0 target    // R0 will become 0, and the next instruction will be skipped
    LDM 99           // This instruction should be skipped
target:
    LDM 7            // Executed after the skip
    HLT