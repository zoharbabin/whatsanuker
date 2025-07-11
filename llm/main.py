import os
import json
import time
import datetime
from fastapi import FastAPI
from pydantic import BaseModel
import litellm
import pathlib

app = FastAPI()
log_dir = './logs'
pathlib.Path(log_dir).mkdir(exist_ok=True)

class JoinReq(BaseModel):
    name: str
    note: str

class MsgReq(BaseModel):
    author: str
    body: str

def load_policy():
    policy_path = pathlib.Path(__file__).parent / 'policy.md'
    with open(policy_path, 'r') as f:
        return f.read()

def log(entry):
    file = os.path.join(log_dir, f'llm-{datetime.date.today().isoformat()}.jsonl')
    with open(file, 'a') as fh:
        fh.write(json.dumps(entry) + '\n')

async def ask_llm(system_prompt, user_prompt):
    start = time.time()
    try:
        resp = litellm.completion(
            model=os.getenv('MODEL_ID'),
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            temperature=0.0,
            max_tokens=120
        )
        txt = resp['choices'][0]['message']['content']
        data = json.loads(txt)
        fallback = False
    except Exception:
        data = {"decision": "reject", "reason": "parse error"}
        fallback = True
    latency = int((time.time() - start) * 1000)
    data['latency_ms'] = latency
    data['fallback'] = fallback
    return data

@app.post('/vet_join')
async def vet_join(req: JoinReq):
    policy = load_policy()
    system = f"Policy:\n{policy}\nReturn JSON with decision approve/reject and reason."
    user = f"Name: {req.name}\nNote: {req.note}"
    data = await ask_llm(system, user)
    log({"ts": int(time.time()*1000), "type": "join", "contact": req.name, "decision": data.get('decision'), "reason": data.get('reason'), "latency_ms": data.get('latency_ms'), "fallback": data.get('fallback')})
    return {"decision": data.get('decision'), "reason": data.get('reason')}

@app.post('/vet_message')
async def vet_message(req: MsgReq):
    policy = load_policy()
    system = f"Policy:\n{policy}\nReturn JSON with is_spam true/false and reason."
    user = f"Message: {req.body}"
    data = await ask_llm(system, user)
    log({"ts": int(time.time()*1000), "type": "message", "contact": req.author, "decision": data.get('is_spam'), "reason": data.get('reason'), "latency_ms": data.get('latency_ms'), "fallback": data.get('fallback')})
    return {"is_spam": data.get('is_spam', False), "reason": data.get('reason')}
