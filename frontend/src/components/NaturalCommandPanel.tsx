import { useState } from "react";

export default function NaturalCommandPanel() {
  const [question, setQuestion] = useState("A서버 디스크 사용량 확인해줘");
  const [result, setResult] = useState<any>(null);
  const [loading, setLoading] = useState(false);

  async function runCommand() {
    setLoading(true);
    setResult(null);
    try {
      const res = await fetch(`${import.meta.env.VITE_API_BASE_URL}/api/ops/natural-command`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ question, dry_run: false }),
      });
      const data = await res.json();
      setResult(data);
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="natural-command-panel">
      <h3>자연어 Linux 점검</h3>
      <textarea value={question} onChange={(e) => setQuestion(e.target.value)} rows={3} />
      <button onClick={runCommand} disabled={loading}>{loading ? "실행 중" : "조회 실행"}</button>
      {result && (
        <div className="command-result">
          <div><b>대상:</b> {result.mapped?.server_id}</div>
          <div><b>변환 명령어:</b> <code>{result.mapped?.command}</code></div>
          <pre>{result.result?.stdout || result.result?.stderr || JSON.stringify(result, null, 2)}</pre>
        </div>
      )}
    </div>
  );
}
