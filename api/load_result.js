import fs from "fs";
import path from "path";

export default function handler(req, res) {
  try {
    const resultDir = path.join(process.cwd(), "results");
    if (!fs.existsSync(resultDir)) {
      return res.status(200).json([]);
    }

    const files = fs.readdirSync(resultDir).filter(f => f.endsWith(".json"));
    const resultList = files.sort().reverse().map(fname => {
      const content = fs.readFileSync(path.join(resultDir, fname), "utf-8");
      return JSON.parse(content);
    });

    res.status(200).json(resultList);
  } catch (err) {
    res.status(500).send(`에러 발생: ${err.message}`);
  }
}
