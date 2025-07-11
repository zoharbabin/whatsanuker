import assert from 'assert';
import fs from 'fs';
import path from 'path';
import { log } from '../index.js';

const today = new Date().toISOString().slice(0,10);
const file = path.join('./logs', `bot-${today}.jsonl`);
if (fs.existsSync(file)) fs.unlinkSync(file);
log({ts:0,type:'test',contact:'x',decision:'ok',reason:'test'});
const content = fs.readFileSync(file,'utf8');
assert.ok(content.includes('"decision":"ok"'));
