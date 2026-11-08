ORG 0x000

    // 1. UART initialization (Chip 3, Register 14)
    FIM P0 0xE0      
    SRC P0           
    LDM 13           // 0x0D (8 bits, no parity)
    WMP              

    // 2. 'H' (72 = 0x48)
WAIT_H:
    FIM P0 0xD0
    SRC P0
    RDM
    JCN Z WAIT_H
    FIM P0 0xC0
    SRC P0
    LDM 8            // Low nibble
    WMP
    LDM 4            // High nibble
    WMP

    // 3. 'e' (101 = 0x65)
WAIT_e1:
    FIM P0 0xD0
    SRC P0
    RDM
    JCN Z WAIT_e1
    FIM P0 0xC0
    SRC P0
    LDM 5
    WMP
    LDM 6
    WMP

    // 4. 'l' (108 = 0x6C)
WAIT_l1:
    FIM P0 0xD0
    SRC P0
    RDM
    JCN Z WAIT_l1
    FIM P0 0xC0
    SRC P0
    LDM 12
    WMP
    LDM 6
    WMP

    // 5. 'l' (108 = 0x6C)
WAIT_l2:
    FIM P0 0xD0
    SRC P0
    RDM
    JCN Z WAIT_l2
    FIM P0 0xC0
    SRC P0
    LDM 12
    WMP
    LDM 6
    WMP

    // 6. 'o' (111 = 0x6F)
WAIT_o1:
    FIM P0 0xD0
    SRC P0
    RDM
    JCN Z WAIT_o1
    FIM P0 0xC0
    SRC P0
    LDM 15
    WMP
    LDM 6
    WMP

    // 7. Space ' ' (32 = 0x20)
WAIT_SPACE:
    FIM P0 0xD0
    SRC P0
    RDM
    JCN Z WAIT_SPACE
    FIM P0 0xC0
    SRC P0
    LDM 0
    WMP
    LDM 2
    WMP

    // 8. 'W' (87 = 0x57)
WAIT_W:
    FIM P0 0xD0
    SRC P0
    RDM
    JCN Z WAIT_W
    FIM P0 0xC0
    SRC P0
    LDM 7
    WMP
    LDM 5
    WMP

    // 9. 'o' (111 = 0x6F)
WAIT_o2:
    FIM P0 0xD0
    SRC P0
    RDM
    JCN Z WAIT_o2
    FIM P0 0xC0
    SRC P0
    LDM 15
    WMP
    LDM 6
    WMP

    // 10. 'r' (114 = 0x72)
WAIT_r:
    FIM P0 0xD0
    SRC P0
    RDM
    JCN Z WAIT_r
    FIM P0 0xC0
    SRC P0
    LDM 2
    WMP
    LDM 7
    WMP

    // 11. 'l' (108 = 0x6C)
WAIT_l3:
    FIM P0 0xD0
    SRC P0
    RDM
    JCN Z WAIT_l3
    FIM P0 0xC0
    SRC P0
    LDM 12
    WMP
    LDM 6
    WMP

    // 12. 'd' (100 = 0x64)
WAIT_d:
    FIM P0 0xD0
    SRC P0
    RDM
    JCN Z WAIT_d
    FIM P0 0xC0
    SRC P0
    LDM 4
    WMP
    LDM 6
    WMP

    // 13. '!' (33 = 0x21)
WAIT_EXCL:
    FIM P0 0xD0
    SRC P0
    RDM
    JCN Z WAIT_EXCL
    FIM P0 0xC0
    SRC P0
    LDM 1
    WMP
    LDM 2
    WMP

    // 14. CR (Carriage Return, 13 = 0x0D)
WAIT_CR:
    FIM P0 0xD0
    SRC P0
    RDM
    JCN Z WAIT_CR
    FIM P0 0xC0
    SRC P0
    LDM 13
    WMP
    LDM 0
    WMP

    // 15. LF (Line Feed, 10 = 0x0A)
WAIT_LF:
    FIM P0 0xD0
    SRC P0
    RDM
    JCN Z WAIT_LF
    FIM P0 0xC0
    SRC P0
    LDM 10
    WMP
    LDM 0
    WMP

    HLT