// chat-sidebar.component.ts
import { Component } from '@angular/core';
import { CommonModule } from '@angular/common';

@Component({
  selector: 'app-sidebar',
  standalone: true,
  imports: [CommonModule],
  templateUrl: './sidebar.component.html',
  styleUrls: ['./sidebar.component.scss']
})
export class SidebarComponent {
  collapsed = false;
  conversations = [
    { id: 1, title: 'Leasing BMW X1' },
    { id: 2, title: 'EV Leasing Options' }
  ];

  toggleSidebar() {
    this.collapsed = !this.collapsed;
  }
}
