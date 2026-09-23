export type UserRole = 'admin' | 'researcher';

export interface User {
  id: string;
  email: string;
  name: string;
  role: UserRole;
}

export interface AuthResponse {
  access_token: string;
  token_type: string;
  user: User;
}

export interface HealthStatus {
  status: 'ok' | 'degraded' | 'error';
  environment: string;
  database: 'connected' | 'disconnected';
  gemini: 'configured' | 'not_configured' | 'mock_mode';
  version: string;
  mock_mode: boolean;
}

export type ProjectStatus = 'draft' | 'active' | 'archived';

export interface Project {
  id: string;
  name: string;
  description: string | null;
  research_questions: string[];
  status: ProjectStatus;
  record_count?: number;
  evidence_count?: number;
  active_jobs_count?: number;
  total_categories_count?: number;
  total_opportunities_count?: number;
  created_at: string;
  updated_at: string;
}

export interface ProjectStats {
  project_id: string;
  total_records: number;
  total_evidence: number;
  review_queue_depth: number;
  categories_count: number;
  opportunities_count: number;
  source_diversity: Record<string, number>;
  confidence_distribution: Record<string, number>;
  recent_jobs: {
    id: string;
    job_type: string;
    source_type: string;
    status: string;
    records_found: number;
    records_stored: number;
    created_at: string;
  }[];
  warnings: {
    is_partial_dataset: boolean;
    has_pending_reviews: boolean;
    pending_reviews_count: number;
    is_stale_taxonomy: boolean;
  };
}

export interface ProjectCreateInput {
  name: string;
  description?: string;
  research_questions?: string[];
}

export interface ProjectUpdateInput {
  name?: string;
  description?: string;
  research_questions?: string[];
  status?: ProjectStatus;
}

export type Platform =
  | 'google_play'
  | 'play_store'
  | 'app_store'
  | 'reddit'
  | 'youtube'
  | 'support_forum'
  | 'forum'
  | 'manual_upload'
  | 'manual_import'
  | 'other';

export interface SourceRecord {
  id: string;
  project_id: string;
  source_platform: Platform | string;
  source_url: string | null;
  source_date: string | null;
  raw_content: string;
  author_handle: string; // Anonymized pseudonym e.g. user_a3f2c
  collection_method: 'automated_adapter' | 'manual_csv' | 'manual_json' | string;
  collection_date: string;
  is_duplicate: boolean;
  metadata?: Record<string, any>;
  language?: string;
  created_at: string;
}

export type JobStatus = 'queued' | 'running' | 'completed' | 'failed' | 'paused' | 'cancelled';
export type JobType = 'ingestion' | 'classification' | 'taxonomy' | 'opportunities' | 'report' | 'reembed';

export interface IngestionJob {
  id: string;
  project_id: string;
  job_type: JobType;
  source_type: string;
  status: JobStatus;
  records_found: number;
  records_stored: number;
  records_failed?: number;
  progress_percent?: number;
  error_details?: Record<string, any> | null;
  started_at: string;
  completed_at?: string | null;
  last_heartbeat_at?: string;
  created_at?: string;
}

export interface ModelRun {
  id: string;
  project_id: string;
  model_name: string;
  prompt_version: string;
  status: JobStatus;
  total_records: number;
  processed_records: number;
  relevant_records: number;
  error_message?: string | null;
  started_at: string;
  completed_at?: string | null;
  created_at: string;
}

export interface MemoryCues {
  person?: string | null;
  place?: string | null;
  time?: string | null;
  event?: string | null;
  object?: string | null;
  visual?: string | null;
  text?: string | null;
  emotion?: string | null;
  purpose?: string | null;
  source?: string | null;
  [key: string]: string | null | undefined;
}

export type RetrievalOutcome =
  | 'found_quickly'
  | 'found_after_effort'
  | 'found_unexpectedly'
  | 'gave_up'
  | 'found_alternative'
  | 'never_found'
  | 'ambiguous'
  | string;

export interface EvidenceRecord {
  id: string;
  source_record_id: string;
  model_run_id?: string;
  is_relevant: boolean;
  relevance_labels: string[];
  retrieval_scenario: string | null;
  memory_cues: MemoryCues;
  missing_information: string | null;
  search_behavior: string | null;
  retrieval_outcome: RetrievalOutcome;
  failure_points: string[];
  user_segment: string | null;
  evidence_excerpt: string | null;
  confidence_score: number;
  rationale: string;
  needs_human_review: boolean;
  is_genuine_experience: boolean;
  created_at: string;
  updated_at?: string;
  // Populated in detail or search views
  source_record?: SourceRecord;
  source_platform?: string;
  raw_content?: string;
  model_name?: string;
  prompt_version?: string;
  similarity_score?: number;
  is_low_confidence?: boolean;
}

export interface TaxonomyCategory {
  id: string;
  project_id: string;
  version: number;
  name: string;
  definition: string;
  user_segment: string;
  common_memory_cues: MemoryCues;
  missing_information: string;
  common_search_behavior: string;
  failure_mechanism: string;
  evidence_count: number;
  unique_author_count: number;
  source_diversity: Record<string, number>;
  representative_excerpts: string[];
  confidence_level: 'high' | 'medium' | 'low';
  open_questions: string[];
  product_implications: string;
  created_at: string;
}

export interface OpportunityArea {
  id: string;
  project_id: string;
  taxonomy_category_id?: string;
  name: string;
  description: string;
  evidence_frequency: number;
  evidence_diversity: Record<string, number>;
  unique_author_count: number;
  user_impact_score: number; // 0 - 10
  abandonment_rate: number; // 0 - 1
  workaround_exists: boolean;
  strategic_relevance: number; // 0 - 10
  problem_clarity: number; // 0 - 10
  potential_reach: string;
  validation_effort: 'low' | 'medium' | 'high';
  scoring_methodology: string;
  analyst_notes?: string;
  status: 'draft' | 'validated' | 'rejected' | 'speculative';
  created_at: string;
}

export interface SearchResponse {
  query: string;
  total_matches: number;
  is_low_confidence: boolean;
  items: EvidenceRecord[];
}

export interface HumanReviewInput {
  action: 'approved' | 'corrected' | 'rejected';
  corrections?: Partial<EvidenceRecord>;
  reviewer_notes?: string;
}

export interface BulkReviewInput {
  evidence_record_ids: string[];
  action: 'approved' | 'rejected';
  reviewer_notes?: string;
}

export interface ResearchReport {
  project_id: string;
  project_name: string;
  generated_at: string;
  categories_count: number;
  opportunities_count: number;
  categories: {
    id: string;
    name: string;
    definition: string;
    evidence_count: number;
    confidence_level: string;
    failure_mechanism: string;
    product_implications: string;
  }[];
  opportunities: {
    id: string;
    name: string;
    user_impact_score: number;
    strategic_relevance: number;
    problem_clarity: number;
    abandonment_rate: number;
    validation_effort: string;
    potential_reach: string;
    status: string;
  }[];
  markdown: string;
}

export interface PaginatedResponse<T> {
  items: T[];
  total: number;
  page: number;
  page_size: number;
  total_pages: number;
  total_before_filters?: number;
  applied_filters?: Record<string, any>;
}

export interface ApiError {
  message: string;
  status?: number;
  details?: any;
}
