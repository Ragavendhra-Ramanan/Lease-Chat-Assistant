import { Injectable } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { Observable } from 'rxjs';
import { Login, User } from '../models/user.model';

@Injectable({
  providedIn: 'root'
})
export class AuthService {
  private apiUrl = 'http://localhost:5000/api/auth'; // 🔹 Change to your backend URL

  constructor(private http: HttpClient) {}

  login(login:Login): Observable<any> {
    return this.http.post(`${this.apiUrl}/login`, login);
  }

  signup(user:User): Observable<any> {
    return this.http.post(`${this.apiUrl}/signup`,user);
  }
}