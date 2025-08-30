import { Injectable } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { Observable } from 'rxjs';
import { AuthResponse, GuestLogin, Login, User } from '../models/user.model';

@Injectable({
  providedIn: 'root'
})
export class AuthService {
  private apiUrl = 'http://localhost:8000/api/auth';

  constructor(private http: HttpClient) {}

  login(login:Login): Observable<AuthResponse> {
    return this.http.post<AuthResponse>(`${this.apiUrl}/login`, login);
  }

  signup(user:User): Observable<any> {
    return this.http.post(`${this.apiUrl}/signup`,user);
  }
  guestLogin(login:GuestLogin): Observable<AuthResponse>{
    return this.http.post<AuthResponse>(`${this.apiUrl}/guestLogin`, login);
  }
}