from pathlib import Path
from typing import Literal
from uuid import UUID, uuid4
from pydantic import BaseModel, ConfigDict, Field, model_validator, model_serializer


class Contract(BaseModel):
    model_config = ConfigDict(extra='forbid', allow_inf_nan=False, validate_assignment=True)
    schema_version: Literal['1.0'] = '1.0'


class Interval(Contract):
    start_us: int = Field(ge=0, strict=True)
    end_us: int = Field(gt=0, strict=True)

    @model_validator(mode='after')
    def ordered(self):
        if self.end_us <= self.start_us:
            raise ValueError('end_us must exceed start_us')
        return self


class Word(Interval):
    id: str = Field(min_length=1)
    text: str = Field(min_length=1)
    probability: float | None = Field(default=None, ge=0, le=1)
    speaker_id: str | None = None


class Segment(Interval):
    id: str
    word_ids: list[str]
    text: str


class Source(Contract):
    id: UUID = Field(default_factory=uuid4)
    sha256: str = Field(pattern=r'^[a-f0-9]{64}$')
    local_path: Path
    kind: Literal['file', 'url'] = 'file'
    original_url: str | None = None
    original_title: str = ''
    channel: str = ''
    attribution: str = ''
    rights_note: str = 'Local evaluation; redistribution not established.'
    duration_us: int = Field(default=0, ge=0)
    probe: dict = Field(default_factory=dict)


class AudioArtifact(Contract):
    source_id: UUID
    source_sha256: str = Field(pattern=r'^[a-f0-9]{64}$')
    path: Path
    sha256: str = Field(pattern=r'^[a-f0-9]{64}$')
    duration_us: int = Field(gt=0)
    sample_rate: Literal[16000] = 16000
    channels: Literal[1] = 1
    source_origin_us: int = 0


class TranscriptArtifact(Contract):
    transcript_id: UUID = Field(default_factory=uuid4)
    source_id: UUID = Field(default_factory=uuid4)
    source_sha256: str = Field(pattern=r'^[a-f0-9]{64}$')
    language: str = 'pt'
    model: dict = Field(default_factory=dict)
    words: list[Word]
    segments: list[Segment] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)

    @model_validator(mode='after')
    def valid_words(self):
        ids = [w.id for w in self.words]
        if len(ids) != len(set(ids)):
            raise ValueError('duplicate word IDs')
        if any(b.start_us < a.start_us for a,b in zip(self.words, self.words[1:])):
            raise ValueError('words must be sorted')
        if any(b.start_us < a.end_us for a,b in zip(self.words, self.words[1:])) and 'overlapping_words' not in self.warnings:
            self.warnings.append('overlapping_words')
        for segment in self.segments:
            if not set(segment.word_ids).issubset(ids):
                raise ValueError('unknown segment word ID')
        return self


class EditorialFlags(Contract):
    completeness: Literal['yes','no','uncertain']
    standalone_context: Literal['yes','no','uncertain']
    qualification_preserved: Literal['yes','no','uncertain']


class Candidate(Contract):
    id: UUID = Field(default_factory=uuid4)
    topic_id: str
    start_word_id: str
    end_word_id: str
    evidence_word_ids: list[str]
    rationale: str
    context_before_word_ids: list[str] = Field(default_factory=list)
    context_after_word_ids: list[str] = Field(default_factory=list)
    editorial: EditorialFlags
    title_suggestion: str = ''
    opening_suggestion: str = Field(default='',max_length=72)
    description_suggestion: str = ''
    warnings: list[str] = Field(default_factory=list)

    @model_serializer(mode='wrap')
    def serialize_compatible(self,handler):
        value=handler(self)
        if not self.opening_suggestion:value.pop('opening_suggestion',None)
        return value


class Topic(Contract):
    id: str
    label: str
    summary: str
    evidence_word_ids: list[str]


class AnalysisArtifact(Contract):
    transcript_id: UUID
    topics: list[Topic] = Field(default_factory=list)
    candidates: list[Candidate] = Field(default_factory=list)
    complete: bool
    covered_word_ids: list[str]
    model: str
    prompt_hash: str
    payload_hashes: list[str]
    responses: list[dict] = Field(default_factory=list)
    clip_min_seconds: int = Field(default=20,ge=20,le=300)

    @model_serializer(mode='wrap')
    def serialize_policy(self,handler):
        value=handler(self)
        if self.clip_min_seconds==20:value.pop('clip_min_seconds',None)
        return value


class CandidateArtifact(Contract):
    transcript_id: UUID
    candidates: list[Candidate]
    rejected: list[dict] = Field(default_factory=list)


PlaybackSpeed = Literal['1x', '1.25x', '1.5x']


class Span(Contract):
    source_start_us: int = Field(ge=0)
    source_end_us: int = Field(gt=0)
    output_start_us: int = Field(ge=0)
    output_end_us: int = Field(gt=0)
    speed_num: Literal[1, 5, 3] = 1
    speed_den: Literal[1, 4, 2] = 1

    @model_validator(mode='after')
    def valid_span(self):
        if self.source_end_us <= self.source_start_us or self.output_end_us <= self.output_start_us:
            raise ValueError('invalid span')
        if (self.speed_num, self.speed_den) not in ((1, 1), (5, 4), (3, 2)):
            raise ValueError('invalid speed ratio')
        expected = (self.source_end_us - self.source_start_us) * self.speed_den // self.speed_num
        if self.output_end_us - self.output_start_us != max(1, expected):
            raise ValueError('span duration mismatch')
        return self


class EDLArtifact(Contract):
    revision_id: UUID = Field(default_factory=uuid4)
    source_id: UUID
    transcript_id: UUID
    policy: Literal['continuous_selection_with_verified_pause_removal'] = 'continuous_selection_with_verified_pause_removal'
    playback_speed: PlaybackSpeed = '1x'
    spans: list[Span]
    removed: list[dict] = Field(default_factory=list)
    protected_word_ids: list[str]
    duration_us: int = Field(gt=0)
    warnings: list[str] = Field(default_factory=list)

    @model_validator(mode='before')
    @classmethod
    def _sync_speed_before(cls, value):
        if not isinstance(value, dict):
            return value
        data = dict(value)
        spans = data.get('spans') or []
        if spans and isinstance(spans[0], dict) and 'playback_speed' not in data:
            num = spans[0].get('speed_num', 1)
            den = spans[0].get('speed_den', 1)
            from engine.render.presets import speed_ratio_to_label
            data['playback_speed'] = speed_ratio_to_label(num, den)
        return data

    @model_validator(mode='after')
    def valid_timeline(self):
        cursor, source_end = 0, 0
        from engine.render.presets import PLAYBACK_SPEED_RATIONAL
        expected_ratio = PLAYBACK_SPEED_RATIONAL.get(self.playback_speed, (1, 1))
        for span in self.spans:
            if span.output_start_us != cursor or span.source_start_us < source_end:
                raise ValueError('timeline gap/overlap/order')
            if (span.speed_num, span.speed_den) != expected_ratio:
                raise ValueError('span speed does not match EDL playback_speed')
            cursor, source_end = span.output_end_us, span.source_end_us
        if cursor != self.duration_us:
            raise ValueError('timeline duration mismatch')
        return self



class CropPoint(Contract):
    output_us: int = Field(ge=0)
    center_x: float = Field(ge=0,le=1)


class CropArtifact(Contract):
    source_id: UUID
    edl_revision_id: UUID
    mode: Literal['fit-blur','center-crop','face-track'] = 'center-crop'
    fallback_reason: str = 'Static central 9:16 crop; face tracking is not enabled.'
    points: list[CropPoint] = Field(default_factory=list)
    model_sha256: str | None = None
    detected_samples: int = Field(default=0,ge=0)
    total_samples: int = Field(default=0,ge=0)

    @model_validator(mode='after')
    def valid_path(self):
        if any(a.output_us>=b.output_us for a,b in zip(self.points,self.points[1:])):
            raise ValueError('crop path must have increasing output timestamps')
        if self.mode=='face-track' and (not self.points or self.points[0].output_us!=0):
            raise ValueError('face track must start at zero')
        return self


class CaptionRevision(Contract):
    revision_id: UUID = Field(default_factory=uuid4)
    edits: dict[str,str] = Field(default_factory=dict)


class CaptionWord(Interval):
    source_word_id: str
    display_text: str


PresetId = Literal['karaoke_yellow','editorial_sober','documentary','impact']
LegacyPresetId = Literal['karaoke_yellow','editorial_sober','documentary','impact','bold-uppercase-v1','karaoke']


class CaptionArtifact(Contract):
    transcript_id: UUID
    edl_revision_id: UUID
    revision_id: UUID
    words: list[CaptionWord]
    ass_path: Path
    srt_path: Path
    font: str
    style_id: LegacyPresetId = 'karaoke_yellow'
    opening_text: str = ''
    opening_duration_us: int = Field(default=0,ge=0)


class EditorialChecks(Contract):
    completeness: bool
    context: bool
    qualifications: bool
    words_and_boundaries: bool
    audiovisual: bool


class ReviewDecision(Contract):
    id: UUID = Field(default_factory=uuid4)
    revision_id: UUID
    decision: Literal['approved','rejected']
    checks: EditorialChecks
    notes: str = ''
    author_kind: Literal['human'] = 'human'
    content_hash: str | None = Field(default=None,pattern=r'^[a-f0-9]{64}$')

    @model_validator(mode='after')
    def approval_checks(self):
        if self.decision == 'approved' and not all(self.checks.model_dump(exclude={'schema_version'}).values()):
            raise ValueError('all human checks required for approval')
        if self.decision == 'approved' and self.content_hash is None:
            raise ValueError('approval must bind the reviewed content hash')
        return self


class RenderArtifact(Contract):
    revision_id: UUID
    path: Path
    sha256: str = Field(pattern=r'^[a-f0-9]{64}$')
    size_bytes: int = Field(gt=0)


class ExportValidation(Contract):
    revision_id: UUID
    technical_pass: bool
    checks: dict
    warnings: list[str] = Field(default_factory=list)


class ArtifactRef(Contract):
    id: UUID = Field(default_factory=uuid4)
    kind: str
    relative_path: str
    sha256: str = Field(pattern=r'^[a-f0-9]{64}$')
    size_bytes: int = Field(gt=0)


class StageRequest(Contract):
    job_id: UUID
    stage: str
    stage_version: str
    inputs: list[ArtifactRef]
    config: dict
    runtime: dict
    cancellation_token_id: UUID


class StageResult(Contract):
    status: Literal['completed','failed','cancelled']
    artifacts: list[ArtifactRef] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)
    metrics: dict = Field(default_factory=dict)
    error: dict | None = None

    @model_validator(mode='after')
    def valid_status(self):
        if (self.status == 'failed') != (self.error is not None):
            raise ValueError('failed requires error; other statuses disallow it')
        return self


class ASRConfig(Contract):
    model_path: Path
    language: Literal['pt'] = 'pt'
    device: Literal['cpu'] = 'cpu'
    compute_type: Literal['int8'] = 'int8'


class AnalysisConfig(Contract):
    model: str = Field(min_length=1)
    prompt_version: Literal['analysis_v1'] = 'analysis_v1'
    timeout_s: int = Field(default=180, ge=1, le=600)
    offline: bool = False
    max_calls: int = Field(ge=1)
    window_seconds: int = Field(default=180,ge=60,le=1800)
    max_text_chars: int = Field(default=12000,ge=1000,le=300000)
    clip_min_seconds: int = Field(default=20,ge=20,le=300)
    clip_preferred_seconds: int = Field(default=180,ge=20,le=300)
    clip_max_seconds: int = Field(default=300,ge=20,le=300)
    show_thought_summaries: bool = True

    @model_validator(mode='after')
    def clip_durations(self):
        if not self.clip_min_seconds<=self.clip_preferred_seconds<=self.clip_max_seconds:raise ValueError('preferred duration exceeds maximum')
        return self


TECHNICAL_CLIP_MIN_SECONDS = 20
TECHNICAL_CLIP_MAX_SECONDS = 600
TECHNICAL_CLIP_MIN_US = TECHNICAL_CLIP_MIN_SECONDS * 1_000_000
TECHNICAL_CLIP_MAX_US = TECHNICAL_CLIP_MAX_SECONDS * 1_000_000


class SelectionConfig(Contract):
    min_us: int = Field(default=TECHNICAL_CLIP_MIN_US, gt=0)
    max_us: int = Field(default=TECHNICAL_CLIP_MAX_US, gt=0, le=TECHNICAL_CLIP_MAX_US)
    max_clips: int = Field(default=10, ge=1, le=10)

    @model_validator(mode='after')
    def durations(self):
        if self.min_us > self.max_us: raise ValueError('min exceeds max')
        return self


class PauseConfig(Contract):
    enabled: bool = False
    min_pause_us: int = Field(default=1_200_000,ge=1_000_000)
    keep_pause_us: int = Field(default=400_000,ge=300_000)
    margin_us: int = Field(default=150_000,ge=100_000)
    noise_db: int = Field(default=-40,ge=-60,le=-35)

    @model_validator(mode='after')
    def safe_margins(self):
        if self.keep_pause_us>=self.min_pause_us:raise ValueError('retained pause must be shorter than threshold')
        return self


class PauseVerification(Contract):
    source_id: UUID
    source_sha256: str = Field(pattern=r'^[a-f0-9]{64}$')
    audio_sha256: str = Field(pattern=r'^[a-f0-9]{64}$')
    silences: list[Interval] = Field(default_factory=list)
    method: str = 'silero-vad-and-quiet-peak'
    warnings: list[str] = Field(default_factory=list)


class CaptionConfig(Contract):
    font_path: Path | None = None
    font_name: str = 'Montserrat ExtraBold'
    preset_id: PresetId = 'karaoke_yellow'
    style_id: LegacyPresetId = 'karaoke_yellow'
    uppercase: bool = True
    max_words: int = Field(default=3,ge=2,le=7)
    font_color: str = Field(default='#FFFFFF',pattern=r'^#[0-9A-Fa-f]{6}$')
    highlight_color: str = Field(default='#FFCC00',pattern=r'^#[0-9A-Fa-f]{6}$')
    border_color: str = Field(default='#000000',pattern=r'^#[0-9A-Fa-f]{6}$')
    border_width: int = Field(default=3,ge=1,le=10)
    opening_text: str = Field(default='',max_length=100)
    opening_seconds: int = Field(default=7,ge=5,le=10)

    @model_validator(mode='before')
    @classmethod
    def _apply_preset(cls, value):
        if not isinstance(value, dict):
            return value
        data = dict(value)
        raw = data.get('preset_id') or data.get('style_id') or data.get('style') or 'karaoke_yellow'
        data.pop('style', None)
        from engine.render.presets import get_preset
        preset = get_preset(raw)
        spec = preset.caption
        data['preset_id'] = preset.id
        data['style_id'] = preset.id
        data['font_name'] = spec.font_name
        data['uppercase'] = spec.uppercase
        data['max_words'] = spec.max_words
        data['font_color'] = spec.font_color
        data['highlight_color'] = spec.highlight_color
        data['border_color'] = spec.border_color
        data['border_width'] = spec.border_width
        return data


class RenderProfile(Contract):
    model_config = ConfigDict(extra='forbid', allow_inf_nan=False, frozen=True)
    name: Literal['preview', 'final'] = 'final'
    width: int = Field(default=1080, gt=0, le=1080)
    height: int = Field(default=1920, gt=0, le=1920)
    fps: Literal[30] = 30
    codec: Literal['libx264'] = 'libx264'
    preset: Literal['veryfast', 'medium'] = 'medium'
    crf: int = Field(default=20, ge=0, le=51)
    audio_kbps: int = Field(default=192, ge=32, le=320)

    @model_validator(mode='after')
    def geometry(self):
        if self.width * 16 != self.height * 9 or self.width % 2 or self.height % 2:
            raise ValueError('Render profile requires even 9:16 dimensions')
        return self


FINAL_PROFILE = RenderProfile()
PREVIEW_PROFILE = RenderProfile(name='preview', width=540, height=960, preset='veryfast', crf=30, audio_kbps=96)


class PreparationArtifact(Contract):
    revision_id: UUID
    candidate_id: UUID
    analysis_hash: str
    source_hash: str
    plan_hash: str
    files: dict[str, str]
    fingerprint: str


class PreviewArtifact(Contract):
    revision_id: UUID
    prepared_hash: str
    render: RenderArtifact
    profile: RenderProfile = PREVIEW_PROFILE
    duration_us: int = Field(gt=0)
    checks: dict[str, bool]


class ExportConfig(Contract):
    width: Literal[1080] = 1080
    height: Literal[1920] = 1920
    fps_num: Literal[30] = 30
    fps_den: Literal[1] = 1
    crf: int = Field(default=20, ge=0, le=51)
    playback_speed: PlaybackSpeed = '1x'
    output_root: Path
    profile: RenderProfile = FINAL_PROFILE

    @model_validator(mode='after')
    def legacy_quality(self):
        if 'profile' not in self.model_fields_set and self.crf != FINAL_PROFILE.crf:
            object.__setattr__(self, 'profile', FINAL_PROFILE.model_copy(update={'crf': self.crf}))
        return self


class ReframeConfig(Contract):
    enabled: bool = True
    model_path: Path | None = None
    sample_fps: int = Field(default=2,ge=1,le=4)
    min_confidence: float = Field(default=.6,ge=.3,le=1)


class PipelineConfig(Contract):
    asr: ASRConfig
    analysis: AnalysisConfig
    selection: SelectionConfig = Field(default_factory=SelectionConfig)
    pauses: PauseConfig = Field(default_factory=PauseConfig)
    captions: CaptionConfig = Field(default_factory=CaptionConfig)
    reframe: ReframeConfig = Field(default_factory=ReframeConfig)
    export: ExportConfig
    ffmpeg: Path
    ffprobe: Path


class ProjectRun(Contract):
    project_id: UUID = Field(default_factory=uuid4)
    source: Source
    status: Literal['processing','transcribed','analyzed','needs_review','no_candidates','completed','failed','cancelled']
    transcript_path: Path | None = None
    candidates_path: Path | None = None
    revisions: list[dict] = Field(default_factory=list)
