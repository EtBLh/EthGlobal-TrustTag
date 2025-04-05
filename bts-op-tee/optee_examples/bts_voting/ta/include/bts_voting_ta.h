#ifndef BTS_VOTING_TA_H
#define BTS_VOTING_TA_H

// 產生一組唯一 UUID（用 uuidgen）
#define TA_BTS_VOTING_UUID { 0x6d4a9275, 0x41d6, 0x467a, \
    { 0x93, 0x0c, 0x9d, 0x73, 0x9e, 0x14, 0x05, 0x3f } }

// Command IDs
#define CMD_PROCESS_VOTE   0
#define CMD_DECRYPT_LABEL  1

#define MAX_VOTERS      1000
#define MAX_INPUT_LEN   65536
#define MAX_OUTPUT_LEN  65536

#endif // BTS_VOTING_TA_H