// app.config.ts
import { ApplicationConfig } from '@angular/core';
import { provideRouter, Routes } from '@angular/router';
import { LoginComponent } from './auth/login/login.component';
import { SignupComponent } from './auth/signup/signup.component';
import { ChatLayoutComponent } from './modules/chat-layout/chat-layout.component';

const routes: Routes = [
  { path: '', redirectTo: 'login', pathMatch: 'full' },
  { path: 'login', component: LoginComponent },
  { path: 'signup', component: SignupComponent },
  { path: 'chatlayout', component: ChatLayoutComponent }
];

export const appConfig: ApplicationConfig = {
  providers: [provideRouter(routes)]
};
