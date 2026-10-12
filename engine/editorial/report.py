import html,json
from pathlib import Path
from engine.contracts import ProjectRun,TranscriptArtifact,EDLArtifact,Candidate

def create_report(root:Path) -> Path:
    root=Path(root).resolve();state=ProjectRun.model_validate_json((root/'project.json').read_bytes())
    transcript=TranscriptArtifact.model_validate_json((root/'transcript.json').read_bytes())
    parts=['<!doctype html><html lang="pt-BR"><meta charset="utf-8"><meta name="viewport" content="width=device-width"><title>Revisão da PoC</title><style>body{font:18px system-ui;max-width:1000px;margin:32px auto;padding:0 20px;background:#fafafa;color:#222}video{max-width:100%;max-height:600px}section{border-top:1px solid #ccc;padding:24px 0}pre{white-space:pre-wrap}code{font-size:14px}</style><h1>Revisão — OpenShorts + Gemini</h1><p>Preview técnico. Aprovação editorial exige ouvir fonte e corte com contexto. Fit-blur preserva o quadro; tracking e remoção de pausas estão fora desta PoC.</p>']
    parts.append('<p>'+html.escape(state.source.attribution)+'</p>')
    for r in state.revisions:
        folder=root/'revisions'/r['revision_id'];e=EDLArtifact.model_validate_json((folder/'edl.json').read_bytes());c=Candidate.model_validate_json((folder/'candidate.json').read_bytes())
        start,end=e.spans[0].source_start_us/1e6,e.spans[-1].source_end_us/1e6
        context=' '.join(w.text for w in transcript.words if max(0,start-30)*1e6<=w.start_us<(end+30)*1e6)
        parts.append(f'<section><h2>{html.escape(c.title_suggestion or "Corte manual de teste")}</h2><p>{html.escape(c.rationale)}</p><p>Origem: {start:.3f}–{end:.3f} s. Revisão {html.escape(r["revision_id"])}.</p><video controls src="{html.escape(Path(r["render_path"]).as_uri(),quote=True)}"></video><h3>Fonte com contexto</h3><video controls src="{html.escape(state.source.local_path.as_uri(),quote=True)}#t={max(0,start-30):.3f},{end+30:.3f}"></video><pre>{html.escape(context)}</pre><p>Estado: {html.escape(r["review_status"])}. Use a CLI approve para confirmar cada critério humano.</p></section>')
    parts.append('</html>');out=root/'review.html';out.write_text('\n'.join(parts),encoding='utf-8');return out
