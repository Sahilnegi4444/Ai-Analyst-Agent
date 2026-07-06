import { MessageItem } from './MessageItem'
import type { Message } from './MessageItem'

interface MessageFeedProps {
  messages: Message[]
  loading: boolean
  activeCitation: string | null
  setActiveCitation: (id: string | null) => void
}

export const MessageFeed: React.FC<MessageFeedProps> = ({
  messages,
  loading,
  activeCitation,
  setActiveCitation
}) => {
  return (
    <div className="messages-feed-wrapper" role="log" aria-label="Conversation Feed">
      {messages.map(msg => (
        <MessageItem
          key={msg.id}
          msg={msg}
          activeCitation={activeCitation}
          setActiveCitation={setActiveCitation}
        />
      ))}

      {/* Bouncing Dots Loading Animation */}
      {loading && (
        <div className="chat-message-wrapper agent" style={{ marginBottom: '16px' }} role="status" aria-label="Agent is typing">
          <div className="message-bubble-container agent">
            <div className="message-sender-identity">AI Agent</div>
            <div className="message-bubble agent">
              <div className="typing-indicator" aria-label="Typing indicator">
                <span className="typing-dot" />
                <span className="typing-dot" />
                <span className="typing-dot" />
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}
