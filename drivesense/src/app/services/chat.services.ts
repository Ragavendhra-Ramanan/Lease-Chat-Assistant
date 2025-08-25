import { Injectable } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { Observable } from 'rxjs';
import { ConversationRequest, ConversationResponse, Message } from '../models/message.model';

@Injectable({
  providedIn: 'root'
})
export class ChatService {
  private apiUrl = 'http://localhost:8000/api/chat';

  constructor(private http: HttpClient) {}

  sendMessage(message: ConversationRequest): Observable<ConversationResponse> {
    return this.http.post<ConversationResponse>(`${this.apiUrl}/sendMessage`, message);
  }

  getConversation(userId: string): Observable<Message[]> {
    return this.http.get<Message[]>(`${this.apiUrl}/conversation/${userId}`);
  }

  startNewConversation(userId: string): Observable<ConversationResponse> {
    return this.http.post<ConversationResponse>(`${this.apiUrl}/startNewConversation`, { userId });
  }
}