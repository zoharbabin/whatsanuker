import axios from 'axios';
import fs from 'fs';
import path from 'path';

const logDir = './logs';
if (!fs.existsSync(logDir)) fs.mkdirSync(logDir);
function log(entry) {
  const file = path.join(logDir, `bot-${new Date().toISOString().slice(0,10)}.jsonl`);
  fs.appendFileSync(file, JSON.stringify(entry) + '\n');
}

async function start() {
  const { Client, LocalAuth } = await import('whatsapp-web.js');
  const client = new Client({
    authStrategy: new LocalAuth(),
    puppeteer: { headless: true }
  });

  client.on('qr', qr => console.log('QR', qr));
  client.on('ready', () => console.log('WA client ready'));

  async function checkRequests() {
    try {
      const community = await client.getChatById(process.env.COMMUNITY_ID);
      const requests = await community.getMembershipRequests();
      for (const req of requests) {
        const t0 = Date.now();
        const { data } = await axios.post(`${process.env.LLM_URL}/vet_join`, {
          name: req.sender?.pushname || '',
          note: req.requestMessage || ''
        });
        if (data.decision === 'approve') {
          await community.approveGroupMembershipRequests([req.id]);
          await client.sendMessage(process.env.LOBBY_ID, 'Welcome!');
        } else {
          await community.rejectGroupMembershipRequests([req.id]);
        }
        log({ ts: Date.now(), type: 'join', contact: req.id, decision: data.decision, reason: data.reason, latency_ms: Date.now()-t0 });
      }
    } catch (e) {
      log({ ts: Date.now(), type: 'join', contact: '-', decision: 'error', reason: e.message });
    }
  }

  setInterval(checkRequests, 45000);

  client.on('message_create', async msg => {
    if (msg.id.fromMe) return;
    try {
      const t0 = Date.now();
      const { data } = await axios.post(`${process.env.LLM_URL}/vet_message`, {
        body: msg.body,
        author: msg.from
      });
      if (data.is_spam) {
        await msg.delete(true);
        const chat = await msg.getChat();
        await chat.removeParticipants([msg.author || msg.from]);
      }
      log({ ts: Date.now(), type: 'message', contact: msg.from, decision: data.is_spam ? 'delete' : 'keep', reason: data.reason, latency_ms: Date.now()-t0 });
    } catch (e) {
      log({ ts: Date.now(), type: 'message', contact: msg.from, decision: 'keep', reason: e.message });
    }
  });

  client.initialize();
}

if (process.env.NODE_ENV !== 'test') {
  start();
}

export { log };
