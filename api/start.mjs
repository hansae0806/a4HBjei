import fs from "fs";
import path from "path";

export default function handler(req, res) {
  try {
    if (req.method !== "POST") {
      return res.status(405).json({ error: "Method not allowed" });
    }

    const body = req.body;
    const { topic, level, sub_category } = body;

    let filename;
    if (["grammar", "vocab", "idioms"].includes(topic)) {
      filename = `${topic}${sub_category}_${level}.json`;
    } else {
      filename = `${topic}_${level}.json`;
    }

    const filepath = path.join(process.cwd(), "data", filename);

    if (!fs.existsSync(filepath)) {
      return res.status(404).send(`파일 ${filename}이 존재하지 않습니다.`);
    }

    const questions = JSON.parse(fs.readFileSync(filepath, "utf-8"));
    res.status(200).json(questions);
  } catch (err) {
    res.status(500).send(`오류 발생: ${err.message}`);
  }
}
