export interface Message {
  id?: string;
  conversationId: string;
  userId: string;
  text: string;
  sender: 'user' | 'bot';
  timestamp: string; 
}
