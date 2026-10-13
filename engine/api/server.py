import json,sys
from pathlib import Path
import uvicorn
from .app import create_app

def serve(workspace: Path):
    session=json.loads((workspace/'.autoclip/session.json').read_text(encoding='utf-8'))
    app=create_app(workspace,session['token'])
    config=uvicorn.Config(app,host='127.0.0.1',port=session['port'],access_log=False,log_level='warning')
    server=uvicorn.Server(config);app.state.shutdown=lambda:setattr(server,'should_exit',True)
    server.run()

def main():
    serve(Path(sys.argv[1]).resolve())

if __name__=='__main__':main()
