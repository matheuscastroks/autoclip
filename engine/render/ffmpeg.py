import shutil,subprocess,tempfile
from pathlib import Path
from engine.contracts import Source,EDLArtifact,CropArtifact,CaptionArtifact,ExportConfig,RenderArtifact,PipelineError
from engine.pipeline.artifacts import file_hash

class FFmpegRenderer:
    def __init__(self,ffmpeg:Path,run=subprocess.run): self.ffmpeg=Path(ffmpeg);self.run=run

    def render(self,source:Source,edl:EDLArtifact,crop:CropArtifact,captions:CaptionArtifact,config:ExportConfig) -> RenderArtifact:
        if edl.source_id!=source.id or crop.source_id!=source.id or crop.edl_revision_id!=edl.revision_id or captions.edl_revision_id!=edl.revision_id:
            raise PipelineError('UNSAFE_EDIT','render','Render inputs belong to different revisions.')
        root=Path(config.output_root).resolve();root.mkdir(parents=True,exist_ok=True)
        output=root/(str(edl.revision_id)+'.mp4')
        if output.exists(): raise PipelineError('OUTPUT_EXISTS','render','This revision already has a render; use cache or create a new revision.')
        origin=source.probe.get('video_origin_us',0)/1e6
        vf=source.probe.get('video_stream_index',0);af=source.probe.get('audio_stream_index',1)
        filters=[];inputs=[]
        for i,span in enumerate(edl.spans):
            start=origin+span.source_start_us/1e6;end=origin+span.source_end_us/1e6
            filters.append(f'[0:{vf}]trim=start={start:.6f}:end={end:.6f},setpts=PTS-STARTPTS[v{i}]')
            filters.append(f'[0:{af}]atrim=start={start:.6f}:end={end:.6f},asetpts=PTS-{start:.6f}/TB,aresample=48000:async=1:first_pts=0,apad,atrim=duration={(span.output_end_us-span.output_start_us)/1e6:.6f}[a{i}]')
            inputs.append(f'[v{i}][a{i}]')
        filters.append(''.join(inputs)+f'concat=n={len(edl.spans)}:v=1:a=1[vbase][aout]')
        filters.append('[vbase]split=2[bg][fg]')
        filters.append('[bg]scale=1080:1920:force_original_aspect_ratio=increase,crop=1080:1920,boxblur=20:2[back]')
        filters.append('[fg]scale=1080:1920:force_original_aspect_ratio=decrease:force_divisible_by=2[front]')
        filters.append('[back][front]overlay=(W-w)/2:(H-h)/2,setsar=1,ass=filename=captions.ass:fontsdir=fonts,fps=30,format=yuv420p[vout]')
        with tempfile.TemporaryDirectory(prefix='.render-',dir=root) as stage:
            stage=Path(stage);shutil.copyfile(captions.ass_path,stage/'captions.ass')
            (stage/'fonts').mkdir()
            font=Path(captions.font)
            if font.is_file(): shutil.copyfile(font,stage/'fonts'/font.name)
            (stage/'filter.txt').write_text(';'.join(filters),encoding='utf-8')
            temp=stage/'result.mp4'
            args=[str(self.ffmpeg),'-nostdin','-hide_banner','-v','error','-y','-copyts','-i',str(source.local_path),'-filter_complex',';'.join(filters),'-map','[vout]','-map','[aout]','-t',f'{edl.duration_us/1e6:.6f}','-c:v','libx264','-preset','medium','-crf',str(config.crf),'-pix_fmt','yuv420p','-c:a','aac','-b:a','192k','-ar','48000','-r','30','-map_metadata','-1','-metadata:s:v:0','rotate=0','-movflags','+faststart',str(temp)]
            result=self.run(args,cwd=stage,capture_output=True,text=True,encoding='utf-8',shell=False)
            if result.returncode or not temp.is_file() or not temp.stat().st_size:
                log=root/(str(edl.revision_id)+'.error.log')
                log.write_text(result.stderr or 'No output produced.',encoding='utf-8')
                raise PipelineError('RENDER_FAILED','render',f'FFmpeg render failed; see {log}. Partial output discarded.')
            digest=file_hash(temp);size=temp.stat().st_size
            temp.replace(output)
        return RenderArtifact(revision_id=edl.revision_id,path=output,sha256=digest,size_bytes=size)
