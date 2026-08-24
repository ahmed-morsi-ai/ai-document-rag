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
      className="chat-workspace-sidebar"
      aria-labelledby="conversation-list-title"
    >
      <div className="chat-sidebar-top">
        <div>
          <p className="workspace-section-kicker">Conversations</p>
          <h2 id="conversation-list-title">Your chats</h2>
        </div>

        <button
          type="button"
          className="chat-new-button"
          onClick={onNewConversation}
        >
          <span aria-hidden="true">+</span>
          New chat
        </button>
      </div>

      <div className="chat-sidebar-body">
        {isLoading ? (
          <div className="chat-sidebar-state" role="status">
            <strong>Loading conversations…</strong>
            <span>Refreshing your chat history…</span>
          </div>
        ) : null}

        {error ? (
          <div className="chat-sidebar-alert" role="alert">
            {error}
          </div>
        ) : null}

        {deleteError ? (
          <div className="chat-sidebar-alert" role="alert">
            {deleteError}
          </div>
        ) : null}

        {!isLoading && !error && conversations.length === 0 ? (
          <div className="chat-sidebar-empty">
            <strong>No conversations yet.</strong>
            <span>Start a new chat to begin.</span>
            <button
              type="button"
              className="secondary"
              onClick={onNewConversation}
            >
              Start a new chat
            </button>
          </div>
        ) : null}

        {!isLoading && !error && conversations.length > 0 ? (
          <nav aria-label="Conversations">
            <ul className="chat-conversation-list">
              {conversations.map((conversation) => {
                const isActive =
                  conversation.id === activeConversationId;
                const isConfirming =
                  deleteTargetConversationId === conversation.id;
                const isDeleting =
                  deletingConversationId === conversation.id;

                return (
                  <li key={conversation.id}>
                    <div
                      className={`chat-conversation-row${
                        isActive ? " is-active" : ""
                      }${
                        isDeleting ? " is-deleting" : ""
                      }`}
                    >
                      <button
                        type="button"
                        className="chat-conversation-button"
                        onClick={() => onSelect(conversation.id)}
                        aria-label={
                          conversation.title ||
                          "Untitled conversation"
                        }
                        aria-current={isActive ? "true" : undefined}
                        disabled={isDeleting}
                      >
                        <span className="chat-conversation-marker" />
                        <span className="chat-conversation-copy">
                          <strong>
                            {conversation.title ||
                              "Untitled conversation"}
                          </strong>
                          <span>Conversation</span>
                        </span>
                      </button>

                      {isConfirming ? (
                        <div className="chat-delete-confirmation">
                          <span>Delete this conversation?</span>

                          <div>
                            <button
                              type="button"
                              className="secondary"
                              onClick={onDeleteCancel}
                            >
                              Cancel
                            </button>
                            <button
                              type="button"
                              className="danger-button"
                              onClick={() =>
                                onDeleteConfirm(conversation.id)
                              }
                              disabled={isDeleting}
                            >
                              Confirm delete
                            </button>
                          </div>
                        </div>
                      ) : (
                        <button
                          type="button"
                          className="chat-conversation-delete"
                          aria-label={`Delete ${
                            conversation.title ||
                            "Untitled conversation"
                          }`}
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
      </div>

      <div className="chat-sidebar-footer">
        <div className="chat-sidebar-note">
          <span className="chat-sidebar-note-dot" aria-hidden="true" />
          <div>
            <strong>Document-aware chat</strong>
            <span>
              Ask questions using the available workspace context.
            </span>
          </div>
        </div>
      </div>
    </aside>
  );
}
