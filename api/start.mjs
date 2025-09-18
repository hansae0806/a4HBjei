import fs from "fs";
import path from "path";

export default async function handler(req, res) {
  try {
    if (req.method !== "POST") {
      return res.status(405).json({ error: "Method not allowed" });
    }

    // Vercel Serverless에서 req.body 직접 파싱
    const body = req.body && Object.keys(req.body).length > 0
      ? req.body
      : await new Promise((resolve, reject) => {
          let data = "";
          req.on("data", chunk => (data += chunk));
          req.on("end", () => {
            try {
              resolve(JSON.parse(data));
            } catch (err) {
              reject(err);
            }
          });
        });

    const { topic, level, sub_category } = body;

    let filename;
    if (["grammar", "vocab", "idioms"].includes(topic)) {
      filename = `${topic}${sub_category}_${level}.json`;
    } else {
      filename = `${topic}_${level}.json`;
    }

    const filepath = path.join(process.cwd(), "data", filename);

    if (!fs.existsSync(filepath)) {
      return res.status(404).json({ error: `파일 ${filename}이 존재하지 않습니다.` });
    }

    const questions = JSON.parse(fs.readFileSync(filepath, "utf-8"));
    return res.status(200).json(questions);
  } catch (err) {
    return res.status(500).json({ error: `오류 발생: ${err.message}` });
  }
}
