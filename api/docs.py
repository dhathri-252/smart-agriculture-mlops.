"""Custom documentation pages for the Smart Agriculture Prediction API.

Small HTML/CSS customization over stock Swagger UI and ReDoc.
No extra dependencies.
"""

from fastapi.responses import HTMLResponse


def swagger_ui_html():
    return HTMLResponse(
        """<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8"/>
<meta name="viewport" content="width=device-width, initial-scale=1"/>
<title>Smart Agriculture Prediction API</title>
<link rel="icon" href="https://cdn.jsdelivr.net/gh/twitter/twemoji@14.0.2/assets/72x72/1f331.png"/>
<link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/swagger-ui-dist@5/swagger-ui.css"/>
<style>
/* Keep Swagger default font stack exactly; layout/accents only. */
html{background:#f1f7f2}
body{margin:0;background:#f1f7f2}
.agri-page{max-width:1020px;margin:0 auto;padding:26px 22px 46px}
.agri-header{background:linear-gradient(120deg,#1b4332 0%,#2d6a4f 58%,#2a9d8f 100%);color:#fff;border-radius:16px;padding:26px 26px 22px;box-shadow:0 10px 26px rgba(27,67,50,.18)}
.agri-top{display:flex;gap:14px;align-items:center}
.agri-logo{width:52px;height:52px;border-radius:13px;display:flex;align-items:center;justify-content:center;background:rgba(255,255,255,.16);border:1px solid rgba(255,255,255,.28)}
.agri-title{margin:0}
.agri-title small{display:block;opacity:.85;letter-spacing:2px;text-transform:uppercase}
.agri-desc{margin:10px 0 0;opacity:.93;line-height:1.6;max-width:760px}
.agri-meta{display:flex;gap:8px;flex-wrap:wrap;margin-top:14px}
.agri-pill{background:rgba(255,255,255,.16);border:1px solid rgba(255,255,255,.30);border-radius:999px;padding:5px 12px}
.agri-pill.solid{background:#fff;color:#1b4332;border-color:#fff}
.agri-online{display:inline-flex;align-items:center;gap:7px;background:#fff;color:#1b4332;border-radius:999px;padding:5px 12px}
.agri-dot{width:9px;height:9px;border-radius:50%;background:#2d9d5f}
.agri-nav{display:grid;grid-template-columns:1fr 1fr 1.25fr;gap:12px;margin:16px 0 6px}
.agri-card{background:#fff;border:1px solid #dcebe1;border-radius:13px;padding:14px 15px;box-shadow:0 6px 18px rgba(27,67,50,.07)}
.agri-card h3{margin:0 0 6px;color:#1b4332}
.agri-card p{margin:4px 0;color:#5d7267;line-height:1.55}
.agri-card code{background:#eef6f0;border:1px solid #dcebe1;border-radius:6px;padding:1px 6px;color:#1b4332}
.agri-card.hl{border:2px solid #2d6a4f;background:#f3faf5}
.m{display:inline-block;color:#fff;border-radius:6px;padding:2px 8px;margin-right:6px}
.m.get{background:#40916c}.m.post{background:#2a9d8f}
#swagger-ui{background:#fff;border:1px solid #dcebe1;border-radius:16px;padding:18px 18px 8px;margin-top:12px;box-shadow:0 8px 24px rgba(27,67,50,.08)}
/* Compact default Swagger whitespace without touching fonts. */
#swagger-ui .info{margin:14px 0 10px}
#swagger-ui .info hgroup.main a{color:#1b4332}
#swagger-ui .scheme-container{margin:0 0 10px;padding:12px 14px;background:#f3faf5;border:1px solid #dcebe1;border-radius:12px;box-shadow:none}
#swagger-ui .opblock-tag{border-bottom:1px solid #e3efe6;padding:14px 4px 10px;margin:0}
#swagger-ui .opblock-tag p{color:#5d7267}
#swagger-ui .opblock{border-radius:12px;margin:0 0 10px;box-shadow:0 3px 12px rgba(27,67,50,.06)}
#swagger-ui .opblock.opblock-get{border-color:#bfe0cc;background:rgba(64,145,108,.06)}
#swagger-ui .opblock.opblock-post{border:2px solid #2d6a4f;background:#f3faf5;box-shadow:0 6px 18px rgba(45,106,79,.16)}
#swagger-ui .opblock .opblock-summary{padding:10px 12px}
#swagger-ui table.model, #swagger-ui section.models{border-color:#dcebe1}
#swagger-ui section.models{border:1px solid #dcebe1;border-radius:12px;background:#fff;margin:14px 0;box-shadow:none}
#swagger-ui section.models h4{color:#1b4332}
#swagger-ui .btn.execute{background:#2d6a4f;border-color:#2d6a4f}
#swagger-ui .btn.authorize{border-color:#2d6a4f;color:#2d6a4f}
.agri-foot{text-align:center;color:#5d7267;padding:18px 0 0}
@media(max-width:860px){.agri-page{padding:16px 12px 34px}.agri-nav{grid-template-columns:1fr}#swagger-ui{padding:12px 10px 4px}}
</style>
</head>
<body>
<div class="agri-page">
<header class="agri-header">
<div class="agri-top"><div class="agri-logo">🌱</div><div>
<h2 class="agri-title"><small>Smart Agriculture</small>Prediction API</h2>
</div></div>
<p class="agri-desc">AI-powered crop recommendation API for the Smart Agriculture Prediction System.</p>
<div class="agri-meta"><span class="agri-pill solid">Version 1.0.0</span><span class="agri-online"><span class="agri-dot"></span>API Online</span><span class="agri-pill">🌾 Random Forest</span><span class="agri-pill">System · Health · Crop Prediction</span></div>
</header>
<div class="agri-nav">
<div class="agri-card"><h3>1 · SYSTEM</h3><p><span class="m get">GET</span><code>/</code></p><p>Smart Agriculture API</p></div>
<div class="agri-card"><h3>2 · HEALTH</h3><p><span class="m get">GET</span><code>/health</code></p><p>Health Check</p></div>
<div class="agri-card hl"><h3>⭐ 3 · CROP PREDICTION</h3><p><span class="m post">POST</span><code>/predict</code></p><p><strong>Crop Prediction</strong> — main AI functionality.</p></div>
</div>
<div id="swagger-ui"></div>
<div class="agri-foot">🌱 Smart Agriculture Prediction API v1.0.0 · POST /predict returns { "recommended_crop": "rice" }</div>
</div>
<script src="https://cdn.jsdelivr.net/npm/swagger-ui-dist@5/swagger-ui-bundle.js"></script>
<script src="https://cdn.jsdelivr.net/npm/swagger-ui-dist@5/swagger-ui-standalone-preset.js"></script>
<script>
const ui = SwaggerUIBundle({ url: '/openapi.json', dom_id: '#swagger-ui', layout: 'StandaloneLayout', deepLinking: true, showExtensions: true, showCommonExtensions: true, presets: [SwaggerUIBundle.presets.apis, SwaggerUIStandalonePreset] });
</script>
</body>
</html>"""
    )


def redoc_html():
    return HTMLResponse(
        """<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8"/>
<meta name="viewport" content="width=device-width, initial-scale=1"/>
<title>Smart Agriculture Prediction API - ReDoc</title>
<link rel="icon" href="https://cdn.jsdelivr.net/gh/twitter/twemoji@14.0.2/assets/72x72/1f331.png"/>
<style>
:root{--g900:#1b4332;--g700:#2d6a4f;--g600:#40916c;--teal:#2a9d8f;--bg:#f1f7f2;--muted:#5d7267}
*{box-sizing:border-box}
html{background:#f1f7f2}
body{margin:0;font-family:-apple-system,BlinkMacSystemFont,"Segoe UI",Roboto,Helvetica,Arial,sans-serif;background:var(--bg);color:#1a2e24}
.agri-page{max-width:1020px;margin:0 auto;padding:26px 22px 46px}
.agri-hero{background:linear-gradient(120deg,#1b4332 0%,#2d6a4f 58%,#2a9d8f 100%);color:#fff;border-radius:16px;padding:26px 26px 22px;box-shadow:0 10px 26px rgba(27,67,50,.18)}
.agri-inner{max-width:100%;margin:0 auto}
.agri-brand{display:flex;align-items:center;gap:14px;flex-wrap:wrap}
.agri-logo{width:52px;height:52px;border-radius:13px;display:flex;align-items:center;justify-content:center;background:rgba(255,255,255,.16);border:1px solid rgba(255,255,255,.28)}
.agri-brand h1{margin:0}
.agri-brand h1 small{display:block;opacity:.85;letter-spacing:2px;text-transform:uppercase}
.agri-brand p{margin:10px 0 0;opacity:.93;max-width:760px;line-height:1.6}
.agri-badges{display:flex;gap:8px;margin-top:14px;flex-wrap:wrap}
.agri-badge{background:rgba(255,255,255,.16);border:1px solid rgba(255,255,255,.30);border-radius:999px;padding:5px 12px}
.agri-badge.solid{background:#fff;color:#1b4332;border-color:#fff}
.agri-online{display:inline-flex;align-items:center;gap:7px;background:#fff;color:#1b4332;border-radius:999px;padding:5px 12px}
.agri-dot{width:9px;height:9px;border-radius:50%;background:#2d9d5f}
.agri-links{display:flex;gap:10px;margin-top:14px;flex-wrap:wrap}
.agri-links a{color:#fff;text-decoration:none;background:rgba(255,255,255,.14);border:1px solid rgba(255,255,255,.3);padding:8px 14px;border-radius:10px}
.agri-strip{max-width:100%;margin:16px 0 6px;padding:0;display:grid;grid-template-columns:1fr 1fr 1.25fr;gap:12px}
.agri-card{background:#fff;border:1px solid #dcebe1;border-radius:13px;padding:14px 15px;box-shadow:0 6px 18px rgba(27,67,50,.07)}
.agri-card h2{margin:0 0 6px;color:#1b4332}
.agri-card p{color:var(--muted);line-height:1.55;margin:4px 0}
.agri-card code{background:#eef6f0;border:1px solid #dcebe1;padding:1px 6px;border-radius:6px;color:#1b4332}
.agri-card pre{background:#0f241c;color:#d8f3dc;border-radius:10px;padding:12px 14px;overflow:auto;margin:10px 0 0;line-height:1.6}
.agri-card.hl{border:2px solid #2d6a4f;background:#f3faf5}
.m{display:inline-block;color:#fff;border-radius:6px;padding:2px 8px;margin-right:6px}
.m.post{background:#2a9d8f}.m.get{background:#40916c}
#redoc-container{max-width:100%;margin:12px 0 0;padding:0}
redoc{display:block;background:#fff;border:1px solid #dcebe1;border-radius:16px;overflow:hidden;box-shadow:0 8px 24px rgba(27,67,50,.08)}
redoc img{max-width:100%}
.agri-footer{text-align:center;color:var(--muted);padding:18px 0 0}
@media(max-width:860px){.agri-page{padding:16px 12px 34px}.agri-strip{grid-template-columns:1fr}}
</style>
</head>
<body>
<div class="agri-page">
<header class="agri-hero"><div class="agri-inner">
<div class="agri-brand"><div class="agri-logo">🌱</div><div>
<h1><small>Smart Agriculture</small>Smart Agriculture Prediction API</h1>
<p>AI-powered crop recommendation API for the Smart Agriculture Prediction System.</p>
</div></div>
<div class="agri-badges"><span class="agri-badge solid">Version 1.0.0</span><span class="agri-online"><span class="agri-dot"></span>API Online</span><span class="agri-badge">🌾 Random Forest</span><span class="agri-badge">System · Health · Crop Prediction</span></div>
<div class="agri-links"><a href="/api-docs">Swagger UI (/api-docs)</a><a href="/openapi.json">OpenAPI JSON</a><a href="#operation/predict_predict_post">Core endpoint: POST /predict</a></div>
</div></header>
<div class="agri-strip">
<div class="agri-card"><h2>1 · SYSTEM</h2>
<p><span class="m get">GET</span><code>/</code></p><p>Smart Agriculture API — confirms the API is running.</p></div>
<div class="agri-card"><h2>2 · HEALTH</h2>
<p><span class="m get">GET</span><code>/health</code></p><p>Health Check — service availability check.</p></div>
<div class="agri-card hl"><h2>⭐ 3 · PREDICTION</h2>
<p><span class="m post">POST</span><code>/predict</code></p><p><strong>Crop Prediction</strong> — main AI functionality.</p>
<pre>{
  "N": 90, "P": 42, "K": 43, "temperature": 20.87,
  "humidity": 82, "ph": 6.50, "rainfall": 202.93
} → { "recommended_crop": "rice" }</pre></div>
</div>
<div id="redoc-container">
<redoc spec-url="/openapi.json" scroll-y-offset="60" hide-download-button expand-responses="200" required-props-first="true" show-object-schema-examples="true" hide-single-request-sample-tab="true" sort-operations-definition-by="tags" sort-tags="false" theme='{"spacing":{"sectionVertical":24,"unit":5},"colors":{"primary":{"main":"#2d6a4f"},"http":{"get":"#40916c","post":"#2a9d8f"},"rightPanel":{"backgroundColor":"#1b4332"}},"sidebar":{"backgroundColor":"#f1f7f2","width":"270px"}}'></redoc>
</div>
<div class="agri-footer">🌱 Smart Agriculture Prediction API v1.0.0 · POST /predict returns { "recommended_crop": "rice" }</div>
</div>
<script src="https://cdn.redoc.ly/redoc/latest/bundles/redoc.standalone.js"></script>
</body>
</html>"""
    )
