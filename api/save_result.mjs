import fs from "fs";
import path from "path";

export default function handler(req, res) {
  try {
    if (req.method !== "POST") {
      return res.status(405).json({ error: "Method not allowed" });
    }

    const body = req.body;
    const username = body.username || "anonymous";
    const score = body.score;
    const topic = body.topic;

    const timestamp = new Date().toISOString().replace(/[:.]/g, "_");
    const filename = `${username}_${timestamp}.json`;

    const resultDir = path.join(process.cwd(), "results");
    if (!fs.existsSync(resultDir)) fs.mkdirSync(resultDir);

    const filepath = path.join(resultDir, filename);
    fs.writeFileSync(filepath, JSON.stringify(body, null, 2), "utf-8");

    res.status(200).json({ message: "저장 완료", file: filename });
  } catch (err) {
    res.status(500).send(`에러 발생: ${err.message}`);
  }
}
