import {
  Component,
  ElementRef,
  ViewChild,
  AfterViewChecked,
  OnInit,
} from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { ConversationRequest, Message } from '../../models/message.model';
import { ChatService } from '../../services/chat.services';
import { marked } from 'marked';
import { DomSanitizer, SafeHtml } from '@angular/platform-browser';
import { ConversationService } from '../../services/conversation.service';

@Component({
  selector: 'app-chat',
  standalone: true,
  imports: [CommonModule, FormsModule],
  templateUrl: './chat.component.html',
  styleUrls: ['./chat.component.scss'],
})
export class ChatComponent implements AfterViewChecked, OnInit {
  messages: Message[];
  recommendations: string[] = [];
  message = '';
  conversationId = '';
  userId = '';
  isBotTyping = false;

  @ViewChild('scrollContainer') private scrollContainer!: ElementRef;

  constructor(
    private messageService: ChatService,
    private sanitizer: DomSanitizer,
    private conversationService: ConversationService
  ) {
    this.messages = [];
  }
  ngOnInit(): void {
    this.userId = sessionStorage.getItem('userId') || '';

    this.conversationService.activeConversation$.subscribe((convo) => {
      if (convo) {
        this.conversationId = convo.conversationId;
        this.messages = convo.messages || [];
        if (!this.messages || this.messages.length === 1) {
          this.messageService
            .getRecommendations(this.userId)
            .subscribe((recs) => {
              this.recommendations = recs || [];
            });
        } else {
          this.recommendations = [];
        }
      } else {
        this.conversationId = '';
        this.messages = [];
        this.recommendations = [];
      }
    });
  }
  onRecommendationClick(reco: string) {
    this.recommendations = [];
    const parts = reco.split(':');
    this.message = parts.length > 1 ? parts[1].trim() : reco;
    this.sendMessage();
  }
  ngAfterViewChecked() {
    this.scrollToBottom();
  }
  getMessageContent(message: Message): SafeHtml {
    var html = marked.parse(message.message) as string;
    return this.sanitizer.bypassSecurityTrustHtml(html);
  }
  scrollToBottom(): void {
    if (this.scrollContainer) {
      this.scrollContainer.nativeElement.scrollTop =
        this.scrollContainer.nativeElement.scrollHeight;
    }
  }

  sendMessage() {
    if (!this.message.trim()) return;
    this.isBotTyping = true;

    var userMsg: ConversationRequest = {
      conversationId: this.conversationId,
      userId: this.userId,
      messages: {
        sender: 'user',
        message: this.message,
        timestamp: new Date().toISOString(),
        fileStream: '',
      },
    };

    this.messages.push(userMsg.messages);

    this.messageService.sendMessage(userMsg).subscribe((botMsg) => {
      this.isBotTyping = false;

      const lastMsg = botMsg.messages[botMsg.messages.length - 1];
      if (lastMsg.fileStream) {
        this.messages.push(lastMsg);
      } else {
        this.simulateTyping(lastMsg.message, 'bot');
      }
    });
    this.message = '';
  }
  simulateTyping(fullText: string, sender: 'bot' | 'user') {
    let index = 0;
    const typingMsg: Message = { sender, message: '', timestamp: '' };
    this.messages.push(typingMsg);

    const interval = setInterval(() => {
      typingMsg.message += fullText[index];
      index++;

      if (index === fullText.length) {
        clearInterval(interval);
      }
    }, 30);
  }

  openPdf(base64: string) {
    const byteChars = atob(base64);
    const byteNumbers = new Array(byteChars.length);
    for (let i = 0; i < byteChars.length; i++) {
      byteNumbers[i] = byteChars.charCodeAt(i);
    }
    const byteArray = new Uint8Array(byteNumbers);
    const blob = new Blob([byteArray], { type: 'application/pdf' });
    const url = URL.createObjectURL(blob);

    window.open(url, '_blank');
  }
}
