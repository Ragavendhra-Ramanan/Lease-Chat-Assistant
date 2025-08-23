export interface Message {
  id?: string;
  conversationId: string;
  userId: string;
  content: string;
  sender: 'user' | 'bot';
  timestamp: string; 
}
