// login.component.ts
import { Component } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { Router, RouterModule } from '@angular/router';
import { AuthService } from '../../services/auth.service';
import { Login } from '../../models/user.model';

@Component({
  selector: 'app-login',
  standalone: true,
  imports: [CommonModule, FormsModule, RouterModule],
  templateUrl: './login.component.html',
  styleUrls: ['./login.component.scss']
})
export class LoginComponent {
  auth: Login = {
    userName: '',
    password: ''
  };

  constructor(private router: Router, private authService: AuthService) {}

  login() {
console.log('Login response:', this.auth);

    if (!this.auth.userName || !this.auth.password) {
      alert('Please enter email/phone and password');
      return;
    }

    this.authService.login(this.auth).subscribe({
      next: (res) => {
        console.log('Login response:', res);
        if (res.userId) {
          localStorage.setItem('token', res.userId);
          alert('Login successful!');
          this.router.navigate(['/chatlayout']);
        } else {
          alert('Invalid credentials');
        }
      }
    });
  }
}
