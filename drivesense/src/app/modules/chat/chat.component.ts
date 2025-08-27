import { Component, ElementRef, ViewChild, AfterViewChecked, OnInit } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { ConversationRequest, Message } from '../../models/message.model';
import { ChatService } from '../../services/chat.services';
import { marked } from 'marked';
import { DomSanitizer, SafeHtml } from '@angular/platform-browser';

@Component({
  selector: 'app-chat',
  standalone: true,
  imports: [CommonModule, FormsModule],
  templateUrl: './chat.component.html',
  styleUrls: ['./chat.component.scss']
})
export class ChatComponent implements AfterViewChecked, OnInit {
  messages: Message[];
  recommendations: string[] = [];
  message = '';   
  conversationId = '';
  userId = '';
  isBotTyping = false;


  @ViewChild('scrollContainer') private scrollContainer!: ElementRef;

  constructor(private messageService: ChatService, private sanitizer: DomSanitizer) {
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

    this.messageService.getRecommendations(this.userId).subscribe({
    next: (recs) => {
      if (recs && recs.length > 0) {
        this.recommendations = recs;
      }
    },
    error: (err) => {
      console.error('Error fetching recommendations', err);
    }
  });
 }
 onRecommendationClick(reco: string) {
  this.recommendations = []; // Hide cards
  this.message = reco;
  this.sendMessage(); // Send like normal message
}
  ngAfterViewChecked() {
    this.scrollToBottom();
  }
  getMessageContent(message: Message): SafeHtml {
  var html = marked.parse(message.message) as string ; // convert markdown → HTML
  return this.sanitizer.bypassSecurityTrustHtml(html); // make it safe
}
  scrollToBottom(): void {
    if (this.scrollContainer) {
      this.scrollContainer.nativeElement.scrollTop = this.scrollContainer.nativeElement.scrollHeight;
    }
  }

  sendMessage() {
    if (!this.message.trim()) return;
    this.isBotTyping = true;
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
        this.isBotTyping = false;
         const fullText = botMsg.messages[botMsg.messages.length - 1].message;
         this.simulateTyping(fullText, 'bot');
      },
      error: (err) => {
        console.error('Error sending message', err);
      }
    });

    this.message = '';
  }
  simulateTyping(fullText: string, sender: 'bot' | 'user') {
  let index = 0;
  const typingMsg: Message = { sender, message: '' };
  this.messages.push(typingMsg);

  const interval = setInterval(() => {
    typingMsg.message += fullText[index];
    index++;

    if (index === fullText.length) {
      clearInterval(interval);
    }
  }, 30); // typing speed (ms per char)
}
}
