from pathlib import Path
from engine.adapters.gemini.credentials import get_gemini_key,set_gemini_key
from engine.pipeline.artifacts import atomic_json
from engine.media.probe import locate_tools
from engine.contracts import PipelineError
from .projects import read_json

class Settings:
    def __init__(self,workspace):self.workspace=Path(workspace);self.path=self.workspace/'.autoclip/settings.json'

    def get(self):
        try:ffmpeg,ffprobe=locate_tools()
        except PipelineError:ffmpeg=ffprobe=Path('')
        values={'asr_model_path':str(self.workspace/'research/models/whisper-small'),'gemini_model':'gemini-2.5-flash',
            'max_calls':10,'window_seconds':600,'max_text_chars':60000,'ffmpeg':str(ffmpeg),'ffprobe':str(ffprobe)}
        values.update(read_json(self.path,{}) or {})
        try:get_gemini_key();configured=True
        except PipelineError:configured=False
        return {**values,'gemini_key_configured':configured,'asr_available':(Path(values['asr_model_path'])/'model.bin').is_file(),
            'tools_available':Path(values['ffmpeg']).is_file() and Path(values['ffprobe']).is_file(),'schema_version':'1.0'}

    def save(self,values):
        atomic_json(self.path,values);return self.get()
