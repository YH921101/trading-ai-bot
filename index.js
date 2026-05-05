import express from "express";
import fetch from "node-fetch";

const app = express();
app.use(express.json());

const OPENAI_API_KEY = process.env.OPENAI_API_KEY;
const DISCORD_WEBHOOK = process.env.DISCORD_WEBHOOK_URL;

function buildPrompt(d) {
  return `
あなたは日本株の短期トレーダーです。
以下を簡潔に分析してください。

銘柄: ${d.symbol} ${d.name}
株価: ${d.price}
前日比: ${d.change}%
出来高倍率: ${d.vol_ratio}倍

① 状況
② 強さ（強い/普通/弱い）
③ 抵抗・支持
④ 判断（買い/様子見/見送り）
⑤ 注意点
`;
}

async function analyzeWithAI(data) {
  const res = await fetch("https://api.openai.com/v1/responses", {
    method: "POST",
    headers: {
      "Authorization": `Bearer ${OPENAI_API_KEY}`,
      "Content-Type": "application/json"
    },
    body: JSON.stringify({
      model: "gpt-5-mini",
      input: buildPrompt(data)
    })
  });

  const json = await res.json();
  return json.output?.[0]?.content?.[0]?.text || "分析失敗";
}

app.post("/webhook", async (req, res) => {
  const data = req.body;
  const analysis = await analyzeWithAI(data);

  await fetch(DISCORD_WEBHOOK, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      content: `📊 ${data.symbol}\n${analysis}`
    })
  });

  res.send("OK");
});

app.listen(3000);
