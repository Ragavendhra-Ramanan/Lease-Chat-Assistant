import { Injectable } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { Observable } from 'rxjs';
import { ConversationRequest, ConversationResponse } from '../models/message.model';

@Injectable({
  providedIn: 'root'
})
export class ChatService {
  private apiUrl = 'http://localhost:8000/api/chat';

  constructor(private http: HttpClient) {}

  sendMessage(message: ConversationRequest): Observable<ConversationResponse> {
    return this.http.post<ConversationResponse>(`${this.apiUrl}/sendMessage`, message);
  }

  getConversations(userId: string): Observable<ConversationResponse[]> {
    return this.http.get<ConversationResponse[]>(`${this.apiUrl}/getConversations/${userId}`);
  }

  startNewConversation(userId: string): Observable<ConversationResponse> {
    return this.http.post<ConversationResponse>(`${this.apiUrl}/startNewConversation`, { userId });
  }

  getRecommendations(userId: string): Observable<string[]> {
  return this.http.get<string[]>(`${this.apiUrl}/recommendations/${userId}`);
}
}