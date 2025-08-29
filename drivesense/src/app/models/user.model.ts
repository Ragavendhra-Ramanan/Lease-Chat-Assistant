export interface User {
  firstName: string;
  lastName: string;
  email: string;
  mobile: string;
  country: string;
  password: string;
}

export interface Login{
  userName: string;
  password:string;
}

export interface GuestLogin{
  name: string;
  contact: string;
}