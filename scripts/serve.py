import json, os, secrets, socket, sys, webbrowser
from pathlib import Path

root = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(root))

import uvicorn
from engine.api.app import create_app

def main():
    port = 58057
    token = secrets.token_urlsafe(32)
    session = {
        "pid": os.getpid(),
        "port": port,
        "token": token,
        "workspace": str(root),
        "shared": True
    }
    autoclip_dir = root / '.autoclip'
    autoclip_dir.mkdir(exist_ok=True)
    (autoclip_dir / 'session.json').write_text(json.dumps(session), encoding='utf-8')
    url = f"http://127.0.0.1:{port}/#session={token}"
    (autoclip_dir / 'ux-url.txt').write_text(url, encoding='utf-8')
    print(f"AUTOCLIP_SERVER_RUNNING: {url}")
    
    app = create_app(root, token)
    config = uvicorn.Config(app, host='127.0.0.1', port=port, access_log=False, log_level='warning')
    server = uvicorn.Server(config)
    app.state.shutdown = lambda: setattr(server, 'should_exit', True)
    server.run()

if __name__ == '__main__':
    main()
