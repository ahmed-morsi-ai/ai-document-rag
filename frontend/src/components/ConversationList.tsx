import type { ConversationItem } from "../types/conversations";

interface ConversationListProps {
  conversations: ConversationItem[];
  activeConversationId: string | null;
  isLoading: boolean;
  error: string;
  deleteTargetConversationId: string | null;
  deletingConversationId: string | null;
  deleteError: string;
  onSelect: (conversationId: string) => void;
  onNewConversation: () => void;
  onDeleteRequest: (conversationId: string) => void;
  onDeleteCancel: () => void;
  onDeleteConfirm: (conversationId: string) => void;
}

export function ConversationList({
  conversations,
  activeConversationId,
  isLoading,
  error,
  deleteTargetConversationId,
  deletingConversationId,
  deleteError,
  onSelect,
  onNewConversation,
  onDeleteRequest,
  onDeleteCancel,
  onDeleteConfirm,
}: ConversationListProps) {
  return (
    <aside
      className="chat-sidebar"
      aria-labelledby="conversation-list-title"
    >
      <div className="chat-sidebar-header">
        <div>
          <p className="eyebrow">Conversations</p>
          <h2 id="conversation-list-title">Your chats</h2>
        </div>

        <button type="button" onClick={onNewConversation}>
          New conversation
        </button>
      </div>

      {isLoading ? (
        <p role="status">Loading conversations…</p>
      ) : null}

      {error ? (
        <p role="alert">{error}</p>
      ) : null}

      {deleteError ? (
        <p role="alert">{deleteError}</p>
      ) : null}

      {!isLoading && !error && conversations.length === 0 ? (
        <p className="muted">No conversations yet.</p>
      ) : null}

      {!isLoading && !error && conversations.length > 0 ? (
        <nav aria-label="Conversations">
          <ul className="conversation-list">
            {conversations.map((conversation) => {
              const isConfirming =
                deleteTargetConversationId === conversation.id;
              const isDeleting =
                deletingConversationId === conversation.id;

              return (
                <li key={conversation.id}>
                  <div>
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
                      disabled={isDeleting}
                    >
                      <span>
                        {conversation.title || "Untitled conversation"}
                      </span>
                    </button>

                    {isConfirming ? (
                      <div>
                        <p>Delete this conversation?</p>

                        <button
                          type="button"
                          onClick={onDeleteCancel}
                        >
                          Cancel
                        </button>

                        <button
                          type="button"
                          onClick={() =>
                            onDeleteConfirm(conversation.id)
                          }
                          disabled={isDeleting}
                        >
                          Confirm delete
                        </button>
                      </div>
                    ) : (
                      <button
                        type="button"
                        onClick={() =>
                          onDeleteRequest(conversation.id)
                        }
                        disabled={isDeleting}
                      >
                        Delete
                      </button>
                    )}
                  </div>
                </li>
              );
            })}
          </ul>
        </nav>
      ) : null}
    </aside>
  );
}
