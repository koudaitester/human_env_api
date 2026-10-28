from fastapi import APIRouter
from fastapi.responses import HTMLResponse, StreamingResponse
from utils.sse_log_helper import log_stream_generator

router = APIRouter()

@router.get("/logs/stream")
async def stream_logs():
    return StreamingResponse(log_stream_generator(), media_type="text/event-stream")

@router.get("", response_class=HTMLResponse)
async def logview_page():
    html = """
<!DOCTYPE html>
<html>
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<style>
*{box-sizing:border-box}
body{background:#111;color:#87cefa;font-family:Menlo,Monaco,monospace;padding:8px;font-size:12px;margin:0}
#log{white-space:pre-wrap;word-break:break-all;height:90vh;overflow-y:auto}
.line{padding:2px 0}
.err{color:#ff6b6b}
.warn{color:#ffd166}
.info{color:#87cefa}
</style>
</head>
<body>
<div id="log"></div>
<script>
const evt = new EventSource('/api/v1/logview/logs/stream');
const box = document.getElementById('log');
evt.onmessage = e=>{
    const div = document.createElement('div');
    div.className = 'line info';
    let t = e.data;
    if(t.includes('ERROR')||t.includes('error')) div.className='line err';
    else if(t.includes('WARN')||t.includes('warn')) div.className='line warn';
    div.innerText = t;
    box.appendChild(div);
    box.scrollTop = box.scrollHeight;
}
</script>
</body>
</html>
"""
    return html
