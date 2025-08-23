import { Component, ElementRef, ViewChild, AfterViewChecked } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { Message } from '../../models/message.model';
import { ChatService } from '../../services/chat.services';

@Component({
  selector: 'app-chat',
  standalone: true,
  imports: [CommonModule, FormsModule],
  templateUrl: './chat.component.html',
  styleUrls: ['./chat.component.scss']
})
export class ChatComponent implements AfterViewChecked {
  messages: Message[] = [];
  message = '';

  conversationId = 'conv-001'; 
  userId = 'user-123';        

  @ViewChild('scrollContainer') private scrollContainer!: ElementRef;

  constructor(private messageService: ChatService) {}

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
    const userMsg: Message = {
      conversationId: this.conversationId,
      userId: this.userId,
      text: this.message,
      sender: 'user',
      timestamp: new Date().toISOString()
    };

    this.messages.push(userMsg);

    // Call backend
    this.messageService.sendMessage(userMsg).subscribe({
      next: (botMsg) => {
        this.messages.push(botMsg);
      },
      error: (err) => {
        console.error('Error sending message', err);
        this.messages.push({
          conversationId: this.conversationId,
          userId: 'system',
          text: 'Oops! Something went wrong.',
          sender: 'bot',
          timestamp: new Date().toISOString()
        });
      }
    });

    this.message = '';
  }
}
