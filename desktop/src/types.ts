export type {
  Source,
  Project,
  AnalysisEvent,
  GenerationItem,
  Job,
  Revision,
  Proposal,
  AnalysisView,
} from './generated/api';
export type RevisionReviewStatus = import('./generated/api').Revision['review_status'];

export interface Config {
  asr_model_path: string;
  gemini_model: string;
  max_calls: number;
  window_seconds: number;
  max_text_chars: number;
  ffmpeg: string;
  ffprobe: string;
  asr_available: boolean;
  tools_available: boolean;
  gemini_key_configured: boolean;
  clip_preferred_seconds?: number;
  clip_max_seconds?: number;
  pause_mode?: 'preserve' | 'conservative';
  show_thought_summaries?: boolean;
  ai_provider?: 'gemini' | 'openrouter';
  openrouter_model?: string;
  openrouter_key_configured?: boolean;
}
export interface GeminiModel {
  id: string;
  name: string;
  display_name: string;
}
export interface GeminiConnection {
  status: 'missing' | 'untested' | 'valid' | 'invalid' | 'unavailable';
  configured: boolean;
  checked_at: string | null;
  message: string;
  models: GeminiModel[];
}
export interface Word {
  id: string;
  text: string;
  start_us: number;
  end_us: number;
}
export interface Transcript {
  words: Word[];
  segments: { id: string; text: string; start_us: number; end_us: number }[];
}
export interface Checks {
  completeness: boolean;
  context: boolean;
  qualifications: boolean;
  words_and_boundaries: boolean;
  audiovisual: boolean;
}
export interface AnalysisSelection {
  schema_version: string;
  analysis_hash: string | null;
  candidate_ids: string[];
}
export interface Decision {
  revision_id: string;
  decision: 'approved' | 'rejected';
  checks: Checks;
  notes: string;
  content_hash: string;
}
export interface HardwareProfile {
  cpu_physical_cores: number;
  cpu_logical_cores: number;
  ram_total_gb: number;
  ram_available_gb: number;
  has_cuda: boolean;
  gpu_name: string | null;
  vram_gb: number;
  recommended_tier: number;
  recommended_model_id: string;
  tier_title: string;
  tier_description: string;
}
export interface ProvisionStatus {
  status:
    'idle' | 'downloading' | 'extracting' | 'extracting_ffmpeg' | 'ready' | 'failed' | 'cancelled';
  stage: string;
  item: string;
  downloaded_bytes: number;
  total_bytes: number;
  speed_bps: number;
  percent: number;
  error: string | null;
  model_path?: string | null;
  ffmpeg_path?: string | null;
  ffprobe_path?: string | null;
}
export interface ProvisionRequest {
  model_id: string;
  install_ffmpeg: boolean;
}
