// Test 3: Check conditional jumps (JCN) by the zero (Z) and carry (C) flags
ORG 0x000
    LDM 0
    JCN Z label_z    // ACC = 0, the jump WILL BE TAKEN
    LDM 1            // Skipped
label_z:
    JCN C label_c    // CY = 0, the jump WILL NOT BE TAKEN
    LDM 2            // Executed
label_c:
    LDM 3            // Executed
    HLT