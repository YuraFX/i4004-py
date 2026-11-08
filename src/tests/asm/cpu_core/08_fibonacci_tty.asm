// =================================================================
// Computing and printing Fibonacci numbers to Teletype
// =================================================================
ORG 0x000

    // --- 1. UART initialization ---
    FIM P7 0xE0       
    SRC P7
    LDM 13            
    WMP

    // --- 2. Initialization ---
    LDM 0
    XCH R0            // R0 = 0
    LDM 1
    XCH R1            // R1 = 1
    LDM 8
    XCH R2            // Counter (8 numbers)

LOOP:
    // --- 3. Output the current number ---
    LD R0
    JMS PRINT_HEX     

    // Print a comma and a space
    LDM 0x2C
    XCH R3
    LDM 0x02
    XCH R4
    JMS UART_SEND

    LDM 0x20
    XCH R3
    LDM 0x02
    XCH R4
    JMS UART_SEND

    // --- 4. Compute the next number ---
    LD R1             // ACC = R1
    CLC               // <--- IMPORTANT: Clear carry before addition!
    ADD R0            // ACC = R1 + R0 + 0
    XCH R1            // R1 = new number
    XCH R0            // R0 = old R1

    // --- 5. Repeat the loop ---
    ISZ R2 LOOP
    NOP

    // --- 6. Finish the line ---
    LDM 0x0D
    XCH R3
    LDM 0x00
    XCH R4
    JMS UART_SEND

    LDM 0x0A
    XCH R3
    LDM 0x00
    XCH R4
    JMS UART_SEND

    HLT

// =================================================================
// SUBROUTINE: Print a number (0-13) in Hex format
// =================================================================
PRINT_HEX:
    XCH R3            // R3 = number
    LDM 10
    XCH R4            // R4 = 10
    LD R3
    CLC               // <--- FIXED: Clear carry before subtraction
    SUB R4            // ACC = R3 - 10
    JCN C HEX_BRANCH  // If R3 >= 10, go to the HEX branch

    // DECIMAL (0-9)
    LDM 3             // Base for '0' (0x30)
    XCH R4
    JMS UART_SEND
    BBL 0

HEX_BRANCH:
    // HEX (10-15 -> A-F)
    LDM 9
    XCH R4
    LD R3
    CLC               // <--- FIXED: Clear carry before the second subtraction
    SUB R4            // ACC = R3 - 9 (for 13 this gives 4)
    XCH R3            // R3 = low nibble (A=1, B=2, C=3, D=4)
    LDM 4             // Base for 'A' (0x40)
    XCH R4
    JMS UART_SEND
    BBL 0

// =================================================================
// SUBROUTINE: Send a character via UART
// =================================================================
UART_SEND:
WAIT_TBMT:
    FIM P7 0xD0       
    SRC P7
    RDM
    JCN Z WAIT_TBMT   

    FIM P7 0xC0       
    SRC P7
    LD R3
    WMP               
    LD R4
    WMP               
    BBL 0