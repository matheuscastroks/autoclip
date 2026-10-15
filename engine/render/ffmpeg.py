import shutil,subprocess,tempfile
from pathlib import Path
from engine.contracts import Source,EDLArtifact,CropArtifact,CaptionArtifact,ExportConfig,RenderArtifact,PipelineError
from engine.pipeline.artifacts import file_hash

class FFmpegRenderer:
    def __init__(self,ffmpeg:Path,run=subprocess.run,progress=None): self.ffmpeg=Path(ffmpeg);self.run=run;self.progress=progress

    def render(self,source:Source,edl:EDLArtifact,crop:CropArtifact,captions:CaptionArtifact,config:ExportConfig) -> RenderArtifact:
        if edl.source_id!=source.id or crop.source_id!=source.id or crop.edl_revision_id!=edl.revision_id or captions.edl_revision_id!=edl.revision_id:
            raise PipelineError('UNSAFE_EDIT','render','Render inputs belong to different revisions.')
        profile=config.profile
        width,height,fps=profile.width,profile.height,profile.fps
        root=Path(config.output_root).resolve();root.mkdir(parents=True,exist_ok=True)
        output=root/(str(edl.revision_id)+'.mp4')
        if output.exists(): raise PipelineError('OUTPUT_EXISTS','render','This revision already has a render; use cache or create a new revision.')
        origin=source.probe.get('video_origin_us',0)/1e6
        vf=source.probe.get('video_stream_index',0);af=source.probe.get('audio_stream_index',1)
        filters=[];inputs=[]
        for i,span in enumerate(edl.spans):
            start=origin+span.source_start_us/1e6;end=origin+span.source_end_us/1e6
            filters.append(f'[0:{vf}]fps={fps}:start_time={origin:.6f},trim=start={start:.6f}:end={end:.6f},setpts=PTS-{start:.6f}/TB[v{i}]')
            filters.append(f'[0:{af}]atrim=start={start:.6f}:end={end:.6f},asetpts=PTS-{start:.6f}/TB,aresample=48000:async=1:first_pts=0,apad,atrim=duration={(span.output_end_us-span.output_start_us)/1e6:.6f}[a{i}]')
            inputs.append(f'[v{i}][a{i}]')
        filters.append(''.join(inputs)+f'concat=n={len(edl.spans)}:v=1:a=1[vbase][aout]')
        x=f'(iw-{width})/2'
        if crop.mode=='face-track':
            from engine.media.face_tracking import crop_expression
            if crop.points[-1].output_us>=edl.duration_us:raise PipelineError('UNSAFE_EDIT','render','Crop path exceeds output timeline.')
            x="'"+crop_expression(crop.points,width=width)+"'"
        duration=edl.duration_us/1e6
        fades=f',fade=t=in:st=0:d={min(.2,duration/3):.6f},fade=t=out:st={max(0,duration-min(.3,duration/3)):.6f}:d={min(.3,duration/3):.6f}'
        filters.append(f'[vbase]scale={width}:{height}:force_original_aspect_ratio=increase:force_divisible_by=2,crop={width}:{height}:{x}:(ih-{height})/2,setsar=1,ass=filename=captions.ass:fontsdir=fonts{fades},fps={fps},format=yuv420p[vout]')
        with tempfile.TemporaryDirectory(prefix='.render-',dir=root) as stage:
            stage=Path(stage);shutil.copyfile(captions.ass_path,stage/'captions.ass')
            (stage/'fonts').mkdir()
            font=Path(captions.font)
            if font.is_file(): shutil.copyfile(font,stage/'fonts'/font.name)
            (stage/'filter.txt').write_text(';'.join(filters),encoding='utf-8')
            temp=stage/'result.mp4'
            args=[str(self.ffmpeg),'-nostdin','-hide_banner','-v','error','-y','-copyts','-threads','2','-i',str(source.local_path),'-filter_complex_threads','2','-filter_complex',';'.join(filters),'-map','[vout]','-map','[aout]','-t',f'{edl.duration_us/1e6:.6f}','-c:v',profile.codec,'-threads','2','-preset',profile.preset,'-crf',str(profile.crf),'-pix_fmt','yuv420p','-c:a','aac','-b:a',f'{profile.audio_kbps}k','-ar','48000','-r',str(fps),'-map_metadata','-1','-metadata:s:v:0','rotate=0','-movflags','+faststart',str(temp)]
            if crop.mode=='face-track':
                index=args.index('-filter_complex');args[index:index+2]=['-/filter_complex','filter.txt']
            extra={}
            if self.progress:
                from engine.pipeline.progress import RenderProgress
                args[1:1]=['-progress','pipe:1','-nostats']
                extra['on_stdout_line']=RenderProgress(edl.duration_us,self.progress).line
            result=self.run(args,cwd=stage,capture_output=True,text=True,encoding='utf-8',shell=False,**extra)
            if result.returncode or not temp.is_file() or not temp.stat().st_size:
                log=root/(str(edl.revision_id)+'.error.log')
                log.write_text(result.stderr or 'No output produced.',encoding='utf-8')
                raise PipelineError('RENDER_FAILED','render',f'FFmpeg render failed; see {log}. Partial output discarded.')
            digest=file_hash(temp);size=temp.stat().st_size
            temp.replace(output)
        return RenderArtifact(revision_id=edl.revision_id,path=output,sha256=digest,size_bytes=size)
