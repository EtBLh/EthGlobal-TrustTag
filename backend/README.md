1. TEST
2. 部署


pip install -r requirements.txt



'''
DB_SCHEMA
// 1) proposals collection
{
  "_id": "string (proposalId)",
  "address": "string",
  "description": "string",              // description in contract
  "malicious": "bool",
  "deadline": "Date",
  "tx_hash": "string",
  "created_at": "Date"
  "updated_at": "Date",
}

// 2. rewards collection
{
  "_id": "string",
  "address": "string",
  "proposal_id": "string",
  "amount": "number",
  "tx_hash": "string",       // on‐chain claim tx
  "claimed_at": "Date"
}

// 3. votes collection
{
  "_id": "string",
  "address": "string",
  "proposal_id": "string",
  "vote": boolean
  "prediction": yes的趴數, 0~100 
}
'''