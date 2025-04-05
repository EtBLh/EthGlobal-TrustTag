#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <err.h>
#include <tee_client_api.h>
#include <bts_voting_ta.h>

#define MAX_JSON_SIZE 65536  // 最多支援 64KB JSON

int main(int argc, char *argv[]) {
    if (argc < 3) {
        fprintf(stderr, "❗ 使用方式:\n");
        fprintf(stderr, "  %s process_vote '{...json...}'\n", argv[0]);
        fprintf(stderr, "  %s decrypt_label '{...json...}'\n", argv[0]);
        fprintf(stderr, "  %s process_vote -   # 從 stdin 讀取 JSON\n", argv[0]);
        return 1;
    }

    const char *mode = argv[1];
    const char *json_arg = argv[2];

    char *json_input_buf = malloc(MAX_JSON_SIZE);
    if (!json_input_buf) {
        fprintf(stderr, "❗ 無法分配記憶體\n");
        return 1;
    }
    memset(json_input_buf, 0, MAX_JSON_SIZE);

    if (strcmp(json_arg, "-") == 0) {
        size_t read_len = fread(json_input_buf, 1, MAX_JSON_SIZE - 1, stdin);
        if (read_len == 0) {
            fprintf(stderr, "❗ 無法從 stdin 讀取任何資料\n");
            free(json_input_buf);
            return 1;
        }
        json_input_buf[read_len] = '\0';  // <<<< 加上這行！
    } else {
        strncpy(json_input_buf, json_arg, MAX_JSON_SIZE - 1);
    }
    
    // 實際 JSON 長度
    size_t json_len = strlen(json_input_buf);

    TEEC_Result res;
    TEEC_Context ctx;
    TEEC_Session sess;
    TEEC_Operation op;
    TEEC_UUID uuid = TA_BTS_VOTING_UUID;
    uint32_t err_origin;
    uint32_t cmd_id;

    if (strcmp(mode, "process_vote") == 0) {
        cmd_id = CMD_PROCESS_VOTE;
    } else if (strcmp(mode, "decrypt_label") == 0) {
        cmd_id = CMD_DECRYPT_LABEL;
    } else {
        fprintf(stderr, "❗ 不支援的模式：%s\n", mode);
        free(json_input_buf);
        return 1;
    }

    res = TEEC_InitializeContext(NULL, &ctx);
    if (res != TEEC_SUCCESS)
        errx(1, "TEEC_InitializeContext failed: 0x%x", res);

    res = TEEC_OpenSession(&ctx, &sess, &uuid,
                           TEEC_LOGIN_PUBLIC, NULL, NULL, &err_origin);
    if (res != TEEC_SUCCESS)
        errx(1, "TEEC_OpenSession failed: 0x%x origin: 0x%x", res, err_origin);

    memset(&op, 0, sizeof(op));
    op.paramTypes = TEEC_PARAM_TYPES(
        TEEC_MEMREF_TEMP_INPUT,
        TEEC_MEMREF_TEMP_OUTPUT,
        TEEC_NONE,
        TEEC_NONE
    );
    op.params[0].tmpref.buffer = json_input_buf;
    op.params[0].tmpref.size   = json_len;

    char output_buf[MAX_JSON_SIZE] = {0};
    op.params[1].tmpref.buffer = output_buf;
    op.params[1].tmpref.size   = sizeof(output_buf);

    res = TEEC_InvokeCommand(&sess, cmd_id, &op, &err_origin);
    if (res != TEEC_SUCCESS)
        errx(1, "TEEC_InvokeCommand failed: 0x%x origin: 0x%x", res, err_origin);

    //printf("Json 輸入：\n%s\n", json_input_buf);
    //printf("✅ TA 輸出：\n%s\n", output_buf);
    printf("%s", output_buf);

    TEEC_CloseSession(&sess);
    TEEC_FinalizeContext(&ctx);
    free(json_input_buf);
    return 0;
}
