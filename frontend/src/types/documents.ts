export interface DocumentItem {
  id: string;
  original_filename: string;
  mime_type: string;
  processing_status: string;
  created_at: string;
  updated_at: string;
}

export interface DocumentListResponse {
  items: DocumentItem[];
  total_count: number;
  page: number;
  page_size: number;
}
