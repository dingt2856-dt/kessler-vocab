const base = process.env.KESSLER_APP_URL || "https://dingt2856-dt.github.io/kessler-vocab";
const stamp = Date.now();
const headers = { "cache-control": "no-cache", pragma: "no-cache" };

async function get(path) {
  const joiner = path.includes("?") ? "&" : "?";
  const response = await fetch(`${base}${path}${joiner}check=${stamp}`, { headers });
  if (!response.ok) throw new Error(`${path} HTTP ${response.status}`);
  return response;
}

(async () => {
  const index = await (await get("/?refresh=20260804-7")).text();
  const interviewScript = await (await get("/interview.js?v=2026-08-04-7")).text();
  const serviceWorker = await (await get("/sw.js")).text();
  const manifest = await (await get("/audio/interview/manifest.json")).json();
  const audio = [];

  for (const item of manifest.items) {
    const response = await get(`/audio/interview/${item.file}`);
    audio.push({
      file: item.file,
      status: response.status,
      bytes: (await response.arrayBuffer()).byteLength,
    });
  }

  const bad = audio.filter((item) => item.status !== 200 || item.bytes < 1_000);
  const result = {
    indexV7: index.includes("interview.js?v=2026-08-04-7"),
    indexFixedMale:
      index.includes("男声音频随网站提供") &&
      interviewScript.includes("Ryan · British English · Male"),
    serviceWorkerV11: serviceWorker.includes("2026-08-06-v11"),
    voice: manifest.voice,
    manifestCount: manifest.generatedFiles,
    items: manifest.items.length,
    audioOK: audio.length - bad.length,
    audioBad: bad.length,
    minBytes: Math.min(...audio.map((item) => item.bytes)),
    maxBytes: Math.max(...audio.map((item) => item.bytes)),
  };
  console.log(JSON.stringify(result, null, 2));

  if (
    !result.indexV7 ||
    !result.indexFixedMale ||
    !result.serviceWorkerV11 ||
    result.voice !== "en-GB-RyanNeural" ||
    result.manifestCount !== 32 ||
    bad.length
  ) {
    console.error(JSON.stringify({ bad }, null, 2));
    process.exit(1);
  }
})().catch((error) => {
  console.error(error.stack || error);
  process.exit(1);
});
