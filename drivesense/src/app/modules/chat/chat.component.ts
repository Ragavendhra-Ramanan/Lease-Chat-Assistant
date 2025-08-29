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
       this.conversationService.activeConversation$.subscribe(convo => {
      if (convo) {
        this.conversationId = convo.conversationId;
        this.messages = convo.messages;
      }
    });
    this.userId = localStorage.getItem('token') || '';
    this.messageService.getRecommendations(this.userId).subscribe((recs) => {
      if (recs && recs.length > 0) {
        this.recommendations = recs;
      }
    });
  }
  onRecommendationClick(reco: string) {
    this.recommendations = [];
    this.message = reco;
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
      messages: { sender: 'user', message: this.message, timestamp: new Date().toISOString() },
    };

    this.messages.push(userMsg.messages);

    this.messageService.sendMessage(userMsg).subscribe((botMsg) => {
      this.isBotTyping = false;
      const fullText = botMsg.messages[botMsg.messages.length - 1].message;
      this.simulateTyping(fullText, 'bot');
    });
    this.message = '';
  }
  simulateTyping(fullText: string, sender: 'bot' | 'user') {
    let index = 0;
    const typingMsg: Message = { sender, message: '' , timestamp: ''};
    this.messages.push(typingMsg);

    const interval = setInterval(() => {
      typingMsg.message += fullText[index];
      index++;

      if (index === fullText.length) {
        clearInterval(interval);
      }
    }, 30);
  }
}
