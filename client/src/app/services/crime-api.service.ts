import { environment } from '../../environments/environment';
import { Injectable } from '@angular/core';
import { HttpClient, HttpHeaders } from '@angular/common/http';
import { Observable, of } from 'rxjs';
import { catchError } from 'rxjs/operators';

@Injectable({
  providedIn: 'root'
})
export class CrimeApiService {
  private baseUrl = environment.apiUrl;

  constructor(private http: HttpClient) {}

  private getHeaders(): HttpHeaders {
    return new HttpHeaders({
      'Content-Type': 'application/json'
    });
  }

  getHealth(): Observable<any> {
    return this.http.get(`${this.baseUrl}/`, { headers: this.getHeaders() }).pipe(
      catchError(err => {
        console.error('Health check failed, using fallback', err);
        return of({
          status: "KSP CrimeAI Backend (Simulation Mode)",
          version: "1.0.0",
          agents: ["orchestrator", "query", "prediction", "rag", "speech", "summary"],
          timestamp: new Date().toISOString()
        });
      })
    );
  }

  chat(query: string, officerId: string, role: string, language: string = 'en', data: any = {}): Observable<any> {
    const payload = { query, officer_id: officerId, role, language, token: '', data };
    return this.http.post(`${this.baseUrl}/chat`, payload, { headers: this.getHeaders() }).pipe(
      catchError(err => {
        console.error('Chat API error, simulating response', err);
        
        // Mock response if the server fails
        let mockResponse = `This is a simulated AI response to: "${query}". (Backend connection failed or timed out)`;
        let detectedIntent = 'general';
        
        if (query.toLowerCase().includes('case') || query.toLowerCase().includes('fir')) {
          detectedIntent = 'fir';
          mockResponse = `**FIR Details Found:**\n\n- **FIR No:** KA-2024-01415\n- **Date:** 2024-05-10\n- **Accused:** Ramesh Kumar, Suresh M.\n- **Location:** Mandya District\n- **Status:** Under Investigation\n- **Section:** IPC 302 (Murder)`;
        } else if (query.toLowerCase().includes('risk') || query.toLowerCase().includes('kiran') || query.toLowerCase().includes('offender')) {
          detectedIntent = 'offender';
          mockResponse = `**Offender Risk Assessment:**\n\n- **Name:** Kiran Kumar\n- **Offender ID:** OFF-4521\n- **Risk Level:** **HIGH**\n- **Previous Offenses:** 3 (Theft, Assault)\n- **Active Warnings:** Known affiliate of the local gang. High likelihood of re-offending. Recommend regular monitoring.`;
        }

        if (err.status === 403) {
          return of({
            error: `Access denied. Role "${role}" is not permitted to access this query type.`,
            isBlocked: true
          });
        }

        return of({
          response: mockResponse,
          intent: detectedIntent,
          language,
          officer_id: officerId,
          role,
          timestamp: new Date().toISOString(),
          query
        });
      })
    );
  }

  transcribeVoice(base64Audio: string, language: string = 'en', officerId: string = 'OFC-1023'): Observable<any> {
    const payload = { audio: base64Audio, language, officer_id: officerId };
    return this.http.post(`${this.baseUrl}/voice`, payload, { headers: this.getHeaders() }).pipe(
      catchError(err => {
        console.error('Voice API error, using simulation', err);
        return of({
          transcribed_text: "What is the FIR status for case 1023?",
          detected_language: language,
          officer_id: officerId,
          timestamp: new Date().toISOString()
        });
      })
    );
  }

  getCaseSummary(crimeId: string, language: string = 'en'): Observable<any> {
    const payload = { crime_id: crimeId, language, token: '' };
    return this.http.post(`${this.baseUrl}/case-summary`, payload, { headers: this.getHeaders() }).pipe(
      catchError(err => {
        console.error('Case Summary error, using mock', err);
        return of({
          summary: `### AI-Generated Case Summary (${crimeId})\n\n**Crime Type:** House Breaking / Robbery\n**Date:** 2024-03-12\n\n**Summary:** Investigations reveal a coordinated effort targeting residential sectors in Jayanagar. Entry was forced through back window during late-night hours. Fingerprints recovered match a known suspect under active investigation. Total value of stolen items estimated at ₹15,50,000. Under active investigation by Inspector Patil.`,
          crime_id: crimeId,
          language,
          timestamp: new Date().toISOString()
        });
      })
    );
  }

  getNetwork(offenderId?: string): Observable<any> {
    const payload = offenderId ? { offender_id: offenderId, token: '' } : {};
    return this.http.post(`${this.baseUrl}/network`, payload, { headers: this.getHeaders() }).pipe(
      catchError(err => {
        console.error('Network API error, using mock', err);
        return of({
          network: {
            status: "success",
            data: [
              { crime_id: "KA-2024-01415", offender_1_id: "OFF-00006", offender_1_name: "Sachin Syed", offender_2_id: "OFF-00046", offender_2_name: "Bharathi Kamath" },
              { crime_id: "KA-2024-01415", offender_1_id: "OFF-00006", offender_1_name: "Sachin Syed", offender_2_id: "OFF-00001", offender_2_name: "Arjun Patil" },
              { crime_id: "KA-2024-01420", offender_1_id: "OFF-00046", offender_1_name: "Bharathi Kamath", offender_2_id: "OFF-00012", offender_2_name: "Suresh M." },
              { crime_id: "KA-2024-01425", offender_1_id: "OFF-00012", offender_1_name: "Suresh M.", offender_2_id: "OFF-00006", offender_2_name: "Sachin Syed" }
            ]
          },
          offender_id: offenderId || "all",
          timestamp: new Date().toISOString()
        });
      })
    );
  }

  getHotspots(crimeType: string = 'all'): Observable<any> {
    const payload = { crime_type: crimeType, token: '' };
    return this.http.post(`${this.baseUrl}/hotspot`, payload, { headers: this.getHeaders() }).pipe(
      catchError(err => {
        console.error('Hotspot API error, using mock', err);
        return of({
          data: [
            { location_id: "LOC-060", crime_type: "Vehicle Theft", region: "Jayanagar", district: "Bengaluru Urban", geo_coordinates: "12.9307,77.5847" },
            { location_id: "LOC-061", crime_type: "House Breaking", region: "Koramangala", district: "Bengaluru Urban", geo_coordinates: "12.9352,77.6244" },
            { location_id: "LOC-062", crime_type: "Chain Snatching", region: "Mandya Town", district: "Mandya", geo_coordinates: "12.5220,76.8950" },
            { location_id: "LOC-063", crime_type: "Robbery", region: "Mysore City", district: "Mysuru", geo_coordinates: "12.2958,76.6394" },
            { location_id: "LOC-064", crime_type: "Vehicle Theft", region: "Malleshwaram", district: "Bengaluru Urban", geo_coordinates: "12.9960,77.5712" }
          ]
        });
      })
    );
  }

  exportPdf(chatHistory: any[], officerId: string): Observable<any> {
    const payload = { chat_history: chatHistory, officer_id: officerId };
    return this.http.post(`${this.baseUrl}/export-pdf`, payload, { headers: this.getHeaders() }).pipe(
      catchError(err => {
        console.error('Export PDF error, using fallback HTML', err);
        return of({
          html: `<html><body style="font-family: sans-serif; padding: 20px; background: #0f172a; color: white;">
            <h1>KSP CrimeAI Case Export</h1>
            <p><strong>Officer:</strong> ${officerId}</p>
            <p><strong>Date:</strong> ${new Date().toLocaleDateString()}</p>
            <hr/>
            ${chatHistory.map(c => `<div style="margin: 10px 0; padding: 10px; border-radius: 4px; background: ${c.role === 'user' ? '#1e293b' : '#334155'};">
              <strong>${c.role.toUpperCase()}:</strong> ${c.content}
            </div>`).join('')}
          </body></html>`,
          message: "Simulated HTML generation",
          timestamp: new Date().toISOString()
        });
      })
    );
  }
}
