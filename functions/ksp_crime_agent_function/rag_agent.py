import json
import urllib.request
import urllib.error

# ============================================================
# KSP CrimeAI — RAG Agent
# Searches Knowledge Base for FIR documents and reports
# ============================================================

def search_knowledge_base(query, project_id, token):
    """Search RAG Knowledge Base in Catalyst QuickML"""
    try:
        url = f"https://api.catalyst.zoho.in/quickml/v1/project/{project_id}/rag/answer"
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Zoho-oauthtoken {token}",
            "CATALYST-ORG": "60072886153"
        }
        payload = json.dumps({"query": query}).encode("utf-8")
        req = urllib.request.Request(url, data=payload, headers=headers, method="POST")
        with urllib.request.urlopen(req) as response:
            return json.loads(response.read().decode("utf-8"))
    except urllib.error.HTTPError as e:
        return {"error": f"HTTP {e.code}", "details": e.read().decode("utf-8")}
    except Exception as e:
        return {"error": str(e)}

def search_fir_document(fir_number, project_id, token):
    """Search for specific FIR document"""
    query = f"Find details about FIR number {fir_number}"
    return search_knowledge_base(query, project_id, token)

def search_ipc_section(ipc_section, project_id, token):
    """Search for IPC section details"""
    query = f"What does IPC section {ipc_section} say? What are the penalties?"
    return search_knowledge_base(query, project_id, token)

def search_crime_procedure(crime_type, project_id, token):
    """Search for investigation procedure for a crime type"""
    query = f"What is the investigation procedure for {crime_type} cases in Karnataka?"
    return search_knowledge_base(query, project_id, token)

def search_similar_cases(description, project_id, token):
    """Search for similar past cases"""
    query = f"Find similar cases to: {description}"
    return search_knowledge_base(query, project_id, token)

def handle_rag_query(intent, query, project_id, token):
    """Route to correct RAG search based on intent"""
    
    query_lower = query.lower()
    
    # Check for FIR number
    words = query.split()
    for word in words:
        if word.startswith('FIR/') or word.startswith('FIR-'):
            return search_fir_document(word, project_id, token)
    
    # Check for IPC section
    if 'ipc' in query_lower or 'section' in query_lower:
        for word in words:
            if word.isdigit():
                return search_ipc_section(word, project_id, token)
    
    # Check for procedure queries
    if 'procedure' in query_lower or 'how to' in query_lower or 'process' in query_lower:
        crime_types = ['murder', 'theft', 'cybercrime', 'assault', 'robbery', 'fraud']
        for crime in crime_types:
            if crime in query_lower:
                return search_crime_procedure(crime, project_id, token)
    
    # Check for similar cases
    if 'similar' in query_lower or 'like this' in query_lower or 'past cases' in query_lower:
        return search_similar_cases(query, project_id, token)
    
    # Default - general knowledge base search
    return search_knowledge_base(query, project_id, token)