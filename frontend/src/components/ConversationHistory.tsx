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
        className="chat-history"
        aria-labelledby="chat-empty-title"
      >
        <div className="chat-empty-state">
          <h2 id="chat-empty-title">Start a new conversation</h2>
          <p className="muted">
            Select an existing conversation or choose New conversation.
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
        <p role="status">Loading conversation history…</p>
      ) : null}

      {error ? (
        <p role="alert">{error}</p>
      ) : null}

      {!isLoading && !error && !hasMessages ? (
        <p className="muted">This conversation has no messages yet.</p>
      ) : null}

      {!isLoading && !error && hasMessages ? (
        <ol className="message-list">
          {messages.map((message) => (
            <li
              key={message.id}
              className={`message message-${message.role}`}
            >
              <p className="message-role">{message.role}</p>
              <p className="message-content">{message.content}</p>
            </li>
          ))}
        </ol>
      ) : null}
    </section>
  );
}
