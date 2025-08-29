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
    this.userId = localStorage.getItem('token') || '';

    // Load conversations
    this.messageService.getConversations(this.userId).subscribe((response) => {
      this.conversations = response || [];

      if (this.conversations.length === 0) {
        //If no conversations exist → always create a fresh one with bot’s greeting
        this.startNewConversation(true);
      } else {
        // auto-open the latest one
        this.openConversation(this.conversations[0]);
      }
    });
  }

  toggleSidebar() {
    this.collapsed = !this.collapsed;
  }

  startNewConversation(isFirstLoad = false) {
    // Prevent duplicate empty convos: skip if current convo only has bot greeting
    if (!isFirstLoad && this.activeConvoHasOnlyBotGreeting) {
      return;
    }

    this.messageService.startNewConversation(this.userId).subscribe((response) => {
      const convo = response;

      // refresh conversations list from backend
      this.messageService.getConversations(this.userId).subscribe((res) => {
        this.conversations = res || [];
        this.conversations.unshift(convo);
        this.setActiveConversation(convo);
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