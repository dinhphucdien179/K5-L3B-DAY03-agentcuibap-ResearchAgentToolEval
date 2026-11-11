"""Escaped presentational components. Source strings never become executable HTML."""
from __future__ import annotations

import html
import json
from urllib.parse import urlsplit
from typing import Any

import streamlit as st


def e(value: Any) -> str:
    return html.escape(str(value if value is not None else ""), quote=True)


def section(label: str, title: str, subtitle: str = "") -> None:
    st.markdown(f'<div class="section"><div class="eyebrow">{e(label)}</div><h2>{e(title)}</h2><p>{e(subtitle)}</p></div>', unsafe_allow_html=True)


def metric(label: str, value: Any, detail: str, accent: str = "cyan") -> str:
    return f'<div class="metric-card {e(accent)}"><span>{e(label)}</span><strong>{e(value)}</strong><small>{e(detail)}</small></div>'


def show_workflow(steps: list[dict[str, Any]]) -> None:
    names = {"validate": "Kiểm tra đầu vào", "search": "Tìm nguồn", "deduplicate": "Gộp URL trùng", "group_sources": "Nhóm theo domain", "build_graph": "Dựng source map"}
    if not steps:
        st.info("Chưa có workflow thực thi. Gửi một yêu cầu hoặc tạo board để bắt đầu.")
        return
    cards = []
    for index, step in enumerate(steps, 1):
        state = step.get("status", "unknown")
        cards.append(f'<div class="workflow-step"><div class="step-num">{index:02d}</div><div><b>{e(names.get(step.get("step"), step.get("step")))}</b><small>{e(step.get("detail", ""))}</small></div><span class="state {e(state)}">{e(state)}</span></div>')
    st.markdown('<div class="workflow">' + "".join(cards) + '</div>', unsafe_allow_html=True)


def show_graph(graph: dict[str, Any]) -> None:
    # Escape script delimiters as JSON unicode escapes, then use SVG textContent.
    data = json.dumps(graph, ensure_ascii=False, default=str).replace("&", "\\u0026").replace("<", "\\u003c").replace(">", "\\u003e").replace("\u2028", "\\u2028").replace("\u2029", "\\u2029")
    document = '''<!doctype html><html><head><meta charset="utf-8"><style>
    *{box-sizing:border-box}body{margin:0;background:#0b1223;color:#bac8e3;font:12px 'Segoe UI',sans-serif}.wrap{border:1px solid #26334d;border-radius:16px;overflow:hidden;position:relative}#canvas{display:block;width:100%;height:490px;background:radial-gradient(ellipse at 50% 20%,#142342 0%,#0b1223 70%);cursor:grab;touch-action:none}.bar{display:flex;gap:18px;align-items:center;padding:13px 16px;border-bottom:1px solid #26334d}.dot{display:inline-block;width:8px;height:8px;border-radius:50%;margin-right:6px}.query{background:#66e4cf}.source{background:#a79bff}.item{background:#79b5ff}button{margin-left:auto;background:#1a2841;border:1px solid #354568;border-radius:7px;color:#dce7ff;padding:5px 10px;cursor:pointer}.hint{position:absolute;bottom:12px;left:15px;color:#94a4c2;font-size:11px;pointer-events:none}#tip{position:absolute;top:58px;left:16px;right:16px;padding:9px 12px;background:#17243aee;border:1px solid #354568;border-radius:9px;display:none;pointer-events:none;white-space:pre-wrap}.node{cursor:pointer}.edge{stroke:#314262;stroke-width:1;opacity:.55}.node text{fill:#c3cee1;font-size:10px;pointer-events:none}.node circle{stroke:#0b1223;stroke-width:3}.dim{opacity:.12}.selected circle{stroke:#f5f9ff;stroke-width:3}
    </style></head><body><div class="wrap"><div class="bar"><span><i class="dot query"></i>Query</span><span><i class="dot source"></i>Domain</span><span><i class="dot item"></i>Evidence</span><button id="reset">Reset view</button></div><svg id="canvas" viewBox="0 0 1000 490" role="img" aria-label="Interactive query domain evidence graph"><g id="scene"></g></svg><div id="tip"></div><div class="hint">Scroll để zoom · Kéo để di chuyển · Chọn node để xem liên kết</div></div><script>
    const data=__DATA__;const svg=document.querySelector('#canvas'),scene=document.querySelector('#scene'),tip=document.querySelector('#tip');const ns='http://www.w3.org/2000/svg';const colors={query:'#66e4cf',source:'#a79bff',item:'#79b5ff'};const kinds=['query','source','item'];const nodes=Array.isArray(data.nodes)?data.nodes:[];const links=Array.isArray(data.edges)?data.edges:[];const byId=new Map();const positions=new Map();let scale=1,dx=0,dy=0;
    kinds.forEach((kind,col)=>{const group=nodes.filter(n=>n.kind===kind);group.forEach((n,i)=>{positions.set(n.id,{x:100+col*380,y:35+(i+.5)*(420/Math.max(1,group.length))});byId.set(n.id,n);});});
    function element(name,attrs){const el=document.createElementNS(ns,name);Object.entries(attrs).forEach(([k,v])=>el.setAttribute(k,String(v)));return el;}
    links.forEach(l=>{const a=positions.get(l.source),b=positions.get(l.target);if(!a||!b)return;const edge=element('path',{d:`M${a.x},${a.y} C${(a.x+b.x)/2},${a.y} ${(a.x+b.x)/2},${b.y} ${b.x},${b.y}`,class:'edge'});edge.dataset.source=l.source;edge.dataset.target=l.target;scene.appendChild(edge);});
    nodes.forEach(n=>{const p=positions.get(n.id);if(!p)return;const g=element('g',{class:'node',transform:`translate(${p.x},${p.y})`});g.dataset.id=n.id;g.appendChild(element('circle',{r:n.kind==='query'?12:n.kind==='source'?8:5,fill:colors[n.kind]||'#aaa'}));const t=element('text',{x:16,y:4});const label=String(n.label||n.id);t.textContent=label.slice(0,n.kind==='item'?26:31)+(label.length>(n.kind==='item'?26:31)?'…':'');g.appendChild(t);const title=element('title',{});title.textContent=label;g.appendChild(title);g.addEventListener('click',event=>{event.stopPropagation();const near=new Set([n.id]);links.forEach(l=>{if(l.source===n.id)near.add(l.target);if(l.target===n.id)near.add(l.source);});scene.querySelectorAll('.node').forEach(el=>{el.classList.toggle('dim',!near.has(el.dataset.id));el.classList.toggle('selected',el.dataset.id===n.id);});scene.querySelectorAll('.edge').forEach(el=>el.classList.toggle('dim',el.dataset.source!==n.id&&el.dataset.target!==n.id));tip.textContent=n.kind.toUpperCase()+' · '+label;tip.style.display='block';});scene.appendChild(g);});
    function transform(){scene.setAttribute('transform',`translate(${dx},${dy}) scale(${scale})`);}function reset(){scale=1;dx=0;dy=0;transform();scene.querySelectorAll('.dim,.selected').forEach(el=>el.classList.remove('dim','selected'));tip.style.display='none';}document.querySelector('#reset').onclick=reset;svg.addEventListener('wheel',ev=>{ev.preventDefault();const rect=svg.getBoundingClientRect(),x=(ev.clientX-rect.left)*1000/rect.width,y=(ev.clientY-rect.top)*490/rect.height;const next=Math.max(.35,Math.min(4,scale*(ev.deltaY<0?1.12:.89)));dx=x-(x-dx)*next/scale;dy=y-(y-dy)*next/scale;scale=next;transform();},{passive:false});let drag=null;svg.addEventListener('pointerdown',ev=>{drag={x:ev.clientX,y:ev.clientY,dx,dy};svg.setPointerCapture(ev.pointerId);});svg.addEventListener('pointermove',ev=>{if(!drag)return;const rect=svg.getBoundingClientRect();dx=drag.dx+(ev.clientX-drag.x)*1000/rect.width;dy=drag.dy+(ev.clientY-drag.y)*490/rect.height;transform();});svg.addEventListener('pointerup',()=>{drag=null;});svg.addEventListener('dblclick',reset);
    </script></body></html>'''.replace("__DATA__", data)
    st.iframe(document, height=550, alt="Interactive query-to-source evidence graph")


def show_evidence(items: list[dict[str, Any]], query_names: dict[str, str]) -> None:
    if not items:
        st.info("Không có evidence card trong kết quả này. Xem trạng thái query và lỗi bên dưới.")
        return
    selected = st.selectbox("Lọc domain", ["Tất cả domain", *sorted({str(i.get("source", "")) for i in items})], key="source_filter")
    visible = items if selected == "Tất cả domain" else [i for i in items if i.get("source") == selected]
    for start in range(0, len(visible), 2):
        columns = st.columns(2)
        for column, item in zip(columns, visible[start:start + 2]):
            with column:
                url = str(item.get("url", ""))
                try:
                    parsed = urlsplit(url)
                    safe = parsed.scheme in {"http", "https"} and bool(parsed.hostname) and not parsed.username and not parsed.password
                except ValueError:
                    safe = False
                title = e(item.get("title") or "Nguồn chưa có tiêu đề")
                title_html = f'<a href="{e(url)}" target="_blank" rel="noopener noreferrer">{title} ↗</a>' if safe else title
                date = item.get("published_at") or "Chưa có ngày từ provider"
                count = len(item.get("provenance", {}).get("query_ids", []))
                st.markdown(f'<article class="evidence"><div class="source-row"><span class="source-dot"></span>{e(item.get("source"))}<span class="query-count">{count} query</span></div><h3>{title_html}</h3><p>{e(item.get("summary") or "Provider chưa trả excerpt cho nguồn này.")}</p><div class="card-footer"><span>{e(str(date)[:45])}</span><code>{e(str(item.get("id", ""))[:14])}</code></div></article>', unsafe_allow_html=True)
                with st.expander("URL & provenance", expanded=False):
                    st.caption("Retrieval score là độ liên quan do provider trả về, không phải điểm đúng/sai.")
                    st.json({"url": url, "relevance_score": item.get("relevance_score"), "queries": [query_names.get(q, q) for q in item.get("provenance", {}).get("query_ids", [])], "provenance": item.get("provenance", {})}, expanded=False)


def show_trace(turn: dict[str, Any]) -> None:
    for index, event in enumerate(turn.get("tool_events", []), 1):
        result = event.get("result", {})
        state = "ERROR" if isinstance(result, dict) and result.get("error") else str(result.get("status", "done")).upper() if isinstance(result, dict) else "DONE"
        with st.expander(f'{index:02d} · {event.get("tool", "unknown")} · {state}', expanded=state in {"ERROR", "PARTIAL", "BLOCKED"}):
            st.caption("Arguments và kết quả thực thi · đã che dữ liệu nhạy cảm")
            st.json(event, expanded=False)
    if turn.get("error"):
        st.error("Provider error · lượt này chưa hoàn thành.")
        st.json(turn["error"])
    if not turn.get("tool_events") and not turn.get("error"):
        st.caption("Lượt này không gọi tool.")
