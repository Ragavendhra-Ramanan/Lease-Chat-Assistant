import { Message } from './message.model';

export interface Conversation {
  id: string;
  userId: string;
  title: string;
  messages?: Message[];
  createdAt?: string;
  updatedAt?: string;
}
