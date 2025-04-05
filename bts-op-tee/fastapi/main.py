from fastapi import FastAPI, HTTPException, UploadFile, File, Form
from pydantic import BaseModel
import socket
import json
import os
from ecdsa import SigningKey, VerifyingKey, NIST256p
import base64

app = FastAPI()

SHARED_FOLDER = "/optee_2/shared_folder"

# ====== 固定 ECDSA 密鑰對（開機就產生一次） ======
PRIVATE_KEY = SigningKey.generate(curve=NIST256p)
PUBLIC_KEY = PRIVATE_KEY.get_verifying_key()

# ====== API: 上傳 JSON 檔案 ======
@app.post("/upload")
def upload_json(file: UploadFile = File(...), filename: str = Form(...)):
    if not filename.endswith(".json"):
        raise HTTPException(status_code=400, detail="Filename must end with .json")

    file_path = os.path.join(SHARED_FOLDER, filename)

    try:
        with open(file_path, "wb") as f:
            content = file.file.read()
            f.write(content)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to save file: {str(e)}")

    return {"message": f"File '{filename}' uploaded successfully."}

# ====== API: 提供公開金鑰 ======
@app.get("/pubkey")
def get_pubkey():
    return {
        "curve": "NIST256p",
        "format": "hex",
        "public_key": PUBLIC_KEY.to_string().hex()
    }

# ====== Guest 命令執行器 ======
def run_in_guest(command: str) -> str:
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.settimeout(3)
            s.connect(("127.0.0.1", 6000))
            s.sendall((command + "\n").encode())
            output = s.recv(4096)
            return output.decode()
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to run command in guest: {str(e)}")

# ====== API: 呼叫 BTS 計算並簽章 ======
@app.post("/vote")
def run_bts_voting(json_file_name: str):
    command = f"cat {json_file_name} | optee_example_bts_voting process_vote -"
    output = run_in_guest(command) + "}"

    try:
        parsed = json.loads(output)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Invalid JSON: {str(e)}")

    # 把原始資料（去掉 signature）拿來簽章
    payload = dict(parsed)
    signature_input = dict(payload)
    signature_input.pop("signature", None)
    message_bytes = json.dumps(signature_input, sort_keys=True).encode()

    signature = PRIVATE_KEY.sign(message_bytes)
    signature_b64 = base64.b64encode(signature).decode()

    # 回傳附帶 signature（以 base64 格式）
    payload["signature"] = signature_b64
    return {"result": payload}

