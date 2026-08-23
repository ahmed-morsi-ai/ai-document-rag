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


export interface ChatRequest {
  query: string;
  top_k?: number;
  conversation_id?: string;
}

export interface ChatResponse {
  query: string;
  answer: string;
}
