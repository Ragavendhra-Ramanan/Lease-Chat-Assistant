// chat-sidebar.component.ts
import { Component, OnInit } from '@angular/core';
import { CommonModule } from '@angular/common';
import { ConversationResponse } from '../../models/message.model';
import { ChatService } from '../../services/chat.services';
import { ConversationService } from '../../services/conversation.service';

@Component({
  selector: 'app-sidebar',
  standalone: true,
  imports: [CommonModule],
  templateUrl: './sidebar.component.html',
  styleUrls: ['./sidebar.component.scss']
})
export class SidebarComponent implements OnInit {
  collapsed = false;
  userId = '';
  conversations: ConversationResponse[] = [];
  activeConvoHasOnlyBotGreeting = false;

  constructor(
    private messageService: ChatService,
    private conversationService: ConversationService
  ) {}

ngOnInit(): void {
  this.userId = sessionStorage.getItem('userId') || '';

  // Always start a fresh conversation after login
  this.messageService.startNewConversation(this.userId).subscribe((newConvo) => {
    // Fetch updated list
    this.messageService.getConversations(this.userId).subscribe((res) => {
      this.conversations = res || [];

      // Put newest conversation on top
      this.conversations.unshift(newConvo);

      // Open the new one immediately
      this.setActiveConversation(newConvo);
    });
  });
}

  toggleSidebar() {
    this.collapsed = !this.collapsed;
  }

startNewConversation(isFirstLoad = false) {
  this.messageService.startNewConversation(this.userId).subscribe((newConvo) => {
    // Refresh conversations
    this.messageService.getConversations(this.userId).subscribe((res) => {
      this.conversations = res || [];

      // Avoid duplicates
      const alreadyExists = this.conversations.some(
        (c) => c.conversationId === newConvo.conversationId
      );
      if (!alreadyExists) {
        this.conversations.unshift(newConvo);
      }

      // Switch to the new conversation immediately
      this.setActiveConversation(newConvo);
    });
  });
}

  openConversation(convo: ConversationResponse) {
    this.setActiveConversation(convo);
  }

  private setActiveConversation(convo: ConversationResponse) {
    // check if conversation has only bot greeting
    this.activeConvoHasOnlyBotGreeting =
      convo.messages &&
      convo.messages.length === 1 &&
      convo.messages[0].sender === 'bot';
    this.conversationService.setActiveConversation(convo);
  }
}