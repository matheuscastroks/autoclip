from pathlib import Path
from engine.adapters.gemini.credentials import get_gemini_key,set_gemini_key
from engine.adapters.openrouter import credentials as openrouter_credentials
from engine.pipeline.artifacts import atomic_json
from engine.media.probe import locate_tools
from engine.contracts import PipelineError
from .projects import read_json

class Settings:
    def __init__(self,workspace):self.workspace=Path(workspace);self.path=self.workspace/'.autoclip/settings.json'

    def _resolve_asr_model(self,current:str)->str:
        if current and (Path(current)/'model.bin').is_file():return current
        dev=self.workspace/'research/models/whisper-small'
        if (dev/'model.bin').is_file():return str(dev)
        bases=[self.workspace/'models']
        try:
            from engine.system.provisioner import get_storage_base
            bases.append(get_storage_base()/'models')
        except Exception:pass
        for base in bases:
            for name in ('whisper-small','whisper-large-v3-turbo','whisper-base'):
                candidate=base/name
                if (candidate/'model.bin').is_file():return str(candidate)
        return current or str(dev)

    def get(self):
        try:ffmpeg,ffprobe=locate_tools()
        except PipelineError:ffmpeg=ffprobe=Path('')
        values={'asr_model_path':str(self.workspace/'research/models/whisper-small'),'gemini_model':'gemini-2.5-flash',
            'max_calls':10,'window_seconds':600,'max_text_chars':60000,'ffmpeg':str(ffmpeg),'ffprobe':str(ffprobe),
            'clip_preferred_seconds':180,'clip_max_seconds':300,'clip_policy_version':2,'pause_mode':'conservative','show_thought_summaries':True,
            'ai_provider':'gemini','openrouter_model':'openrouter/free'}
        saved=read_json(self.path,{}) or {}
        values.update(saved)
        if not (values.get('ffmpeg') and Path(values['ffmpeg']).is_file() and values.get('ffprobe') and Path(values['ffprobe']).is_file()) and ffmpeg.is_file() and ffprobe.is_file():
            values.update(ffmpeg=str(ffmpeg),ffprobe=str(ffprobe))
        values['asr_model_path']=self._resolve_asr_model(values.get('asr_model_path',''))
        if saved.get('clip_policy_version')!=2:
            values.update(clip_preferred_seconds=180,clip_max_seconds=300,clip_policy_version=2)
        try:get_gemini_key();configured=True
        except PipelineError:configured=False
        try:openrouter_credentials.get_openrouter_key();or_configured=True
        except PipelineError:or_configured=False
        return {**values,'gemini_key_configured':configured,'openrouter_key_configured':or_configured,
            'asr_available':(Path(values['asr_model_path'])/'model.bin').is_file(),
            'tools_available':Path(values['ffmpeg']).is_file() and Path(values['ffprobe']).is_file(),'schema_version':'1.0'}

    def save(self,values):
        atomic_json(self.path,values);return self.get()

