import { Component, OnInit } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { Router } from '@angular/router';

declare var catalyst: any;

@Component({
  selector: 'app-login',
  standalone: true,
  imports: [CommonModule, FormsModule],
  templateUrl: './login.component.html',
  styleUrls: ['./login.component.css']
})
export class LoginComponent implements OnInit {
  isRegisterMode = false;
  useCatalystAuth = false;

  // Form Fields
  fullName = 'Arjun Patil';
  badgeId = 'KSP-BLR-04821';
  designation = 'Sub-Inspector';
  role = 'sub_inspector';
  district = 'Bengaluru Urban';
  policeStation = 'Jayanagar PS';
  email = 'arjun.patil@ksp.gov.in';
  password = '••••••••';
  confirmPassword = '••••••••';
  preferredLanguage = 'kn'; // 'kn' (Kannada), 'en' (English), 'hi' (Hindi), 'ur' (Urdu)
  termsAccepted = true;

  // Login mode specific
  loginId = 'KSP-BLR-04821';
  loginPassword = 'password123';
  loginRole = 'inspector'; // default to inspector for demo

  constructor(private router: Router) {}

  ngOnInit() {
  
}

  toggleMode() {
    this.isRegisterMode = !this.isRegisterMode;
  }

  handleLogin() {
    // Store user session in localStorage for mockup session persistency
    const officerDetails = {
      name: this.loginId === 'KSP-BLR-04821' ? 'Arjun Patil' : 'Officer ' + this.loginId,
      badge: this.loginId,
      role: this.loginRole, // 'sub_inspector', 'inspector', 'senior_inspector', 'analyst', 'policymaker'
      district: this.district || 'Bengaluru Urban',
      station: this.policeStation || 'Jayanagar PS',
      email: this.email || 'officer@ksp.gov.in',
      language: this.preferredLanguage
    };

    localStorage.setItem('ksp_officer', JSON.stringify(officerDetails));
    this.router.navigate(['/dashboard']);
  }

  handleRegister() {
    if (!this.termsAccepted) {
      alert('Please accept the data governance policy terms.');
      return;
    }

    const officerDetails = {
      name: this.fullName,
      badge: this.badgeId,
      role: this.role,
      district: this.district,
      station: this.policeStation,
      email: this.email,
      language: this.preferredLanguage
    };

    localStorage.setItem('ksp_officer', JSON.stringify(officerDetails));
    alert('Registration request submitted to SP. Simulating secure entry...');
    this.router.navigate(['/dashboard']);
  }

  selectLanguage(lang: string) {
    this.preferredLanguage = lang;
  }

  selectRole(roleVal: string) {
    this.role = roleVal;
    
    // Auto sync designation
    if (roleVal === 'sub_inspector') {
      this.designation = 'Sub-Inspector';
    } else if (roleVal === 'inspector') {
      this.designation = 'Inspector';
    } else if (roleVal === 'senior_inspector') {
      this.designation = 'Senior Inspector';
    } else if (roleVal === 'analyst') {
      this.designation = 'Analyst';
    } else if (roleVal === 'policymaker') {
      this.designation = 'Policymaker';
    }
  }
}
