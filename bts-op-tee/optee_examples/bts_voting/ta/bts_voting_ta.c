#include <tee_internal_api.h>
#include <tee_internal_api_extensions.h>
#include <string.h>
#include <bts_voting_ta.h>

#define LOG_I(fmt, ...) IMSG("[BTS_TA] " fmt, ##__VA_ARGS__)
#define LOG_D(fmt, ...) DMSG("[BTS_TA] " fmt, ##__VA_ARGS__)

typedef struct {
    char  user[64];
    char  vote[8];
    float prediction_yes;
    float prediction_no;
} VoterInfo;

static const char* find_json_key(const char *start, const char *key) {
    const char *p = start;
    size_t key_len = strlen(key);

    while ((p = strstr(p, key))) {
        if ((p == start || *(p - 1) == ',' || *(p - 1) == '{' || *(p - 1) == '\n') &&
            (*(p + key_len) == ':' || *(p + key_len) == ' ')) {
            p = strchr(p, ':');
            if (!p) return NULL;
            p++;
            while (*p == ' ' || *p == '\t' || *p == '\n') p++;
            return p;
        }
        p += key_len;
    }

    return NULL;
}

static int read_quoted_string(const char *p, char *dest, size_t dest_size) {
    while (*p && *p != '\"') p++;
    if (*p != '\"') return -1;
    p++;
    const char *start = p;
    while (*p && *p != '\"') p++;
    if (*p != '\"') return -1;

    size_t len = p - start;
    if (len >= dest_size) return -1;
    TEE_MemMove(dest, start, len);
    dest[len] = '\0';
    return 0;
}

static float atof_lite(const char *s) {
    float result = 0.0f;
    float decimal = 0.1f;
    int seen_dot = 0;

    while (*s == ' ' || *s == '\n' || *s == '\t') s++;

    while (*s) {
        if (*s == '.') {
            seen_dot = 1;
        } else if (*s >= '0' && *s <= '9') {
            if (!seen_dot) {
                result = result * 10.0f + (*s - '0');
            } else {
                result += (*s - '0') * decimal;
                decimal *= 0.1f;
            }
        } else {
            break;
        }
        s++;
    }

    return result;
}

static int parse_votes_json(const char *json, VoterInfo *voters, int max_voters) {
    LOG_I("開始呼叫 parse_votes_json");

    const char *votes_p = find_json_key(json, "\"votes\"");
    if (!votes_p) {
        LOG_I("找不到 \"votes\" key");
        return 0;
    }

    while (*votes_p && *votes_p != '[') votes_p++;
    if (!*votes_p) {
        LOG_I("找不到 '['");
        return 0;
    }
    votes_p++;

    int count = 0;
    while (count < max_voters) {
        while (*votes_p && *votes_p != '{') votes_p++;
        if (!*votes_p) break;
        votes_p++;

        const char *user_key = find_json_key(votes_p, "\"user\"");
        if (!user_key || read_quoted_string(user_key, voters[count].user, sizeof(voters[count].user)) < 0) {
            LOG_I("解析 user 出錯");
            break;
        }

        const char *vote_key = find_json_key(votes_p, "\"vote\"");
        if (!vote_key || read_quoted_string(vote_key, voters[count].vote, sizeof(voters[count].vote)) < 0) {
            LOG_I("解析 vote 出錯");
            break;
        }

        const char *py_key = find_json_key(votes_p, "\"prediction_yes\"");
        if (!py_key) {
            LOG_I("解析 prediction_yes 出錯");
            break;
        }
        voters[count].prediction_yes = atof_lite(py_key);
        LOG_I("prediction_yes = 0x%x", *((uint32_t*)&voters[count].prediction_yes));

        const char *pn_key = find_json_key(votes_p, "\"prediction_no\"");
        if (!pn_key) {
            LOG_I("解析 prediction_no 出錯");
            break;
        }
        voters[count].prediction_no = atof_lite(pn_key);

        LOG_I("投票者 %d: user=%s, vote=%s, prediction_yes=%f, prediction_no=%f",
              count, voters[count].user, voters[count].vote,
              voters[count].prediction_yes, voters[count].prediction_no);

        count++;

        while (*votes_p && *votes_p != '}') votes_p++;
        if (!*votes_p) break;
        votes_p++;

        while (*votes_p && (*votes_p == ',' || *votes_p == '\n' || *votes_p == ' ')) votes_p++;
        if (*votes_p == ']') break;
    }

    return count;
}

static void compute_bts_scores(const VoterInfo *voters, int num_voters, int *scores) {
    // 1. 計算實際比例
    int yes_count = 0;
    for (int i = 0; i < num_voters; i++) {
        if (strcmp(voters[i].vote, "yes") == 0)
            yes_count++;
    }
    float actual_yes_ratio = (float)yes_count / num_voters;

    LOG_I("實際 yes 比例: %d/%d = %d", yes_count, num_voters, (int)(actual_yes_ratio * 10000));

    // 2. 計算每個人的預測準確性（越接近 actual_yes_ratio 越好）
    for (int i = 0; i < num_voters; i++) {
        float pred_yes = voters[i].prediction_yes;

        // score = 1 - abs(預測 - 真實)
        float accuracy_score = 1.0f - (pred_yes > actual_yes_ratio ?
                                       (pred_yes - actual_yes_ratio) :
                                       (actual_yes_ratio - pred_yes));

        // 再乘上 100 當作整數分數
        int score = (int)(accuracy_score * 100.0f);

        // 👇 這裡還沒加入 information gain（可後續擴充）
        scores[i] = score;

        LOG_I("user=%s, score=%d", voters[i].user, scores[i]);
    }
}

#define MAX_VOTERS 1000

/*
 * 安全拼接函式：
 * 將 src 拷貝到 dest 目前字串尾端，並手動補上 '\0'。
 * dest_size：dest 緩衝區的總大小（含結尾的空間）。
 */
static void safe_concat(char *dest, size_t dest_size, const char *src)
{
    size_t curr_len = strlen(dest);
    size_t src_len  = strlen(src);

    // 預留 1 byte 給 '\0'
    if (curr_len + src_len < dest_size - 1) {
        TEE_MemMove(dest + curr_len, src, src_len);
        dest[curr_len + src_len] = '\0';
    }
}

/*
 * 產出模擬簽名（真實實作要使用私鑰）：
 * 原先使用 strcat(buffer, ", ")，現在改用 safe_concat。
 */
static void fake_sign_result(char *buffer, size_t buf_len)
{
    const char *sep       = ", ";
    const char *signature = "\"signature\": \"FAKE_SIGNATURE_FROM_TA\"";

    // 先拼接 ", "
    safe_concat(buffer, buf_len, sep);

    // 再拼接 signature
    safe_concat(buffer, buf_len, signature);
}

static TEE_Result handle_process_vote(uint32_t param_types, TEE_Param params[4])
{
    const uint32_t expected =
        TEE_PARAM_TYPES(TEE_PARAM_TYPE_MEMREF_INPUT,
                        TEE_PARAM_TYPE_MEMREF_OUTPUT,
                        TEE_PARAM_TYPE_NONE,
                        TEE_PARAM_TYPE_NONE);

    if (param_types != expected)
        return TEE_ERROR_BAD_PARAMETERS;

    // 讀入 vote JSON
    const char *input = (const char *)params[0].memref.buffer;
    LOG_I("收到投票資料: %s", input);

    VoterInfo *voters = TEE_Malloc(sizeof(VoterInfo)*1000, TEE_MALLOC_FILL_ZERO);
    if (!voters) {
        LOG_I("TEE_Malloc voters 失敗");
        return TEE_ERROR_OUT_OF_MEMORY;
    }

    int num_voters = parse_votes_json(input, voters, MAX_VOTERS);

    if (num_voters < 0) {
        LOG_I("解析投票資料失敗");
        return TEE_ERROR_BAD_PARAMETERS;
    }
    LOG_I("解析到 %d 位投票者", num_voters);
    for (int i = 0; i < num_voters; i++) {
        LOG_I("投票者 %d: user=%s, vote=%s, prediction_yes=%d, prediction_no=%d",
            i, voters[i].user, voters[i].vote,
            (int)(voters[i].prediction_yes * 10000),
            (int)(voters[i].prediction_no * 10000));
    }

    int scores[MAX_VOTERS] = {0};
    compute_bts_scores(voters, num_voters, scores);

    char *output = (char *)params[1].memref.buffer;
    size_t max_len = params[1].memref.size;
    memset(output, 0, max_len);

    TEE_MemMove(output, "{\"user_scores\": {", 20);

    for (int i = 0; i < num_voters; i++) {
        char temp[128];
        snprintf(temp, sizeof(temp), "\"%s\": %d", voters[i].user, scores[i]);
        safe_concat(output, max_len, temp);

        if (i < num_voters - 1)
            safe_concat(output, max_len, ", ");
    }
    safe_concat(output, max_len, "}");

    fake_sign_result(output, max_len);
    params[1].memref.size = strlen(output);

    LOG_I("處理投票結果: %s", output);

    TEE_Free(voters);
    return TEE_SUCCESS;
}

static TEE_Result handle_decrypt_label(uint32_t param_types, TEE_Param params[4])
{
    const uint32_t expected =
        TEE_PARAM_TYPES(TEE_PARAM_TYPE_MEMREF_INPUT,
                        TEE_PARAM_TYPE_MEMREF_OUTPUT,
                        TEE_PARAM_TYPE_NONE,
                        TEE_PARAM_TYPE_NONE);

    if (param_types != expected)
        return TEE_ERROR_BAD_PARAMETERS;

    const char *input = (const char *)params[0].memref.buffer;
    LOG_I("收到 label 解密請求: %s", input);

    // 模擬解密結果
    const char *response = "{\"label\": \"decrypted_label_xyz\"}";

    // 寫入 output + 簽名
    char *output   = (char *)params[1].memref.buffer;
    size_t max_len = params[1].memref.size;
    memset(output, 0, max_len);

    TEE_MemMove(output, response, strlen(response));

    fake_sign_result(output, max_len);
    params[1].memref.size = strlen(output);


    return TEE_SUCCESS;
}

// TA lifecycle
TEE_Result TA_CreateEntryPoint(void)
{
    LOG_I("CreateEntryPoint");
    return TEE_SUCCESS;
}

void TA_DestroyEntryPoint(void)
{
    LOG_I("DestroyEntryPoint");
}

TEE_Result TA_OpenSessionEntryPoint(uint32_t param_types,
                                    TEE_Param __maybe_unused params[4],
                                    void __maybe_unused **sess_ctx)
{
    (void)param_types;
    LOG_I("OpenSession");
    return TEE_SUCCESS;
}

void TA_CloseSessionEntryPoint(void __maybe_unused *sess_ctx)
{
    LOG_I("CloseSession");
}

// Command Dispatcher
TEE_Result TA_InvokeCommandEntryPoint(void __maybe_unused *sess_ctx,
                                      uint32_t cmd_id,
                                      uint32_t param_types,
                                      TEE_Param params[4])
{
    switch (cmd_id) {
    case CMD_PROCESS_VOTE:
        return handle_process_vote(param_types, params);
    case CMD_DECRYPT_LABEL:
        return handle_decrypt_label(param_types, params);
    default:
        return TEE_ERROR_NOT_SUPPORTED;
    }
}
