#!/usr/bin/env python3
"""
Numen Web App — FastAPI backend + custom animated frontend.
"""

import io
import base64
import os
from fastapi import FastAPI, File, UploadFile, Form, HTTPException
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from PIL import Image

from numen.solvers.student_solver import StudentSolver
from numen.ocr.simple_ocr import SimpleOCR

app = FastAPI()
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])

solver = StudentSolver()
ocr = SimpleOCR()


@app.post("/api/solve")
async def solve_text(problem: str = Form(...)):
    if not problem.strip():
        raise HTTPException(status_code=400, detail="No problem provided")
    try:
        sol = solver.solve_problem(problem.strip())
        return {
            "answer": sol.answer,
            "steps": sol.steps,
            "explanation": sol.explanation,
            "problem_type": sol.problem_type,
            "confidence": sol.confidence,
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/ocr")
async def ocr_image(file: UploadFile = File(...)):
    try:
        data = await file.read()
        img = Image.open(io.BytesIO(data)).convert("RGB")
        result = ocr.extract_from_pil_image(img)
        if not result:
            return {"text": "", "confidence": 0}
        return {"text": result.cleaned_text or result.text, "confidence": round(result.confidence, 2)}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


HTML = r"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8"/>
<meta name="viewport" content="width=device-width,initial-scale=1"/>
<title>Numen — Solve Any Math</title>
<link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800;900&display=swap" rel="stylesheet"/>
<style>
*,*::before,*::after{box-sizing:border-box;margin:0;padding:0}
:root{--red:#dc2626;--rd:#b91c1c;--black:#0a0a0a;--s:#111;--b:#1f1f1f;--t:#e8e8e8;--m:#666}
html{scroll-behavior:smooth}
body{background:var(--black);color:var(--t);font-family:'Inter',sans-serif;overflow-x:hidden;min-height:100vh}
::-webkit-scrollbar{width:3px}::-webkit-scrollbar-thumb{background:var(--red)}

/* ── NAV ── */
nav{position:fixed;top:0;left:0;right:0;z-index:100;display:flex;align-items:center;justify-content:space-between;padding:18px 48px;background:rgba(10,10,10,.9);backdrop-filter:blur(16px);border-bottom:1px solid var(--b);animation:slideDown .5s ease both}
.logo{font-size:20px;font-weight:900;letter-spacing:-1px;color:#fff}.logo span{color:var(--red)}
.nav-tag{font-size:12px;color:var(--m);font-weight:500;letter-spacing:.05em}

/* ── HERO ── */
.hero{min-height:100vh;display:flex;flex-direction:column;align-items:center;justify-content:center;text-align:center;padding:120px 24px 60px;position:relative;overflow:hidden}
.hero-bg{position:absolute;inset:0;pointer-events:none;overflow:hidden}
.hero-glow{position:absolute;top:30%;left:50%;transform:translate(-50%,-50%);width:700px;height:700px;background:radial-gradient(circle,rgba(220,38,38,.12) 0%,transparent 65%);animation:pulse 5s ease-in-out infinite}
.hero-grid{position:absolute;inset:0;background-image:linear-gradient(rgba(255,255,255,.02) 1px,transparent 1px),linear-gradient(90deg,rgba(255,255,255,.02) 1px,transparent 1px);background-size:60px 60px;animation:gridMove 20s linear infinite}
.badge{display:inline-flex;align-items:center;gap:8px;background:rgba(220,38,38,.08);border:1px solid rgba(220,38,38,.25);color:var(--red);padding:6px 16px;border-radius:100px;font-size:11px;font-weight:700;letter-spacing:.12em;text-transform:uppercase;margin-bottom:32px;animation:fadeUp .6s .1s both}
.dot{width:6px;height:6px;background:var(--red);border-radius:50%;animation:blink 1.2s infinite}
h1{font-size:clamp(52px,9vw,110px);font-weight:900;line-height:.92;letter-spacing:-4px;color:#fff;margin-bottom:24px;animation:fadeUp .6s .2s both}
h1 span{color:var(--red)}
.sub{font-size:18px;color:var(--m);max-width:480px;line-height:1.7;margin-bottom:48px;animation:fadeUp .6s .3s both}

/* ── INPUT CARD ── */
.card{background:var(--s);border:1px solid var(--b);border-radius:16px;padding:32px;width:100%;max-width:720px;animation:fadeUp .7s .4s both;position:relative;z-index:1}
.card:hover{border-color:rgba(220,38,38,.3);transition:border-color .3s}

.tabs{display:flex;gap:4px;margin-bottom:24px;background:var(--black);border-radius:8px;padding:4px}
.tab{flex:1;padding:10px;border:none;background:transparent;color:var(--m);font-size:13px;font-weight:600;cursor:pointer;border-radius:6px;transition:all .2s;font-family:inherit}
.tab.active{background:var(--red);color:#fff}
.tab:not(.active):hover{color:#fff;background:rgba(255,255,255,.05)}

/* text input */
.input-wrap{position:relative;margin-bottom:16px}
textarea{width:100%;background:var(--black);border:1px solid var(--b);color:var(--t);padding:16px;border-radius:10px;font-size:15px;font-family:'Inter',monospace;resize:none;outline:none;transition:border-color .2s;line-height:1.6}
textarea:focus{border-color:var(--red);box-shadow:0 0 0 3px rgba(220,38,38,.1)}
.char-hint{position:absolute;bottom:10px;right:12px;font-size:11px;color:var(--m)}

/* examples */
.examples{display:flex;flex-wrap:wrap;gap:8px;margin-bottom:20px}
.ex{background:rgba(255,255,255,.04);border:1px solid var(--b);color:var(--m);padding:6px 12px;border-radius:100px;font-size:12px;cursor:pointer;transition:all .2s;white-space:nowrap}
.ex:hover{border-color:var(--red);color:#fff;background:rgba(220,38,38,.08)}

/* image drop zone */
.drop-zone{border:2px dashed var(--b);border-radius:10px;padding:40px 24px;text-align:center;cursor:pointer;transition:all .3s;position:relative;margin-bottom:16px;background:var(--black)}
.drop-zone:hover,.drop-zone.drag-over{border-color:var(--red);background:rgba(220,38,38,.04)}
.drop-icon{font-size:40px;margin-bottom:12px;display:block}
.drop-text{color:var(--m);font-size:14px}
.drop-text strong{color:var(--t);display:block;margin-bottom:4px;font-size:15px}
.drop-actions{display:flex;gap:8px;justify-content:center;margin-top:16px}
.drop-btn{background:rgba(255,255,255,.06);border:1px solid var(--b);color:var(--t);padding:8px 20px;border-radius:6px;font-size:13px;font-weight:600;cursor:pointer;transition:all .2s;font-family:inherit}
.drop-btn:hover{border-color:var(--red);color:var(--red)}
#file-input,#camera-input{display:none}

/* image preview */
.img-preview{display:none;position:relative;margin-bottom:16px;border-radius:10px;overflow:hidden;border:1px solid var(--b)}
.img-preview img{width:100%;max-height:220px;object-fit:contain;background:#000;display:block}
.img-clear{position:absolute;top:10px;right:10px;background:rgba(0,0,0,.8);border:1px solid var(--b);color:var(--t);width:28px;height:28px;border-radius:50%;cursor:pointer;font-size:14px;display:flex;align-items:center;justify-content:center;transition:all .2s}
.img-clear:hover{border-color:var(--red);color:var(--red)}

/* OCR edit */
.ocr-edit{display:none;margin-bottom:16px}
.ocr-label{font-size:11px;font-weight:700;color:var(--red);text-transform:uppercase;letter-spacing:.08em;margin-bottom:8px}
.ocr-confidence{font-size:11px;color:var(--m);margin-left:8px}

/* solve btn */
.solve-btn{width:100%;padding:16px;background:var(--red);color:#fff;border:none;border-radius:10px;font-size:16px;font-weight:800;cursor:pointer;transition:all .2s;font-family:inherit;letter-spacing:.02em;position:relative;overflow:hidden}
.solve-btn::after{content:'';position:absolute;inset:0;background:linear-gradient(135deg,rgba(255,255,255,.1),transparent);opacity:0;transition:opacity .2s}
.solve-btn:hover{background:var(--rd);transform:translateY(-2px);box-shadow:0 8px 24px rgba(220,38,38,.35)}
.solve-btn:hover::after{opacity:1}
.solve-btn:active{transform:translateY(0)}
.solve-btn:disabled{background:#333;color:#666;cursor:not-allowed;transform:none;box-shadow:none}

/* ── RESULTS ── */
.results{width:100%;max-width:720px;margin-top:24px;position:relative;z-index:1}
.result-card{background:var(--s);border:1px solid var(--b);border-radius:12px;padding:28px;margin-bottom:16px;opacity:0;transform:translateY(20px);transition:opacity .5s ease,transform .5s ease;position:relative;overflow:hidden}
.result-card.show{opacity:1;transform:translateY(0)}
.result-card::before{content:'';position:absolute;left:0;top:0;bottom:0;width:3px;background:var(--red)}
.result-card.steps-card::before{background:#f59e0b}
.result-card.explain-card::before{background:#10b981}
.r-label{font-size:10px;font-weight:700;text-transform:uppercase;letter-spacing:.12em;color:var(--m);margin-bottom:12px;display:flex;align-items:center;gap:8px}
.r-label span{width:20px;height:20px;border-radius:50%;display:inline-flex;align-items:center;justify-content:center;font-size:11px}
.r-answer{font-size:28px;font-weight:800;color:#fff;letter-spacing:-1px;line-height:1.2}
.r-type{font-size:12px;color:var(--red);font-weight:600;margin-top:8px;text-transform:capitalize}
.step-item{padding:10px 0;border-bottom:1px solid rgba(255,255,255,.04);font-size:14px;color:#ccc;line-height:1.6}
.step-item:last-child{border-bottom:none}
.r-explain{font-size:15px;color:#aaa;line-height:1.8}

/* ── LOADING ── */
.loading{display:none;text-align:center;padding:40px;color:var(--m)}
.spinner{width:32px;height:32px;border:2px solid var(--b);border-top-color:var(--red);border-radius:50%;animation:spin .8s linear infinite;margin:0 auto 16px}
.loading-text{font-size:13px;font-weight:500;animation:pulse 1.5s ease-in-out infinite}

/* ── ERROR ── */
.error-card{background:rgba(220,38,38,.08);border:1px solid rgba(220,38,38,.3);border-radius:10px;padding:16px 20px;color:#fca5a5;font-size:14px;margin-top:16px;display:none}

/* ── FLOATING PARTICLES ── */
.particles{position:fixed;inset:0;pointer-events:none;z-index:0;overflow:hidden}
.particle{position:absolute;width:2px;height:2px;background:var(--red);border-radius:50%;opacity:0;animation:float linear infinite}

/* ── SCROLL HINT ── */
.scroll-hint{position:absolute;bottom:32px;left:50%;transform:translateX(-50%);display:flex;flex-direction:column;align-items:center;gap:8px;color:var(--m);font-size:12px;animation:fadeIn 1s 1.5s both}
.scroll-arrow{width:20px;height:20px;border-right:2px solid var(--m);border-bottom:2px solid var(--m);transform:rotate(45deg);animation:bounce 1.5s ease-in-out infinite}

/* ── KEYFRAMES ── */
@keyframes fadeUp{from{opacity:0;transform:translateY(24px)}to{opacity:1;transform:translateY(0)}}
@keyframes fadeIn{from{opacity:0}to{opacity:1}}
@keyframes slideDown{from{opacity:0;transform:translateY(-20px)}to{opacity:1;transform:translateY(0)}}
@keyframes pulse{0%,100%{opacity:.6;transform:translate(-50%,-50%) scale(1)}50%{opacity:1;transform:translate(-50%,-50%) scale(1.08)}}
@keyframes gridMove{from{background-position:0 0}to{background-position:60px 60px}}
@keyframes spin{to{transform:rotate(360deg)}}
@keyframes blink{0%,100%{opacity:1}50%{opacity:.2}}
@keyframes float{0%{opacity:0;transform:translateY(0) translateX(0)}10%{opacity:.6}90%{opacity:.2}100%{opacity:0;transform:translateY(-100vh) translateX(40px)}}
@keyframes bounce{0%,100%{transform:rotate(45deg) translateY(0)}50%{transform:rotate(45deg) translateY(6px)}}
@keyframes countIn{from{clip-path:inset(0 100% 0 0)}to{clip-path:inset(0 0% 0 0)}}
@keyframes shimmer{0%{background-position:-200% 0}100%{background-position:200% 0}}

/* ── MOBILE ── */
@media(max-width:600px){nav{padding:14px 20px}.hero{padding:100px 16px 40px}h1{letter-spacing:-2px}.card{padding:20px}.drop-actions{flex-direction:column}}
</style>
</head>
<body>

<!-- Particles -->
<div class="particles" id="particles"></div>

<!-- Nav -->
<nav>
  <div class="logo">NU<span>MEN</span></div>
  <div class="nav-tag">Mathematical Reasoning Engine</div>
</nav>

<!-- Hero -->
<section class="hero">
  <div class="hero-bg">
    <div class="hero-glow"></div>
    <div class="hero-grid"></div>
  </div>

  <div class="badge"><span class="dot"></span>Symbolic Math · Zero Hallucination</div>
  <h1>SOLVE<br/>ANY<br/><span>MATH.</span></h1>
  <p class="sub">Type a problem or snap a photo. Numen verifies every answer mathematically — 100% accurate, step by step.</p>

  <!-- Input Card -->
  <div class="card" id="main-card">

    <!-- Tabs -->
    <div class="tabs">
      <button class="tab active" onclick="switchTab('text')">✏️ Type problem</button>
      <button class="tab" onclick="switchTab('image')">📷 Upload photo</button>
    </div>

    <!-- TEXT TAB -->
    <div id="tab-text">
      <div class="input-wrap">
        <textarea id="problem-input" rows="3" placeholder="e.g. solve 2x + 5 = 13 · derivative of x³ + 2x · integral of sin(x)"></textarea>
        <span class="char-hint" id="char-count">0</span>
      </div>
      <div class="examples" id="examples-row"></div>
    </div>

    <!-- IMAGE TAB -->
    <div id="tab-image" style="display:none">
      <div class="drop-zone" id="drop-zone">
        <span class="drop-icon">📐</span>
        <div class="drop-text">
          <strong>Drop your photo here</strong>
          Homework, textbook, whiteboard — anything works
        </div>
        <div class="drop-actions">
          <button class="drop-btn" onclick="document.getElementById('file-input').click()">📁 Browse files</button>
          <button class="drop-btn" onclick="document.getElementById('camera-input').click()">📷 Use camera</button>
        </div>
      </div>
      <input type="file" id="file-input" accept="image/*" onchange="handleFile(this.files[0])"/>
      <input type="file" id="camera-input" accept="image/*" capture="environment" onchange="handleFile(this.files[0])"/>

      <div class="img-preview" id="img-preview">
        <img id="preview-img" src="" alt="preview"/>
        <button class="img-clear" onclick="clearImage()" title="Remove">✕</button>
      </div>

      <div class="ocr-edit" id="ocr-edit">
        <div class="ocr-label">Numen read this — edit if anything's wrong <span class="ocr-confidence" id="ocr-conf"></span></div>
        <textarea id="ocr-text" rows="2" placeholder="Extracted equation will appear here..."></textarea>
      </div>
    </div>

    <!-- Error -->
    <div class="error-card" id="error-card"></div>

    <!-- Solve button -->
    <button class="solve-btn" id="solve-btn" onclick="solve()">Solve it →</button>
  </div>

  <!-- Results -->
  <div class="results" id="results" style="display:none">
    <div class="loading" id="loading">
      <div class="spinner"></div>
      <div class="loading-text">Computing...</div>
    </div>

    <div id="result-cards" style="display:none">
      <div class="result-card" id="card-answer">
        <div class="r-label">Answer</div>
        <div class="r-answer" id="res-answer"></div>
        <div class="r-type" id="res-type"></div>
      </div>
      <div class="result-card steps-card" id="card-steps">
        <div class="r-label">Step-by-step</div>
        <div id="res-steps"></div>
      </div>
      <div class="result-card explain-card" id="card-explain">
        <div class="r-label">Explanation</div>
        <div class="r-explain" id="res-explain"></div>
      </div>
    </div>
  </div>

  <div class="scroll-hint">
    <span>scroll</span>
    <div class="scroll-arrow"></div>
  </div>
</section>

<script>
// ── PARTICLES ────────────────────────────────────────────────
const pContainer = document.getElementById('particles');
for (let i = 0; i < 28; i++) {
  const p = document.createElement('div');
  p.className = 'particle';
  p.style.cssText = `
    left:${Math.random()*100}%;
    top:${Math.random()*100}%;
    animation-duration:${6+Math.random()*12}s;
    animation-delay:${Math.random()*8}s;
    opacity:${0.2+Math.random()*0.5};
    width:${Math.random()>0.7?3:2}px;
    height:${Math.random()>0.7?3:2}px;
  `;
  pContainer.appendChild(p);
}

// ── EXAMPLES ─────────────────────────────────────────────────
const EXAMPLES = [
  "solve 2x + 5 = 13",
  "derivative of x³ + 2x²",
  "integral of sin(x)",
  "solve x² - 5x + 6 = 0",
  "simplify (x²-1)/(x-1)",
  "expand (x+3)²",
];
const exRow = document.getElementById('examples-row');
EXAMPLES.forEach(ex => {
  const btn = document.createElement('button');
  btn.className = 'ex';
  btn.textContent = ex;
  btn.onclick = () => {
    document.getElementById('problem-input').value = ex;
    updateCount();
    document.getElementById('problem-input').focus();
  };
  exRow.appendChild(btn);
});

// char counter
const input = document.getElementById('problem-input');
const counter = document.getElementById('char-count');
function updateCount() { counter.textContent = input.value.length; }
input.addEventListener('input', updateCount);
input.addEventListener('keydown', e => { if (e.key === 'Enter' && !e.shiftKey) { e.preventDefault(); solve(); } });

// ── TABS ─────────────────────────────────────────────────────
let currentTab = 'text';
function switchTab(tab) {
  currentTab = tab;
  document.getElementById('tab-text').style.display = tab === 'text' ? 'block' : 'none';
  document.getElementById('tab-image').style.display = tab === 'image' ? 'block' : 'none';
  document.querySelectorAll('.tab').forEach((t,i) => t.classList.toggle('active', (i===0&&tab==='text')||(i===1&&tab==='image')));
  hideResults();
}

// ── DRAG & DROP ───────────────────────────────────────────────
const dropZone = document.getElementById('drop-zone');
dropZone.addEventListener('dragover', e => { e.preventDefault(); dropZone.classList.add('drag-over'); });
dropZone.addEventListener('dragleave', () => dropZone.classList.remove('drag-over'));
dropZone.addEventListener('drop', e => { e.preventDefault(); dropZone.classList.remove('drag-over'); if (e.dataTransfer.files[0]) handleFile(e.dataTransfer.files[0]); });
dropZone.addEventListener('click', () => document.getElementById('file-input').click());

// ── IMAGE HANDLING ────────────────────────────────────────────
let currentFile = null;
function handleFile(file) {
  if (!file || !file.type.startsWith('image/')) return;
  currentFile = file;
  const reader = new FileReader();
  reader.onload = e => {
    document.getElementById('preview-img').src = e.target.result;
    document.getElementById('img-preview').style.display = 'block';
    dropZone.style.display = 'none';
    runOCR(file);
  };
  reader.readAsDataURL(file);
}

function clearImage() {
  currentFile = null;
  document.getElementById('img-preview').style.display = 'none';
  document.getElementById('ocr-edit').style.display = 'none';
  document.getElementById('drop-zone').style.display = 'block';
  document.getElementById('file-input').value = '';
  hideResults();
}

async function runOCR(file) {
  const ocrEdit = document.getElementById('ocr-edit');
  const ocrText = document.getElementById('ocr-text');
  ocrText.value = '⏳ Reading image...';
  ocrEdit.style.display = 'block';

  const fd = new FormData();
  fd.append('file', file);
  try {
    const res = await fetch('/api/ocr', { method: 'POST', body: fd });
    const data = await res.json();
    ocrText.value = data.text || '';
    const pct = Math.round((data.confidence || 0) * 100);
    document.getElementById('ocr-conf').textContent = `(${pct}% confidence)`;
  } catch {
    ocrText.value = '';
    document.getElementById('ocr-conf').textContent = '(OCR failed — type manually)';
  }
}

// ── SOLVE ─────────────────────────────────────────────────────
async function solve() {
  let problem = '';
  if (currentTab === 'text') {
    problem = document.getElementById('problem-input').value.trim();
    if (!problem) { shakeCard(); return; }
  } else {
    problem = document.getElementById('ocr-text').value.trim();
    if (!problem) { shakeCard(); return; }
  }

  showLoading();
  hideError();

  try {
    const fd = new FormData();
    fd.append('problem', problem);
    const res = await fetch('/api/solve', { method: 'POST', body: fd });
    if (!res.ok) { const e = await res.json(); throw new Error(e.detail || 'Server error'); }
    const data = await res.json();
    showResults(data);
  } catch (err) {
    hideLoading();
    showError(err.message);
  }
}

function showResults(data) {
  hideLoading();
  document.getElementById('results').style.display = 'block';
  document.getElementById('result-cards').style.display = 'block';

  // Answer
  document.getElementById('res-answer').textContent = data.answer || '—';
  document.getElementById('res-type').textContent = (data.problem_type || '').replace(/_/g,' ');

  // Steps
  const stepsEl = document.getElementById('res-steps');
  stepsEl.innerHTML = '';
  (data.steps || []).forEach(s => {
    const d = document.createElement('div');
    d.className = 'step-item';
    d.textContent = s.replace(/\*\*/g,'').replace(/📝|🔧|📊|🔍|✅|📐|🔢/g,'').trim();
    stepsEl.appendChild(d);
  });

  // Explanation
  document.getElementById('res-explain').textContent = data.explanation || '—';

  // Animate cards in with stagger
  ['card-answer','card-steps','card-explain'].forEach((id,i) => {
    const el = document.getElementById(id);
    el.classList.remove('show');
    setTimeout(() => el.classList.add('show'), 80 + i * 120);
  });

  // Scroll to results
  setTimeout(() => document.getElementById('results').scrollIntoView({behavior:'smooth',block:'nearest'}), 200);
}

function showLoading() {
  document.getElementById('solve-btn').disabled = true;
  document.getElementById('results').style.display = 'block';
  document.getElementById('loading').style.display = 'block';
  document.getElementById('result-cards').style.display = 'none';
}
function hideLoading() {
  document.getElementById('solve-btn').disabled = false;
  document.getElementById('loading').style.display = 'none';
}
function hideResults() {
  document.getElementById('results').style.display = 'none';
  ['card-answer','card-steps','card-explain'].forEach(id => document.getElementById(id).classList.remove('show'));
}
function showError(msg) {
  const el = document.getElementById('error-card');
  el.textContent = '⚠️ ' + msg;
  el.style.display = 'block';
}
function hideError() { document.getElementById('error-card').style.display = 'none'; }

function shakeCard() {
  const card = document.getElementById('main-card');
  card.style.animation = 'none';
  card.style.transform = 'translateX(-8px)';
  setTimeout(() => card.style.transform = 'translateX(8px)', 80);
  setTimeout(() => card.style.transform = 'translateX(-5px)', 160);
  setTimeout(() => card.style.transform = 'translateX(5px)', 240);
  setTimeout(() => card.style.transform = 'translateX(0)', 320);
}

// ── CURSOR GLOW EFFECT ────────────────────────────────────────
document.addEventListener('mousemove', e => {
  const glow = document.querySelector('.hero-glow');
  if (!glow) return;
  const x = (e.clientX / window.innerWidth) * 100;
  const y = (e.clientY / window.innerHeight) * 100;
  glow.style.left = x + '%';
  glow.style.top = y + '%';
  glow.style.transform = 'translate(-50%,-50%)';
});
</script>
</body>
</html>"""


@app.get("/", response_class=HTMLResponse)
async def index():
    return HTML


if __name__ == "__main__":
    import uvicorn
    port = int(os.environ.get("PORT", 8000))
    uvicorn.run("web_app:app", host="0.0.0.0", port=port, reload=False)
