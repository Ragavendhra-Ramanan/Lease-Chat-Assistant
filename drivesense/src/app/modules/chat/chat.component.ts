// chat-window.component.ts
import { Component, ElementRef, ViewChild } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms'; 

interface Message {
  sender: 'user' | 'bot';
  text: string;
}

@Component({
  selector: 'app-chat',
  standalone: true,
  imports: [CommonModule, FormsModule],
  templateUrl: './chat.component.html',
  styleUrls: ['./chat.component.scss']
})
export class ChatComponent {
  messages: Message[] = [
  ];
  message = '';
  @ViewChild('scrollContainer') private scrollContainer!:ElementRef;
  ngAfterViewChecked(){
    this.scrollToBottom();
  }

  scrollToBottom():void{
    this.scrollContainer.nativeElement.scrollTop= this.scrollContainer.nativeElement.scrollHeight;
  }

  sendMessage() {
    if (!this.message.trim()) return;
    this.messages.push({ sender: 'user', text: this.message });
    this.message = '';
  }
}
