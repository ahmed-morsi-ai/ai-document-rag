import type { ConversationItem } from "../types/conversations";

interface ConversationListProps {
  conversations: ConversationItem[];
  activeConversationId: string | null;
  isLoading: boolean;
  error: string;
  onSelect: (conversationId: string) => void;
  onNewConversation: () => void;
}

export function ConversationList({
  conversations,
  activeConversationId,
  isLoading,
  error,
  onSelect,
  onNewConversation,
}: ConversationListProps) {
  return (
    <aside className="chat-sidebar" aria-labelledby="conversation-list-title">
      <div className="chat-sidebar-header">
        <div>
          <p className="eyebrow">Conversations</p>
          <h2 id="conversation-list-title">Your chats</h2>
        </div>

        <button type="button" onClick={onNewConversation}>
          New conversation
        </button>
      </div>

      {isLoading ? <p role="status">Loading conversations…</p> : null}

      {error ? (
        <p role="alert">{error}</p>
      ) : null}

      {!isLoading && !error && conversations.length === 0 ? (
        <p className="muted">No conversations yet.</p>
      ) : null}

      {!isLoading && !error && conversations.length > 0 ? (
        <nav aria-label="Conversations">
          <ul className="conversation-list">
            {conversations.map((conversation) => (
              <li key={conversation.id}>
                <button
                  type="button"
                  className={
                    conversation.id === activeConversationId
                      ? "conversation-item active"
                      : "conversation-item"
                  }
                  onClick={() => onSelect(conversation.id)}
                  aria-current={
                    conversation.id === activeConversationId
                      ? "true"
                      : undefined
                  }
                >
                  <span>{conversation.id}</span>
                </button>
              </li>
            ))}
          </ul>
        </nav>
      ) : null}
    </aside>
  );
}
