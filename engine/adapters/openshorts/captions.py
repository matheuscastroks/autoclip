from pathlib import Path
from engine.contracts import TranscriptArtifact, EDLArtifact, CaptionRevision, CaptionConfig, CaptionArtifact, CaptionWord, PipelineError
from engine.editorial.edl import output_at
from engine.render.presets import get_preset
from vendor.openshorts.subtitles import generate_ass_from_captions, generate_srt_from_captions


class OpenShortsCaptionBuilder:
    def __init__(self, root: Path):
        self.root = Path(root)

    def build(self, transcript: TranscriptArtifact, edl: EDLArtifact, revision: CaptionRevision, config: CaptionConfig) -> CaptionArtifact:
        if transcript.transcript_id != edl.transcript_id:
            raise PipelineError('UNSAFE_EDIT', 'captions', 'Transcript revision mismatch.')
        ws = {w.id: w for w in transcript.words}
        if not set(revision.edits).issubset(ws):
            raise PipelineError('INVALID_CAPTION', 'captions', 'Unknown edited word ID.')
        preset = get_preset(getattr(config, 'preset_id', None) or config.style_id)
        spec = preset.caption
        words = []
        for wid in edl.protected_word_ids:
            if wid not in ws:
                raise PipelineError('UNSAFE_EDIT', 'captions', 'Protected word missing.')
            w = ws[wid]
            span = next((s for s in edl.spans if s.source_start_us <= w.start_us and w.end_us <= s.source_end_us), None)
            if span is None:
                raise PipelineError('UNSAFE_EDIT', 'captions', 'Protected word is cut.')
            text = revision.edits.get(wid, w.text).strip()
            if not text:
                raise PipelineError('INVALID_CAPTION', 'captions', 'Empty display text must be reviewed explicitly.')
            if spec.uppercase:
                text = text.upper()
            if len(text.split()) > spec.max_words:
                raise PipelineError('INVALID_CAPTION', 'captions', 'A display token exceeds the configured word limit.')
            start_us = output_at(edl, w.start_us)
            end_us = output_at(edl, w.end_us)
            if start_us is None or end_us is None or end_us <= start_us:
                start_us = span.output_start_us + (w.start_us - span.source_start_us) * span.speed_den // span.speed_num
                end_us = max(start_us + 1, span.output_start_us + (w.end_us - span.source_start_us) * span.speed_den // span.speed_num)
            words.append(CaptionWord(source_word_id=wid, display_text=text, start_us=start_us, end_us=end_us))
        folder = self.root / str(edl.revision_id) / str(revision.revision_id)
        folder.mkdir(parents=True, exist_ok=False)
        ass, srt = folder / 'captions.ass', folder / 'captions.srt'
        # Upstream consumes milliseconds; contract retains original microseconds.
        payload = [{'text': w.display_text, 'startMs': w.start_us // 1000, 'endMs': w.end_us // 1000} for w in words]
        if not payload:
            raise PipelineError('INVALID_CAPTION', 'captions', 'No caption words.')
        generate_ass_from_captions(
            payload,
            str(ass),
            max_chars=spec.max_chars,
            max_duration=spec.max_duration,
            alignment=spec.alignment,
            fontsize=spec.fontsize,
            font_name=spec.font_name,
            font_color=spec.font_color,
            border_color=spec.border_color,
            border_width=spec.border_width,
            highlight_color=spec.highlight_color,
            bg_color=spec.bg_color,
            bg_opacity=spec.bg_opacity,
            effect=spec.effect,
            uppercase=spec.uppercase,
            margin_v=spec.margin_v,
            letter_spacing=spec.letter_spacing,
            max_words=spec.max_words,
            mode=spec.mode,
            bold=spec.bold,
            shadow=spec.shadow,
            fade_ms=spec.fade_ms,
            accent_prefix=spec.accent_prefix,
        )
        generate_srt_from_captions(
            payload,
            str(srt),
            max_chars=spec.max_chars,
            max_duration=spec.max_duration,
            max_words=spec.max_words,
        )
        from engine.render.opening import add_opening, normalize_opening
        opening_text = normalize_opening(config.opening_text)
        opening_duration = min(edl.duration_us, config.opening_seconds * 1_000_000) if opening_text else 0
        if opening_duration:
            add_opening(ass, opening_text, opening_duration, spec.font_name, preset_id=preset.id)
        return CaptionArtifact(
            transcript_id=transcript.transcript_id,
            edl_revision_id=edl.revision_id,
            revision_id=revision.revision_id,
            words=words,
            ass_path=ass.resolve(),
            srt_path=srt.resolve(),
            font=str(config.font_path) if config.font_path else spec.font_name,
            style_id=preset.id,
            opening_text=opening_text,
            opening_duration_us=opening_duration,
        )
