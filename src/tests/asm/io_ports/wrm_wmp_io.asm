// Check independent writes to RAM (WRM) and IO ports (WMP)
ORG 0x000
    FIM P0 0x00      // Set up address: register 0, character 0
    SRC P0           // Send the address to memory
    LDM 5
    WRM              // Write 5 to RAM (visible in Memory)
    LDM 7
    WMP              // Write 7 to IO (visible in Port 0)
    HLT