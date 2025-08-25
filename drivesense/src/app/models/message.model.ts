export interface ConversationRequest {
  conversationId: string;
  userId: string;
  timestamp: string; 
  messages: Message;
}

export interface ConversationResponse {
    messages: Message[] 
    userId: string
    conversationId: string
}   

export interface Message{
   sender: string
   message: string
}
    