// signup.component.ts
import { Component } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { Router, RouterModule } from '@angular/router';
import { AuthService } from '../../services/auth.service';
import { User } from '../../models/user.model';

@Component({
  selector: 'app-signup',
  standalone: true,
  imports: [CommonModule, FormsModule, RouterModule],
  templateUrl: './signup.component.html',
  styleUrls: ['./signup.component.scss']
})
export class SignupComponent {
  user:User ={
    firstName:'',
    lastName:'',
    email:'',
    mobile:'',
    password:''
  };

  constructor(private router: Router,private authService: AuthService) {
  }

  signup() {
    console.log('Login successful:', this.user)
    if (!this.user.firstName || !this.user.password) {
      alert('Name and password are required');
      return;
    }

    if (!this.user.email && !this.user.mobile) {
      alert('Please provide at least email or mobile number');
      return;
    }

this.authService.signup(this.user).subscribe({
      next: (res) => {
        console.log('Signup response:',this.user, res);
        if (res.success) {
          alert('Signup successful! Please login.');
          this.router.navigate(['/login']);
        } else {
          alert(res.message || 'Signup failed. Try again.');
        }
      },
      error: (err) => {
        console.error('Signup error:', err);
        alert('Something went wrong during signup.');
      }
    });
  }
}

