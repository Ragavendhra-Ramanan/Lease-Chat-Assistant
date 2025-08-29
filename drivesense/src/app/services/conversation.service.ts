import { Injectable } from '@angular/core';
import { BehaviorSubject } from 'rxjs';

@Injectable({ providedIn: 'root' })
export class ConversationService {
  private activeConversation = new BehaviorSubject<any>(null);
  activeConversation$ = this.activeConversation.asObservable();

  setActiveConversation(conversation: any) {
    this.activeConversation.next(conversation);
  }
}