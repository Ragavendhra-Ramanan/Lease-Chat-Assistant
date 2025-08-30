// chat-header.component.ts
import { Component, OnInit } from '@angular/core';
import { CommonModule } from '@angular/common';
import { Router } from '@angular/router';

@Component({
  selector: 'app-header',
  standalone: true,
  imports: [CommonModule],
  templateUrl: './header.component.html',
  styleUrls: ['./header.component.scss']
})
export class HeaderComponent implements OnInit {
  userName: string | null = null;
  constructor(private router: Router) {}
  ngOnInit(): void {
     this.userName = sessionStorage.getItem('username');
  }

  logout() {
      sessionStorage.clear();
      this.router.navigate(['/login']);
    }
}
