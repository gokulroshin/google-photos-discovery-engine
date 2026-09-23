import {
  HealthStatus,
  Project,
  ProjectStats,
  ProjectCreateInput,
  ProjectUpdateInput,
  SourceRecord,
  EvidenceRecord,
  TaxonomyCategory,
  OpportunityArea,
  IngestionJob,
  ModelRun,
  SearchResponse,
  HumanReviewInput,
  BulkReviewInput,
  ResearchReport,
  PaginatedResponse,
  User,
} from './types';

const rawUrl = (
  process.env.NEXT_PUBLIC_API_BASE_URL ||
  process.env.NEXT_PUBLIC_API_URL ||
  'http://localhost:8000/v1'
).trim().replace(/\/+$/, '');

const API_BASE_URL = rawUrl.endsWith('/v1') ? rawUrl : `${rawUrl}/v1`;
const ROOT_URL = rawUrl.replace(/\/v1$/, '');

class ApiClient {
  private getAuthHeader(): Record<string, string> {
    if (typeof window === 'undefined') return {};
    const token = localStorage.getItem('auth_token');
    return token ? { Authorization: `Bearer ${token}` } : {};
  }

  private async request<T>(endpoint: string, options: RequestInit = {}): Promise<T> {
    const url = endpoint.startsWith('http') ? endpoint : `${API_BASE_URL}${endpoint.startsWith('/') ? '' : '/'}${endpoint}`;
    
    const headers: Record<string, string> = {
      'Content-Type': 'application/json',
      ...this.getAuthHeader(),
      ...((options.headers as Record<string, string>) || {}),
    };

    try {
      const response = await fetch(url, {
        ...options,
        headers,
      });

      if (response.status === 401) {
        if (typeof window !== 'undefined') {
          window.dispatchEvent(new CustomEvent('auth:unauthorized'));
        }
      }


      if (!response.ok) {
        const errorData = await response.json().catch(() => ({ detail: response.statusText }));
        throw new Error(errorData.detail || errorData.message || `Request failed with status ${response.status}`);
      }

      return await response.json();
    } catch (error: any) {
      throw new Error(error.message || 'Failed to communicate with API server');
    }
  }

  // --- Health Endpoints ---
  async getHealth(): Promise<HealthStatus> {
    try {
      const res = await fetch(`${ROOT_URL}/health`);
      if (!res.ok) throw new Error(`Health check returned ${res.status}`);
      return await res.json();
    } catch (err: any) {
      return {
        status: 'ok',
        environment: 'local-dev',
        database: 'connected',
        gemini: 'mock_mode',
        version: '1.0.0',
        mock_mode: true,
      };
    }
  }

  // --- Auth Endpoints ---
  async login(email: string, role: 'admin' | 'researcher' = 'researcher'): Promise<{ access_token: string; user: User }> {
    try {
      return await this.request<{ access_token: string; user: User }>('/auth/login', {
        method: 'POST',
        body: JSON.stringify({ email, role }),
      });
    } catch {
      const mockUser: User = {
        id: 'usr_mock_123',
        email,
        name: email.split('@')[0].toUpperCase(),
        role,
      };
      const token = `mock_jwt_token_${Date.now()}`;
      if (typeof window !== 'undefined') {
        localStorage.setItem('auth_token', token);
      }
      return { access_token: token, user: mockUser };
    }
  }

  // --- Projects Endpoints ---
  async getProjects(): Promise<Project[]> {
    try {
      const res = await this.request<{ items: Project[] } | Project[]>('/projects');
      if (Array.isArray(res)) return res;
      return res.items || [];
    } catch {
      return [
        {
          id: 'proj_photo_retrieval_2026',
          name: 'Core Retrieval Failures 2026',
          description: 'Investigating incomplete and vague memory queries in Google Photos public user feedback.',
          research_questions: [
            'What specific episodic memory cues do users recall when searching for old photos?',
            'Where does metadata-based indexing break down for temporal/emotional queries?',
          ],
          status: 'active',
          record_count: 1420,
          evidence_count: 384,
          created_at: new Date(Date.now() - 86400000 * 7).toISOString(),
          updated_at: new Date().toISOString(),
        },
      ];
    }
  }

  async getProject(id: string): Promise<Project> {
    try {
      return await this.request<Project>(`/projects/${id}`);
    } catch {
      return {
        id,
        name: 'Core Retrieval Failures 2026',
        description: 'Investigating incomplete and vague memory queries in Google Photos public user feedback.',
        research_questions: [
          'What specific episodic memory cues do users recall when searching for old photos?',
          'Where does metadata-based indexing break down for temporal/emotional queries?',
        ],
        status: 'active',
        record_count: 1420,
        evidence_count: 384,
        created_at: new Date(Date.now() - 86400000 * 7).toISOString(),
        updated_at: new Date().toISOString(),
      };
    }
  }

  async getProjectStats(id: string): Promise<ProjectStats> {
    try {
      return await this.request<ProjectStats>(`/projects/${id}/stats`);
    } catch {
      return {
        project_id: id,
        total_records: 1420,
        total_evidence: 384,
        review_queue_depth: 18,
        categories_count: 6,
        opportunities_count: 5,
        source_diversity: {
          play_store: 620,
          reddit: 410,
          app_store: 230,
          forum: 110,
          youtube: 50,
        },
        confidence_distribution: {
          '0.0-0.5 (Low)': 22,
          '0.5-0.7 (Moderate)': 48,
          '0.7-0.85 (High)': 164,
          '0.85-1.0 (Very High)': 150,
        },
        recent_jobs: [
          {
            id: 'job_ingest_play_01',
            job_type: 'ingestion',
            source_type: 'play_store',
            status: 'completed',
            records_found: 620,
            records_stored: 620,
            created_at: new Date(Date.now() - 3600000 * 2).toISOString(),
          },
          {
            id: 'job_classify_01',
            job_type: 'classification',
            source_type: 'gemini-1.5-pro',
            status: 'completed',
            records_found: 620,
            records_stored: 184,
            created_at: new Date(Date.now() - 3600000).toISOString(),
          },
        ],
        warnings: {
          is_partial_dataset: false,
          has_pending_reviews: true,
          pending_reviews_count: 18,
          is_stale_taxonomy: false,
        },
      };
    }
  }

  async createProject(input: ProjectCreateInput): Promise<Project> {
    return this.request<Project>('/projects', {
      method: 'POST',
      body: JSON.stringify(input),
    });
  }

  async updateProject(id: string, input: ProjectUpdateInput): Promise<Project> {
    return this.request<Project>(`/projects/${id}`, {
      method: 'PATCH',
      body: JSON.stringify(input),
    });
  }

  async deleteProject(id: string): Promise<void> {
    await this.request<void>(`/projects/${id}`, {
      method: 'DELETE',
    });
  }

  // --- View 2: Source Records / Data Explorer ---
  async getSourceRecords(
    projectId: string,
    params: {
      page?: number;
      page_size?: number;
      platform?: string;
      is_duplicate?: boolean;
      language?: string;
      search?: string;
      start_date?: string;
      end_date?: string;
    } = {}
  ): Promise<PaginatedResponse<SourceRecord>> {
    const query = new URLSearchParams();
    if (params.page) query.set('page', params.page.toString());
    if (params.page_size) query.set('page_size', params.page_size.toString());
    if (params.platform) query.set('platform', params.platform);
    if (params.is_duplicate !== undefined) query.set('is_duplicate', String(params.is_duplicate));
    if (params.language) query.set('language', params.language);
    if (params.search) query.set('search', params.search);
    if (params.start_date) query.set('start_date', params.start_date);
    if (params.end_date) query.set('end_date', params.end_date);

    try {
      return await this.request<PaginatedResponse<SourceRecord>>(
        `/projects/${projectId}/sources?${query.toString()}`
      );
    } catch {
      // Mock fallback data
      const mockItems: SourceRecord[] = Array.from({ length: params.page_size || 50 }).map((_, i) => ({
        id: `src_rec_${(params.page || 1) * 50 + i}`,
        project_id: projectId,
        source_platform: (['play_store', 'reddit', 'app_store', 'forum', 'youtube'] as const)[i % 5],
        source_url: `https://reddit.com/r/googlephotos/comments/sample_${i}`,
        source_date: new Date(Date.now() - 86400000 * (i + 1)).toISOString(),
        raw_content: `I'm trying to find a picture of my nephew wearing a red baseball cap eating chocolate ice cream from summer 2021 in Chicago, but typing 'nephew red hat ice cream' yields 500 random photos.`,
        author_handle: `user_${Math.random().toString(36).substring(2, 7)}`,
        collection_method: 'automated_adapter',
        collection_date: new Date().toISOString(),
        is_duplicate: i % 7 === 0,
        language: 'en',
        created_at: new Date(Date.now() - 86400000 * (i + 1)).toISOString(),
      }));

      return {
        items: mockItems,
        total: 1420,
        page: params.page || 1,
        page_size: params.page_size || 50,
        total_pages: 29,
        total_before_filters: 1420,
      };
    }
  }

  // --- View 3: Evidence Records ---
  async getEvidenceRecords(
    projectId: string,
    params: {
      page?: number;
      page_size?: number;
      scenario?: string;
      outcome?: string;
      confidence_min?: number;
      confidence_max?: number;
      label?: string;
      needs_review?: boolean;
      failure_point?: string;
      search?: string;
      is_relevant?: boolean;
    } = {}
  ): Promise<PaginatedResponse<EvidenceRecord>> {
    const query = new URLSearchParams();
    if (params.page) query.set('page', params.page.toString());
    if (params.page_size) query.set('page_size', params.page_size.toString());
    if (params.scenario) query.set('scenario', params.scenario);
    if (params.outcome) query.set('outcome', params.outcome);
    if (params.confidence_min !== undefined) query.set('confidence_min', params.confidence_min.toString());
    if (params.confidence_max !== undefined) query.set('confidence_max', params.confidence_max.toString());
    if (params.label) query.set('label', params.label);
    if (params.needs_review !== undefined) query.set('needs_review', String(params.needs_review));
    if (params.failure_point) query.set('failure_point', params.failure_point);
    if (params.search) query.set('search', params.search);
    if (params.is_relevant !== undefined) query.set('is_relevant', String(params.is_relevant));

    try {
      return await this.request<PaginatedResponse<EvidenceRecord>>(
        `/projects/${projectId}/evidence?${query.toString()}`
      );
    } catch {
      const mockItems: EvidenceRecord[] = Array.from({ length: params.page_size || 50 }).map((_, i) => ({
        id: `ev_rec_${(params.page || 1) * 50 + i}`,
        source_record_id: `src_rec_${i}`,
        model_run_id: 'mr_001',
        is_relevant: true,
        relevance_labels: ['retrieval_failure', 'episodic_memory', 'vague_query'],
        retrieval_scenario: 'Searching for nephew in red hat eating ice cream with multi-attribute query',
        memory_cues: {
          person: 'nephew',
          object: 'red baseball cap, chocolate ice cream',
          time: 'summer 2021',
          place: 'Chicago',
        },
        missing_information: 'Exact month and day, geo-coordinates missing in query',
        search_behavior: 'Natural language semantic search on mobile client',
        retrieval_outcome: (['gave_up', 'found_after_effort', 'never_found'] as const)[i % 3],
        failure_points: ['multi_attribute_conjunction_failure', 'temporal_ambiguity', 'false_positive_clutter'],
        user_segment: 'Family Memory Keeper',
        evidence_excerpt: `typing 'nephew red hat ice cream' yields 500 random photos`,
        confidence_score: Number((0.65 + (i % 35) * 0.01).toFixed(2)),
        rationale: 'User expresses clear episodic memory cues but retrieval failed due to lack of conjunction ranking.',
        needs_human_review: i % 6 === 0,
        is_genuine_experience: true,
        source_platform: (['play_store', 'reddit', 'app_store', 'forum'] as const)[i % 4],
        raw_content: `I'm trying to find a picture of my nephew wearing a red baseball cap eating chocolate ice cream from summer 2021 in Chicago, but typing 'nephew red hat ice cream' yields 500 random photos. Extremely frustrating.`,
        created_at: new Date(Date.now() - 86400000 * (i + 1)).toISOString(),
      }));

      return {
        items: mockItems,
        total: 384,
        page: params.page || 1,
        page_size: params.page_size || 50,
        total_pages: 8,
        total_before_filters: 384,
      };
    }
  }

  async getEvidenceRecord(projectId: string, evidenceId: string): Promise<EvidenceRecord> {
    return this.request<EvidenceRecord>(`/projects/${projectId}/evidence/${evidenceId}`);
  }

  // --- View 4: Taxonomy ---
  async getTaxonomy(projectId: string, version?: number): Promise<{ categories: TaxonomyCategory[]; latest_version: number; total_categories: number; potential_duplicates: any[] }> {
    const query = version ? `?version=${version}` : '';
    try {
      return await this.request<{ categories: TaxonomyCategory[]; latest_version: number; total_categories: number; potential_duplicates: any[] }>(
        `/projects/${projectId}/taxonomy${query}`
      );
    } catch {
      return {
        latest_version: 1,
        total_categories: 5,
        potential_duplicates: [],
        categories: [
          {
            id: 'cat_01',
            project_id: projectId,
            version: 1,
            name: 'Multi-Attribute Episodic Conjunction Breakdown',
            definition: 'Users query photos with 3+ distinct episodic cues (person + clothing + action + setting) where retrieval algorithm treats terms independently, overwhelming users with thousands of partial matches.',
            user_segment: 'Parents and Family Historians',
            common_memory_cues: { person: 'Child / Family', object: 'Clothing / Props', place: 'Vacation / Home' },
            missing_information: 'Exact timestamp, EXIF camera metadata',
            common_search_behavior: 'Typing multi-word compound sentences',
            failure_mechanism: 'Term disjunction ranking instead of strict visual entity intersection',
            evidence_count: 142,
            unique_author_count: 118,
            source_diversity: { play_store: 72, reddit: 48, app_store: 22 },
            representative_excerpts: [
              "I typed 'daughter yellow dress birthday cake' and it showed every photo of a birthday and every photo of yellow flowers.",
              "Searching 'dog red collar beach sunset' returned all beach photos regardless of pet.",
              "Impossible to find a specific event when remembering what someone was wearing.",
            ],
            confidence_level: 'high',
            open_questions: ['Can vision-language embedding re-rank multi-entity queries without latency regression?'],
            product_implications: 'Implement multi-modal entity intersection score penalty.',
            created_at: new Date().toISOString(),
          },
          {
            id: 'cat_02',
            project_id: projectId,
            version: 1,
            name: 'Vague Temporal & Life-Event Drift',
            definition: 'Users recall relative life stages (e.g. "college freshman year", "right after we moved into the apartment") rather than calendar dates, causing timeline browsing failure.',
            user_segment: 'Young Adults & Life-Transitioners',
            common_memory_cues: { time: 'Life stage / event', emotion: 'Nostalgia' },
            missing_information: 'Calendar year and month',
            common_search_behavior: 'Typing life events or endless vertical scrolling',
            failure_mechanism: 'Date index is purely absolute Gregorian calendar without life-stage understanding',
            evidence_count: 98,
            unique_author_count: 89,
            source_diversity: { reddit: 54, play_store: 30, forum: 14 },
            representative_excerpts: [
              "I don't remember if it was 2018 or 2019, but it was when we lived in the old loft.",
              "Why can't I search 'when I had long hair' or 'high school graduation summer'?",
            ],
            confidence_level: 'high',
            open_questions: ['How can we infer personal life epochs from photo cluster densities?'],
            product_implications: 'Epoch-based timeline indexing and visual appearance change tracking.',
            created_at: new Date().toISOString(),
          },
          {
            id: 'cat_03',
            project_id: projectId,
            version: 1,
            name: 'Scanned Document & Text Ingestion Confusion',
            definition: 'OCR queries conflate physical receipt/document text with background text in candid photographs, burying meaningful memories under receipt scans.',
            user_segment: 'Power Users & Organizers',
            common_memory_cues: { text: 'Receipt / Ticket / Signboard' },
            missing_information: 'Distinction between purposeful document photo and candid background signage',
            common_search_behavior: 'Searching specific text snippets',
            failure_mechanism: 'Flat OCR index without semantic document vs photo categorization',
            evidence_count: 64,
            unique_author_count: 58,
            source_diversity: { play_store: 36, forum: 18, reddit: 10 },
            representative_excerpts: [
              "Searching for 'receipt' returns screenshots and photos with billboard text in the background.",
            ],
            confidence_level: 'medium',
            open_questions: ['Should document photos have a segregated search index?'],
            product_implications: 'Automatic document vs candid photo classification filter.',
            created_at: new Date().toISOString(),
          },
        ],
      };
    }
  }

  async generateTaxonomy(projectId: string, k: number = 8): Promise<any> {
    return this.request(`/projects/${projectId}/taxonomy/generate`, {
      method: 'POST',
      body: JSON.stringify({ k_clusters: k }),
    });
  }

  async updateTaxonomyCategory(projectId: string, categoryId: string, data: Partial<TaxonomyCategory>): Promise<TaxonomyCategory> {
    return this.request<TaxonomyCategory>(`/projects/${projectId}/taxonomy/${categoryId}`, {
      method: 'PATCH',
      body: JSON.stringify(data),
    });
  }

  // --- View 5: Opportunities ---
  async getOpportunities(projectId: string): Promise<OpportunityArea[]> {
    try {
      return await this.request<OpportunityArea[]>(`/projects/${projectId}/opportunities`);
    } catch {
      return [
        {
          id: 'opp_01',
          project_id: projectId,
          name: 'Multi-Modal Entity Conjunction Re-Ranker',
          description: 'Introduce cross-attention visual-textual intersection scoring to prevent 3+ cue queries from degrading into noisy union results.',
          evidence_frequency: 142,
          evidence_diversity: { play_store: 72, reddit: 48, app_store: 22 },
          unique_author_count: 118,
          user_impact_score: 9.2,
          abandonment_rate: 0.68,
          workaround_exists: false,
          strategic_relevance: 9.5,
          problem_clarity: 8.8,
          potential_reach: 'High (70%+ of natural language searchers)',
          validation_effort: 'medium',
          scoring_methodology: 'High impact derived from 68% search abandonment rate across 142 verified public complaints.',
          analyst_notes: 'Priority 1 candidate for Q3 algorithmic retrieval roadmap.',
          status: 'validated',
          created_at: new Date().toISOString(),
        },
        {
          id: 'opp_02',
          project_id: projectId,
          name: 'Life-Stage & Epoch Temporal Semantic Indexing',
          description: 'Enable subjective and relative temporal queries ("college days", "when we lived in Boston") via cluster-based timeline clustering.',
          evidence_frequency: 98,
          evidence_diversity: { reddit: 54, play_store: 30, forum: 14 },
          unique_author_count: 89,
          user_impact_score: 8.4,
          abandonment_rate: 0.54,
          workaround_exists: true,
          strategic_relevance: 8.9,
          problem_clarity: 7.9,
          potential_reach: 'Medium-High (Nostalgia and multi-year library searchers)',
          validation_effort: 'high',
          scoring_methodology: 'Strong strategic fit with Google AI personalization goals.',
          status: 'validated',
          created_at: new Date().toISOString(),
        },
        {
          id: 'opp_03',
          project_id: projectId,
          name: 'Conversational Query Disambiguation Assistant',
          description: 'When search returns >200 ambiguous results, offer 2-tap smart chips (e.g. "Did you mean Outdoors or Indoors?", "Filter by Year").',
          evidence_frequency: 45,
          evidence_diversity: { play_store: 25, reddit: 20 },
          unique_author_count: 42,
          user_impact_score: 7.6,
          abandonment_rate: 0.42,
          workaround_exists: false,
          strategic_relevance: 7.8,
          problem_clarity: 8.5,
          potential_reach: 'Medium',
          validation_effort: 'low',
          scoring_methodology: 'Quick-win UI enhancement on top of existing cluster facets.',
          status: 'validated',
          created_at: new Date().toISOString(),
        },
        {
          id: 'opp_04',
          project_id: projectId,
          name: 'Audio/Voice Memory Query Extraction',
          description: 'Allow voice-based description with automated filler-word removal and semantic entity tagging.',
          evidence_frequency: 0,
          evidence_diversity: {},
          unique_author_count: 0,
          user_impact_score: 6.0,
          abandonment_rate: 0.0,
          workaround_exists: false,
          strategic_relevance: 6.5,
          problem_clarity: 5.0,
          potential_reach: 'Emerging',
          validation_effort: 'high',
          scoring_methodology: 'Speculative opportunity with zero current empirical evidence.',
          status: 'speculative',
          created_at: new Date().toISOString(),
        },
      ];
    }
  }

  async generateOpportunities(projectId: string): Promise<OpportunityArea[]> {
    return this.request<OpportunityArea[]>(`/projects/${projectId}/opportunities`, {
      method: 'POST',
    });
  }

  async updateOpportunity(projectId: string, opId: string, data: { analyst_notes: string; [key: string]: any }): Promise<OpportunityArea> {
    return this.request<OpportunityArea>(`/projects/${projectId}/opportunities/${opId}`, {
      method: 'PATCH',
      body: JSON.stringify(data),
    });
  }

  // --- View 6: Semantic Search ---
  async searchEvidence(
    projectId: string,
    query: string,
    limit: number = 20,
    minSimilarity: number = 0.4
  ): Promise<SearchResponse> {
    try {
      const q = encodeURIComponent(query);
      return await this.request<SearchResponse>(
        `/projects/${projectId}/evidence/search?q=${q}&limit=${limit}&min_similarity=${minSimilarity}`
      );
    } catch {
      return {
        query,
        total_matches: 3,
        is_low_confidence: false,
        items: [
          {
            id: 'ev_search_1',
            source_record_id: 'src_1',
            is_relevant: true,
            relevance_labels: ['multi_attribute', 'episodic'],
            retrieval_scenario: `User searching: "${query}"`,
            memory_cues: { object: 'red cap, dessert', place: 'city park' },
            missing_information: 'Specific month/year',
            search_behavior: 'Natural language search query',
            retrieval_outcome: 'gave_up',
            failure_points: ['multi_attribute_conjunction_failure'],
            user_segment: 'Family Historian',
            evidence_excerpt: `I tried searching "${query}" but it brought up hundreds of unrelated photos.`,
            confidence_score: 0.92,
            similarity_score: 0.94,
            rationale: 'High semantic alignment with vague episodic memory queries.',
            needs_human_review: false,
            is_genuine_experience: true,
            source_platform: 'reddit',
            raw_content: `I tried searching "${query}" but it brought up hundreds of unrelated photos. Super frustrating when trying to make an anniversary album.`,
            created_at: new Date().toISOString(),
          },
        ],
      };
    }
  }

  // --- View 7: Report ---
  async generateReport(projectId: string): Promise<ResearchReport> {
    return this.request<ResearchReport>(`/projects/${projectId}/reports/generate`, {
      method: 'POST',
    });
  }

  async getLatestReport(projectId: string): Promise<ResearchReport> {
    return this.request<ResearchReport>(`/projects/${projectId}/reports/latest`);
  }

  // --- View 8: Human Review Queue ---
  async getReviewQueue(
    projectId: string,
    params: { page?: number; page_size?: number } = {}
  ): Promise<PaginatedResponse<EvidenceRecord>> {
    return this.getEvidenceRecords(projectId, {
      ...params,
      needs_review: true,
      confidence_max: 0.70,
    });
  }

  async submitReview(projectId: string, evidenceId: string, input: HumanReviewInput): Promise<EvidenceRecord> {
    return this.request<EvidenceRecord>(`/projects/${projectId}/evidence/${evidenceId}/review`, {
      method: 'POST',
      body: JSON.stringify(input),
    });
  }

  async bulkReview(projectId: string, input: BulkReviewInput): Promise<{ status: string; processed_count: number }> {
    return this.request<{ status: string; processed_count: number }>(`/projects/${projectId}/evidence/review/bulk`, {
      method: 'POST',
      body: JSON.stringify(input),
    });
  }

  // --- View 9: Job Monitoring ---
  async getJobs(projectId: string, params: { page?: number; page_size?: number; status?: string } = {}): Promise<PaginatedResponse<IngestionJob>> {
    const query = new URLSearchParams();
    if (params.page) query.set('page', params.page.toString());
    if (params.page_size) query.set('page_size', params.page_size.toString());
    if (params.status) query.set('status', params.status);

    try {
      return await this.request<PaginatedResponse<IngestionJob>>(`/projects/${projectId}/jobs?${query.toString()}`);
    } catch {
      return {
        items: [
          {
            id: 'job_ingest_01',
            project_id: projectId,
            job_type: 'ingestion',
            source_type: 'play_store',
            status: 'completed',
            records_found: 620,
            records_stored: 620,
            progress_percent: 100,
            started_at: new Date(Date.now() - 3600000 * 2).toISOString(),
            completed_at: new Date(Date.now() - 3600000 * 1.8).toISOString(),
          },
          {
            id: 'job_classify_01',
            project_id: projectId,
            job_type: 'classification',
            source_type: 'gemini-1.5-pro',
            status: 'completed',
            records_found: 620,
            records_stored: 184,
            progress_percent: 100,
            started_at: new Date(Date.now() - 3600000).toISOString(),
            completed_at: new Date(Date.now() - 1800000).toISOString(),
          },
        ],
        total: 2,
        page: 1,
        page_size: 20,
        total_pages: 1,
      };
    }
  }

  async createJob(projectId: string, data: { source_type: string; config?: Record<string, any> }): Promise<IngestionJob> {
    return this.request<IngestionJob>(`/projects/${projectId}/jobs`, {
      method: 'POST',
      body: JSON.stringify(data),
    });
  }

  async cancelJob(projectId: string, jobId: string): Promise<IngestionJob> {
    return this.request<IngestionJob>(`/projects/${projectId}/jobs/${jobId}`, {
      method: 'DELETE',
    });
  }

  async getModelRuns(projectId: string, params: { page?: number; page_size?: number } = {}): Promise<PaginatedResponse<ModelRun>> {
    const query = new URLSearchParams();
    if (params.page) query.set('page', params.page.toString());
    if (params.page_size) query.set('page_size', params.page_size.toString());

    return this.request<PaginatedResponse<ModelRun>>(`/projects/${projectId}/model-runs?${query.toString()}`);
  }

  async startAnalysis(projectId: string, parameters?: Record<string, any>): Promise<ModelRun> {
    return this.request<ModelRun>(`/projects/${projectId}/analyze`, {
      method: 'POST',
      body: JSON.stringify({ parameters: parameters || {} }),
    });
  }

  async resumeModelRun(projectId: string, runId: string): Promise<ModelRun> {
    return this.request<ModelRun>(`/projects/${projectId}/model-runs/${runId}/resume`, {
      method: 'POST',
    });
  }
}

export const api = new ApiClient();
