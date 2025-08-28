// login.component.ts
import { Component } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { Router, RouterModule } from '@angular/router';
import { AuthService } from '../../services/auth.service';
import { Login } from '../../models/user.model';
import { ToastrService } from 'ngx-toastr';

@Component({
  selector: 'app-login',
  standalone: true,
  imports: [CommonModule, FormsModule, RouterModule],
  templateUrl: './login.component.html',
  styleUrls: ['./login.component.scss'],
})
export class LoginComponent {
  auth: Login = {
    userName: '',
    password: '',
  };

  constructor(
    private router: Router,
    private authService: AuthService,
    private toastr: ToastrService
  ) {}

  login(form: any) {
    if (form.invalid) {
      return;
    }
    this.authService.login(this.auth).subscribe({
      next: (res) => {
        if (res.userId) {
          localStorage.setItem('token', res.userId);
          this.toastr.success('login successful!');
          this.router.navigate(['/chatlayout']);
        } else {
          this.toastr.error('login failed!');
        }
      },
    });
  }
}
