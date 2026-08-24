import type { ConversationMessage } from "../types/conversations";

interface ConversationHistoryProps {
  messages: ConversationMessage[];
  isLoading: boolean;
  error: string;
  hasActiveConversation: boolean;
}

export function ConversationHistory({
  messages,
  isLoading,
  error,
  hasActiveConversation,
}: ConversationHistoryProps) {
  const hasMessages = messages.length > 0;

  if (!hasActiveConversation && !hasMessages) {
    return (
      <section
        className="chat-history chat-history-empty"
        aria-labelledby="chat-empty-title"
      >
        <div className="chat-empty-state">
          <div className="chat-empty-mark" aria-hidden="true">
            +
          </div>
          <p className="workspace-section-kicker">Conversation workspace</p>
          <h2 id="chat-empty-title">Start a new conversation</h2>
          <p>
            Select an existing chat or start a new one. Your composer is ready
            whenever you are.
          </p>
        </div>
      </section>
    );
  }

  return (
    <section
      className="chat-history"
      aria-labelledby="chat-history-title"
      aria-live="polite"
    >
      <h2 id="chat-history-title" className="visually-hidden">
        Conversation history
      </h2>

      {isLoading ? (
        <div className="chat-history-state" role="status">
          <span className="chat-loading-dot" aria-hidden="true" />
          Loading conversation history…
        </div>
      ) : null}

      {error ? (
        <div className="chat-history-alert" role="alert">
          {error}
        </div>
      ) : null}

      {!isLoading && !error && !hasMessages ? (
        <div className="chat-history-empty-message">
          <strong>This conversation has no messages yet.</strong>
          <span>Use the composer below to send the first question.</span>
        </div>
      ) : null}

      {!isLoading && !error && hasMessages ? (
        <ol className="chat-message-list">
          {messages.map((message) => (
            <li
              key={message.id}
              className={`chat-message chat-message-${message.role}`}
            >
              <div className="chat-message-meta">
                <span className="chat-message-role">
                  {message.role === "assistant"
                    ? "Assistant"
                    : "You"}
                </span>
              </div>

              <div className="chat-message-surface">
                <p className="chat-message-content">
                  {message.content}
                </p>
              </div>
            </li>
          ))}
        </ol>
      ) : null}
    </section>
  );
}
