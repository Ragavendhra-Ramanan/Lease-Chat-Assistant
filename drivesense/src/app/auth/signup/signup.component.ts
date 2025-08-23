// signup.component.ts
import { Component } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { Router, RouterModule } from '@angular/router';

@Component({
  selector: 'app-signup',
  standalone: true,
  imports: [CommonModule, FormsModule, RouterModule],
  templateUrl: './signup.component.html',
  styleUrls: ['./signup.component.scss']
})
export class SignupComponent {
  firstname = '';
  lastname=''
  email = '';
  mobile = '';
  password = '';

  constructor(private router: Router) {}

  signup() {
    if (!this.firstname || !this.password) {
      alert('Name and password are required');
      return;
    }

    if (!this.email && !this.mobile) {
      alert('Please provide at least email or mobile number');
      return;
    }

    // TODO: Call auth service to register user
    console.log('Signup successful:', {
      firstnamename: this.firstname,
      email: this.email,
      mobile: this.mobile,
      password: this.password
    });

    this.router.navigate(['/login']);
  }
}
