import json
import urllib.request
import urllib.error

# ============================================================
# KSP CrimeAI — Summary Agent
# Combines all agent outputs and formats final answer using LLM
# ============================================================

CRIME_TYPE_MAP = {
    0: "Theft", 1: "Murder", 2: "Cybercrime", 
    3: "Assault", 4: "Robbery", 5: "Fraud", 6: "Kidnapping"
}

RISK_MAP = {0: "LOW RISK", 1: "MEDIUM RISK", 2: "HIGH RISK"}

def format_fir_response(data, language='en'):
    """Format FIR data into readable response"""
    try:
        if "error" in data:
            return f"Error fetching FIR data: {data['error']}"
        
        rows = data.get('data', [])
        if not rows:
            return "No FIR records found for your query."
        
        if language == 'kn':
            response = "📋 **ಎಫ್‌ಐಆರ್ ವಿವರಗಳು:**\n\n"
        else:
            response = "📋 **FIR Details:**\n\n"
        
        for row in rows[:5]:
            crime = row.get('crime_incidents', row)
            response += f"• **Crime ID:** {crime.get('crime_id', 'N/A')}\n"
            response += f"  **Type:** {crime.get('crime_type', 'N/A')}\n"
            response += f"  **Date:** {crime.get('crime_date', 'N/A')}\n"
            response += f"  **Status:** {crime.get('status', 'N/A')}\n"
            response += f"  **FIR No:** {crime.get('fir_number', 'N/A')}\n"
            response += f"  **Description:** {crime.get('description', 'N/A')[:100]}...\n\n"
        
        return response
    except Exception as e:
        return f"Error formatting response: {str(e)}"

def format_offender_response(data, language='en'):
    """Format offender data into readable response"""
    try:
        if "error" in data:
            return f"Error fetching offender data: {data['error']}"
        
        rows = data.get('data', [])
        if not rows:
            return "No offender records found."
        
        if language == 'kn':
            response = "👤 **ಆರೋಪಿ ವಿವರಗಳು:**\n\n"
        else:
            response = "👤 **Offender Details:**\n\n"
        
        for row in rows[:5]:
            offender = row.get('offenders', row)
            response += f"• **Name:** {offender.get('name', 'N/A')}\n"
            response += f"  **Offender ID:** {offender.get('offender_id', 'N/A')}\n"
            response += f"  **Age:** {offender.get('age', 'N/A')}\n"
            response += f"  **Gender:** {offender.get('gender', 'N/A')}\n"
            response += f"  **Linked Crime:** {offender.get('crime_id', 'N/A')}\n\n"
        
        return response
    except Exception as e:
        return f"Error formatting response: {str(e)}"

def format_prediction_response(data, language='en'):
    """Format ML prediction into readable response"""
    try:
        if "error" in data:
            return f"Prediction error: {data['error']}"
        
        message = data.get('message', '')
        
        if language == 'kn':
            prefix = "🔮 **ಮುನ್ಸೂಚನೆ:**\n"
        else:
            prefix = "🔮 **Prediction:**\n"
        
        return f"{prefix}{message}"
    except Exception as e:
        return f"Error formatting prediction: {str(e)}"

def format_rag_response(data, language='en'):
    """Format RAG knowledge base response"""
    try:
        if "error" in data:
            return f"Document search error: {data['error']}"
        
        answer = data.get('answer', data.get('response', str(data)))
        
        if language == 'kn':
            prefix = "📚 **ದಾಖಲೆಗಳಿಂದ:**\n"
        else:
            prefix = "📚 **From Documents:**\n"
        
        return f"{prefix}{answer}"
    except Exception as e:
        return f"Error formatting RAG response: {str(e)}"

def format_network_response(data, language='en'):
    """Format criminal network data"""
    try:
        if "error" in data:
            return f"Network analysis error: {data['error']}"
        
        rows = data.get('data', [])
        if not rows:
            return "No criminal network connections found."
        
        if language == 'kn':
            response = "🕸️ **ಅಪರಾಧ ಜಾಲ:**\n\n"
        else:
            response = "🕸️ **Criminal Network:**\n\n"
        
        connections = set()
        for row in rows[:10]:
            o1 = row.get('offenders', {})
            response += f"• Connection found: {o1.get('name', 'Unknown')}\n"
        
        return response
    except Exception as e:
        return f"Error formatting network: {str(e)}"

def build_final_response(intent, query_result, prediction_result, 
                         rag_result, language, officer_role):
    """Build complete final response combining all agent outputs"""
    
    response_parts = []
    
    # Add role-based header
    if language == 'kn':
        header = f"🚔 **KSP CrimeAI ಉತ್ತರ:**\n\n"
    else:
        header = f"🚔 **KSP CrimeAI Response:**\n\n"
    
    response_parts.append(header)
    
    # Add query result
    if query_result:
        if intent == 'fir' or intent == 'location' or intent == 'summary':
            response_parts.append(format_fir_response(query_result, language))
        elif intent == 'offender':
            response_parts.append(format_offender_response(query_result, language))
        elif intent == 'network':
            response_parts.append(format_network_response(query_result, language))
    
    # Add prediction result
    print(f"Prediction in summary: {prediction_result}")
    if prediction_result and "error" not in prediction_result:
        response_parts.append(format_prediction_response(prediction_result, language))
    
    # Add RAG result
    if rag_result and "error" not in rag_result:
        response_parts.append(format_rag_response(rag_result, language))
    
    # Add role-based disclaimer
    if officer_role == 'policymaker':
        if language == 'kn':
            response_parts.append("\n📊 *ನೀತಿ ನಿರ್ಧಾರಕ್ಕಾಗಿ ವಿಶ್ಲೇಷಣೆ*")
        else:
            response_parts.append("\n📊 *Analysis for policy decision making*")
    elif officer_role == 'analyst':
        if language == 'kn':
            response_parts.append("\n🔍 *ವಿಶ್ಲೇಷಕ ವೀಕ್ಷಣೆ*")
        else:
            response_parts.append("\n🔍 *Analyst view — full database access*")
    
    # Add audit note
    response_parts.append(f"\n\n🔒 *Query logged for audit compliance*")
    
    final_response = "\n".join(filter(None, response_parts))
    
    return final_response

def generate_case_summary(crime_data, victim_data, investigation_data, language='en'):
    """Generate AI case summary from multiple data sources"""
    try:
        crimes = crime_data.get('data', [])
        victims = victim_data.get('data', [])
        investigations = investigation_data.get('data', [])
        
        if not crimes:
            return "No case data found to generate summary."
        
        crime = crimes[0].get('crime_incidents', crimes[0])
        
        if language == 'kn':
            summary = f"""📋 **AI ಪ್ರಕರಣ ಸಾರಾಂಶ**
            
**ಪ್ರಕರಣ:** {crime.get('crime_id', 'N/A')}
**ಅಪರಾಧ ವಿಧ:** {crime.get('crime_type', 'N/A')}
**ದಿನಾಂಕ:** {crime.get('crime_date', 'N/A')}
**ಸ್ಥಿತಿ:** {crime.get('status', 'N/A')}
**ವಿವರಣೆ:** {crime.get('description', 'N/A')}

**ಬಲಿಪಶುಗಳು:** {len(victims)} ಜನರು ಪರಿಣಾಮ ಹೊಂದಿದ್ದಾರೆ
**ತನಿಖೆ:** {investigations[0].get('investigations', {}).get('status', 'Pending') if investigations else 'Pending'}"""
        else:
            summary = f"""📋 **AI Generated Case Summary**

**Case ID:** {crime.get('crime_id', 'N/A')}
**Crime Type:** {crime.get('crime_type', 'N/A')}
**Date:** {crime.get('crime_date', 'N/A')}
**Status:** {crime.get('status', 'N/A')}
**FIR Number:** {crime.get('fir_number', 'N/A')}
**Description:** {crime.get('description', 'N/A')}

**Victims Affected:** {len(victims)} person(s)
**Investigation Status:** {investigations[0].get('investigations', {}).get('status', 'Pending') if investigations else 'Pending'}
**IPC Section:** {crime.get('ipc_section', 'N/A')}

🔒 *AI Summary generated — All data referenced from KSP Crime Database*"""
        
        return summary
    except Exception as e:
        return f"Error generating case summary: {str(e)}"