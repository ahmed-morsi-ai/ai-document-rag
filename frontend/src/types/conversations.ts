export interface ConversationItem {
  id: string;
  title: string | null;
  created_at: string;
  updated_at: string;
}

export interface ConversationListResponse {
  conversations: ConversationItem[];
}

export interface ConversationMessage {
  id: string;
  role: string;
  content: string;
  sequence_number: number;
  created_at: string;
}

export interface ConversationHistoryResponse {
  conversation: ConversationItem;
  messages: ConversationMessage[];
}

export interface ChatSource {
  text: string;
  document_id: string;
  chunk_index: number;
  distance: number;
  metadata: Record<string, string>;
}

export interface ChatMessage extends ConversationMessage {
  sources?: ChatSource[];
}

export interface ChatRequest {
  query: string;
  top_k?: number;
  conversation_id?: string;
}

export interface ChatResponse {
  query: string;
  answer: string;
  sources: ChatSource[];
}
