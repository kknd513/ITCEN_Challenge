import React, { useState } from 'react';
import { createRoot } from 'react-dom/client';
import NaturalCommandPanel from "./components/NaturalCommandPanel";
import { Bot, LayoutDashboard, Server, Bell, FileText, Settings, Send, BookOpen, Terminal, Activity, ClipboardList, User, ChevronRight, Loader2, CheckCircle2 } from 'lucide-react';
import './styles.css';

type Cause = {
  rank: number;
  title: string;
  probability: number;
  reason: string;
  evidence: string[];
  recommended_commands: string[];
  next_actions: string[];
};

type AnalysisResponse = {
  incident_id: string;
  summary: string;
  causes: Cause[];
  agent_logs: any[];
  rag_sources: any[];
  command_suggestions: any[];
  report_markdown: string;
};

const API_BASE = import.meta.env.VITE_API_BASE_URL || 'https://back-end-production-8a58.up.railway.app';

function Sidebar() {
  const items = [
    { icon: Bot, label: '챗봇', active: true },
    { icon: LayoutDashboard, label: '대시보드' },
    { icon: Server, label: '서버/자원' },
    { icon: Bell, label: '이벤트' },
    { icon: FileText, label: '보고서' },
    { icon: Settings, label: '설정' },
  ];
  return <aside className="sidebar">
    <div className="brand"><div className="brandBot">🤖</div><div>CENOps<br/>Copilot</div></div>
    <nav>{items.map(({ icon: Icon, label, active }) => <div key={label} className={`navItem ${active ? 'active' : ''}`}><Icon size={22}/><span>{label}</span></div>)}</nav>
    <div className="admin"><div className="avatar"><User size={22}/></div><div><b>admin</b><span>시스템 관리자</span></div></div>
  </aside>;
}

function FeatureCard({ icon: Icon, title, desc }: any) {
  return <div className="feature"><div className="featureIcon"><Icon size={30}/></div><div><h3>{title}</h3><p>{desc}</p></div></div>;
}

function ResultPanel({ result }: { result: AnalysisResponse }) {
  return <section className="resultPanel">
    <div className="resultHeader"><CheckCircle2 size={22}/><strong>분석 결과</strong><span>Incident ID: {result.incident_id.slice(0, 8)}</span></div>
    <p className="summary">{result.summary}</p>
    {result.causes.length > 0 && <div className="causeGrid">
      {result.causes.map((cause) => <article key={cause.rank} className="causeCard">
        <div className="rank">{cause.rank}</div>
        <h3>{cause.title}</h3>
        <p className="prob">가능성 {Math.round(cause.probability * 100)}%</p>
        <p>{cause.reason}</p>
        <h4>근거 로그</h4>
        <ul>{cause.evidence.slice(0,2).map((e, idx) => <li key={idx}>{e}</li>)}</ul>
        <h4>권장 조회 Command</h4>
        <code>{cause.recommended_commands[0]}</code>
      </article>)}
    </div>}
    {result.causes.length === 0 && <div className="noCauses">원인 후보 산출이 아닌 서버/RAG 질의 응답입니다. 아래 수집 결과와 참조 문서를 확인하세요.</div>}
    <div className="details">
      <div><h3>Agent 수집 결과</h3>{result.agent_logs.map((a) => <p key={a.agent_name}>• {a.agent_name} / {a.role} / {a.status} / {a.collection_mode}</p>)}</div>
      <div><h3>RAG 검색 문서</h3>{result.rag_sources.slice(0,3).map((s) => <p key={s.path}>• {s.title} ({s.path})</p>)}</div>
    </div>
    <details className="report"><summary>장애 보고서 미리보기</summary><pre>{result.report_markdown}</pre></details>
  </section>
}

function App() {
  const [message, setMessage] = useState('Zenius 알림: WEB-01 502 오류 발생. 원인 분석해줘.');
  const [target, setTarget] = useState('');
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState<AnalysisResponse | null>(null);
  const [error, setError] = useState<string | null>(null);

  async function submit(prompt?: string) {
    const text = prompt || message;
    setMessage(text);
    setLoading(true);
    setError(null);
    try {
      const res = await fetch(`${API_BASE}/api/chat`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ message: text, target: target || undefined }),
      });
      if (!res.ok) throw new Error(`API 오류: ${res.status}`);
      setResult(await res.json());
    } catch (e: any) {
      setError(e.message || '분석 중 오류가 발생했습니다.');
    } finally {
      setLoading(false);
    }
  }

  const examples = ['WEB-01 502 오류 원인 분석해줘', 'A서버 최근 Nginx 로그 상태 확인해줘', 'B서버 Tomcat 502 조치 문서 찾아줘', 'C서버 DB 연결 상태와 RAG 문서 근거 알려줘', '장애 분석 보고서를 생성해줘'];

  return <div className="app"><Sidebar/><main className="main">
    <header className="hero"><div><h1>CENOps Copilot 챗봇 인터페이스</h1><p>Railway 기반 운영지원 프로토타입</p></div><div className="heroBot">🤖</div></header>
    <section className="card intro">
      <h2>안녕하세요!</h2><p><b>CENOps Copilot</b>이 Railway 기반 운영을 도와드릴게요.</p>
      <div className="exampleBox"><h3>챗봇 예시 질문</h3>{examples.map((ex) => <button key={ex} onClick={() => submit(ex)}>{ex}<ChevronRight size={18}/></button>)}</div>
      <div className="features">
        <FeatureCard icon={BookOpen} title="운영문서 RAG 검색" desc="Tomcat 장애조치 문서와 산출물을 검색합니다."/>
        <FeatureCard icon={Bot} title="Mock Agent 상태 수집" desc="WEB/WAS/DB Agent 로그와 지표를 수집합니다."/>
        <FeatureCard icon={Terminal} title="조회성 자연어 Command" desc="안전한 조회성 명령어를 제안합니다."/>
        <FeatureCard icon={ClipboardList} title="장애 보고서 생성" desc="요약, 근거, 조치 가이드를 보고서로 생성합니다."/>
      </div>
      <div className="targetRow"><label>대상 서버</label><select value={target} onChange={(e) => setTarget(e.target.value)}><option value="">자동선택 / 전체</option><option value="A">A-SERVER / WEB-01</option><option value="B">B-SERVER / WAS-01</option><option value="C">C-SERVER / DB-01</option></select></div><div className="inputRow"><input value={message} onChange={(e) => setMessage(e.target.value)} onKeyDown={(e) => { if (e.key === 'Enter') submit(); }} placeholder="궁금한 내용을 입력해 주세요..."/><button onClick={() => submit()} disabled={loading}>{loading ? <Loader2 className="spin"/> : <Send/>}</button></div>
      {error && <p className="error">{error}</p>}
    </section>
    {result && <ResultPanel result={result}/>}  
  </main></div>;
}

createRoot(document.getElementById('root')!).render(<App />);
