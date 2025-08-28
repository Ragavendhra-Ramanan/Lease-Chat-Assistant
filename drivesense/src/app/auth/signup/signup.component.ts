// signup.component.ts
import { Component } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { Router, RouterModule } from '@angular/router';
import { AuthService } from '../../services/auth.service';
import { User } from '../../models/user.model';
import { ToastrService } from 'ngx-toastr';

@Component({
  selector: 'app-signup',
  standalone: true,
  imports: [CommonModule, FormsModule, RouterModule],
  templateUrl: './signup.component.html',
  styleUrls: ['./signup.component.scss'],
})
export class SignupComponent {
  user: User = {
    firstName: '',
    lastName: '',
    email: '',
    mobile: '',
    country: '',
    password: '',
  };
  constructor(
    private router: Router,
    private authService: AuthService,
    private toastr: ToastrService
  ) {}

  signup(form : any) {
    if (form.invalid || (!this.user.email && !this.user.mobile)) {
      return;
    }
    this.authService.signup(this.user).subscribe({
      next: (res) => {
        if (res.value) {
          this.toastr.success('Signup successful!');
          this.router.navigate(['/login']);       
        } else {
          this.toastr.error('Signup failed!');
        }
      },
    });
  }
}
