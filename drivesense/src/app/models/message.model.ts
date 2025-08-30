export interface ConversationRequest {
  conversationId: string;
  userId: string;
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
   timestamp: string; 
   fileStream?: string;
}
    