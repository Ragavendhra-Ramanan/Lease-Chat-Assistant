// login.component.ts
import { Component } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { Router, RouterModule } from '@angular/router';
import { AuthService } from '../../services/auth.service';
import { GuestLogin, Login } from '../../models/user.model';
import { ToastrService } from 'ngx-toastr';

@Component({
  selector: 'app-login',
  standalone: true,
  imports: [CommonModule, FormsModule, RouterModule],
  templateUrl: './login.component.html',
  styleUrls: ['./login.component.scss'],
})
export class LoginComponent {
   loginMode: string='';
  auth: Login = {
    userName: '',
    password: '',
  };

  guest :GuestLogin={
    name:'',
    contact:''
  }

  constructor(
    private router: Router,
    private authService: AuthService,
    private toastr: ToastrService
  ) {}
   setLoginMode(mode: 'user' | 'guest') {
    this.loginMode = mode;
  }

  login(form: any) {
    if (form.invalid) {
      return;
    }
    this.authService.login(this.auth).subscribe(res => {
        if (res.userId) {
          localStorage.setItem('token', res.userId);
          this.toastr.success('login successful!');
          this.router.navigate(['/chatlayout']);
        } else {
          this.toastr.error('login failed!');        
      }
    });
  }

    guestLogin(form: any) {
     if (form.invalid) {
      return;
    }
    this.authService.guestLogin(this.guest).subscribe(res => {
        if (res.userId) {
          localStorage.setItem('token', res.userId);
          this.toastr.success('login successful!');
          this.router.navigate(['/chatlayout']);
        } else {
          this.toastr.error('login failed!');        
      }
    });
  }
}
