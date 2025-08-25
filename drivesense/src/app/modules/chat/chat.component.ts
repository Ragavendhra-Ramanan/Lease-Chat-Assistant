import { Component, ElementRef, ViewChild, AfterViewChecked, OnInit } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { ConversationRequest, Message } from '../../models/message.model';
import { ChatService } from '../../services/chat.services';

@Component({
  selector: 'app-chat',
  standalone: true,
  imports: [CommonModule, FormsModule],
  templateUrl: './chat.component.html',
  styleUrls: ['./chat.component.scss']
})
export class ChatComponent implements AfterViewChecked, OnInit {
  messages: Message[];
  message = '';   
  conversationId = '';
  userId = '';

  @ViewChild('scrollContainer') private scrollContainer!: ElementRef;

  constructor(private messageService: ChatService) {
    this.messages = [];
  }
 ngOnInit(): void {
    this.userId = localStorage.getItem('token') || '';
    this.messageService.startNewConversation(this.userId).subscribe({
      next: (response) => {
        this.conversationId = response.conversationId;
        this.messages = response.messages;
      },
      error: (err) => {
        console.error('Error starting conversation', err);
      }
    });
 }
  ngAfterViewChecked() {
    this.scrollToBottom();
  }

  scrollToBottom(): void {
    if (this.scrollContainer) {
      this.scrollContainer.nativeElement.scrollTop = this.scrollContainer.nativeElement.scrollHeight;
    }
  }

  sendMessage() {
    if (!this.message.trim()) return;

    // Construct user message
    var userMsg: ConversationRequest = {
      conversationId: this.conversationId,
      userId: this.userId,
      timestamp: new Date().toISOString(),
      messages: { sender: 'user', message: this.message }
    };

    this.messages.push(userMsg.messages);

    // Call backend
    this.messageService.sendMessage(userMsg).subscribe({
      next: (botMsg) => {
        this.messages.push(botMsg.messages[-1]); 
      },
      error: (err) => {
        console.error('Error sending message', err);
      }
    });

    this.message = '';
  }
}
