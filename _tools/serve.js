// 极简静态服务器：仅用于本地无头浏览器渲染/截图（不参与交付物，不引入依赖）
const http = require("http");
const fs = require("fs");
const path = require("path");

const ROOT = path.resolve(__dirname, "..", "Zhouruoying_C6A_dashboard");
const PORT = Number(process.argv[2] || 8799);
const MIME = {
  ".html": "text/html; charset=utf-8",
  ".js": "application/javascript; charset=utf-8",
  ".css": "text/css; charset=utf-8",
  ".json": "application/json; charset=utf-8",
  ".png": "image/png",
};

http
  .createServer((req, res) => {
    const urlPath = decodeURIComponent((req.url || "/").split("?")[0].split("#")[0]);
    const rel = urlPath === "/" ? "index.html" : urlPath.replace(/^\/+/, "");
    const full = path.join(ROOT, rel);
    if (!full.startsWith(ROOT)) {
      res.writeHead(403).end("forbidden");
      return;
    }
    fs.readFile(full, (err, buf) => {
      if (err) {
        res.writeHead(404, { "content-type": "text/plain; charset=utf-8" }).end("not found: " + rel);
        return;
      }
      res.writeHead(200, { "content-type": MIME[path.extname(full)] || "application/octet-stream" });
      res.end(buf);
    });
  })
  .listen(PORT, "127.0.0.1", () => console.log("serving " + ROOT + " on http://127.0.0.1:" + PORT));
