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
  // Skip creating another convo if the active one is just bot greeting
  if (!isFirstLoad && this.activeConvoHasOnlyBotGreeting) {
    return;
  }

  this.messageService.startNewConversation(this.userId).subscribe((convo) => {
    // Fetch updated list from backend
    this.messageService.getConversations(this.userId).subscribe((res) => {
      let allConvos = res || [];

      if (isFirstLoad) {
        // First login → allow the bot-greeting-only conversation
        this.conversations = allConvos;
      } else {
        // Later → show only convos with at least 2 messages
        this.conversations = allConvos.filter(c => c.messages.length >= 2);
      }

      // Always set the newly created conversation active
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