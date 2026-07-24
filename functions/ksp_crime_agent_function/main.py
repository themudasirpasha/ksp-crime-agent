from flask import Flask, request, jsonify, Request
from datetime import datetime
import json
import zcatalyst_sdk

# Import all agents
from query_agent import handle_query, build_offender_features
from token_manager import get_fresh_token
from token_manager import get_fresh_token, get_fresh_ml_token
from prediction_agent import handle_prediction
from rag_agent import handle_rag_query
from summary_agent import build_final_response, generate_case_summary
from speech_agent import handle_voice_query, handle_voice_response, detect_language

app = Flask(__name__)


# ============================================================
# KSP CrimeAI — Main Orchestrator
# Entry point connecting all agents
# ============================================================

PROJECT_ID = "43110000000018001"
# ============================================================
# RBAC — Role-Based Access Control
# ============================================================

ROLE_PERMISSIONS = {
    "sub_inspector": {
        "allowed_intents": ["fir", "location", "victim"],
        "access_level": "basic"
    },
    "inspector": {
        "allowed_intents": ["fir", "location", "victim", "offender", "predict",
                             "network", "financial", "summary"],
        "access_level": "full"
    },
    "senior_inspector": {
        "allowed_intents": ["fir", "location", "victim", "offender", "predict",
                             "network", "financial", "summary"],
        "access_level": "full"
    },
    "analyst": {
        "allowed_intents": ["fir", "location", "victim", "offender", "predict",
                             "network", "financial", "summary"],
        "access_level": "full"
    },
    "policymaker": {
        "allowed_intents": ["summary", "location"],
        "access_level": "aggregate_only"
    },
    "App Administrator": {
        "allowed_intents": ["fir", "location", "victim", "offender", "predict",
                             "network", "financial", "summary"],
        "access_level": "full"
    }
}


def get_officer_role():
    """Fetch the current logged-in officer's role from Catalyst Authentication.
    Only works when the app is deployed on Catalyst (not on localhost)."""
    try:
        catalyst_app = zcatalyst_sdk.initialize()
        authentication_service = catalyst_app.authentication()
        current_user = authentication_service.get_current_user()
        role_name = current_user.get("role_details", {}).get("role_name", "App User")
        return role_name
    except Exception as e:
        print(f"Could not fetch Catalyst user role: {e}")
        return None


def is_intent_allowed(role_name, intent):
    """Check if the given role is allowed to access the given intent"""
    if not role_name:
        # Fallback for local testing when Catalyst session isn't available
        return True
    permissions = ROLE_PERMISSIONS.get(role_name)
    if not permissions:
        return False
    return intent in permissions["allowed_intents"]

INTENT_PATTERNS = {
    'fir': ['fir', 'case', 'incident', 'complaint', 'ಎಫ್‌ಐಆರ್', 'ಪ್ರಕರಣ'],
    'offender': ['offender', 'accused', 'criminal', 'suspect', 'ಆರೋಪಿ', 'ಅಪರಾಧಿ'],
    'victim': ['victim', 'complainant', 'ಸಂತ್ರಸ್ತ', 'ಬಲಿಪಶು'],
    'location': ['location', 'district', 'area', 'where', 'ಜಿಲ್ಲೆ', 'ಸ್ಥಳ'],
    'predict': ['predict', 'forecast', 'future', 'next', 'risk', 'likely', 'tonight', 'crime type', 'repeat', 'suspicious', 'vulnerab', 'sociological', 'hotspot', 'ಮುನ್ಸೂಚನೆ'],
    'network': ['network', 'gang', 'connected', 'linked', 'associate', 'ಜಾಲ', 'ಗ್ಯಾಂಗ್'],
    'financial': ['transaction', 'money', 'amount', 'bank', 'fraud', 'ಹಣ', 'ವಹಿವಾಟು'],
    'summary': ['summary', 'summarize', 'overview', 'timeline', 'ಸಾರಾಂಶ'],
}

def detect_intent(query):
    q = query.lower()
    for intent, keywords in INTENT_PATTERNS.items():
        if any(k in q for k in keywords):
            return intent
    return 'fir'

# ============================================================
# MAIN CHAT ENDPOINT
# ============================================================
@app.route('/chat', methods=['POST'])
def chat():
    try:
        data = request.get_json()
        query = data.get('query', '')
        officer_id = data.get('officer_id', 'unknown')
        role = data.get('role', 'investigator')
        language = data.get('language', 'en')
        ds_token = get_fresh_token()
        ml_token = get_fresh_ml_token()
        extra_data = data.get('data', {})

        if not query:
            return jsonify({'error': 'Query is required'}), 400

        # Auto detect language
        if detect_language(query) == 'kn':
            language = 'kn'

        # Detect intent
       # Detect intent
        # Detect intent
        intent = detect_intent(query)

        # RBAC check
        catalyst_role = get_officer_role()
        if catalyst_role and not is_intent_allowed(catalyst_role, intent):
            return jsonify({
                'error': f'Access denied. Role "{catalyst_role}" is not permitted to access "{intent}" queries.',
                'officer_id': officer_id,
                'timestamp': datetime.now().isoformat()
            }), 403

        print(f"[{datetime.now()}] Officer: {officer_id} | Role: {role} | Intent: {intent} | Lang: {language}")
        print(f"Query: {query}")

        # Extract probable name once — used by both query and prediction steps
        words = query.split()
        candidate_name = " ".join([w for w in words if w[:1].isupper()])

        # Step 1: Query agent — fetch from Data Store
        query_result = None
        if ds_token:
            if intent == 'offender' and candidate_name:
                query_result = handle_query(intent, candidate_name, ds_token)
            else:
                query_result = handle_query(intent, query, ds_token)

        # Step 2: Prediction agent — call ML models
        # Step 2: Prediction agent — call ML models
        prediction_result = None
        if ml_token and intent in ['predict', 'offender', 'network', 'financial']:
            if not extra_data and ('risk' in query.lower() or 'gang' in query.lower() or 'repeat' in query.lower()):
                if candidate_name:
                    print(f"Auto-fetching features for '{candidate_name}' from Data Store")
                    features = build_offender_features(candidate_name, ds_token)
                    if "error" not in features:
                        extra_data = features
                        print(f"Auto-fetched features: {features}")
                    else:
                        print(f"Auto-fetch failed: {features.get('error')}")

            print(f"Calling prediction for intent: {intent}")
            prediction_result = handle_prediction(intent, query, extra_data, ml_token)
            print(f"Prediction result: {prediction_result}")
        # Step 3: RAG agent — search knowledge base
        rag_result = None
        if ds_token:
            print(f"Token: {ds_token[:20] if ds_token else 'EMPTY'}")
            rag_result = handle_rag_query(intent, query, PROJECT_ID, ds_token)
            print(f"RAG Result: {rag_result}")

        # Step 4: Summary agent — build final response
        final_response = build_final_response(
            intent,
            query_result,
            prediction_result,
            rag_result,
            language,
            role
        )

        return jsonify({
            'response': final_response,
            'intent': intent,
            'language': language,
            'officer_id': officer_id,
            'role': role,
            'timestamp': datetime.now().isoformat(),
            'query': query
        }), 200

    except Exception as e:
        print(f"Error: {str(e)}")
        return jsonify({'error': str(e)}), 500

# ============================================================
# VOICE ENDPOINT
# ============================================================
@app.route('/voice', methods=['POST'])
def voice():
    try:
        data = request.get_json()
        audio_base64 = data.get('audio', '')
        language = data.get('language', 'en')
        officer_id = data.get('officer_id', 'unknown')

        if not audio_base64:
            return jsonify({'error': 'Audio data is required'}), 400

        # Convert speech to text
        stt_result = handle_voice_query(audio_base64, language)

        if "error" in stt_result:
            return jsonify(stt_result), 400

        return jsonify({
            'transcribed_text': stt_result.get('transcribed_text', ''),
            'detected_language': stt_result.get('detected_language', 'en'),
            'officer_id': officer_id,
            'timestamp': datetime.now().isoformat()
        }), 200

    except Exception as e:
        return jsonify({'error': str(e)}), 500

# ============================================================
# CASE SUMMARY ENDPOINT
# ============================================================
@app.route('/case-summary', methods=['POST'])
def case_summary():
    try:
        data = request.get_json()
        crime_id = data.get('crime_id', '')
        language = data.get('language', 'en')
        ds_token = data.get('token', '')

        if not crime_id:
            return jsonify({'error': 'crime_id is required'}), 400

        from query_agent import (get_fir_by_id, get_victims_by_crime, 
                                  get_investigation_status)

        crime_data = get_fir_by_id(crime_id, ds_token)
        victim_data = get_victims_by_crime(crime_id, ds_token)
        investigation_data = get_investigation_status(crime_id, ds_token)

        summary = generate_case_summary(
            crime_data, victim_data, investigation_data, language
        )

        return jsonify({
            'summary': summary,
            'crime_id': crime_id,
            'language': language,
            'timestamp': datetime.now().isoformat()
        }), 200

    except Exception as e:
        return jsonify({'error': str(e)}), 500

# ============================================================
# NETWORK GRAPH ENDPOINT
# ============================================================
@app.route('/network', methods=['POST'])
def network():
    try:
        data = request.get_json()
        offender_id = data.get('offender_id', '')
        ds_token = data.get('token', '')

        from query_agent import get_criminal_network
        network_data = get_criminal_network(offender_id, ds_token)

        return jsonify({
            'network': network_data,
            'offender_id': offender_id,
            'timestamp': datetime.now().isoformat()
        }), 200

    except Exception as e:
        return jsonify({'error': str(e)}), 500

# ============================================================
# HEALTH CHECK
# ============================================================
@app.route('/', methods=['GET'])
def health():
    return jsonify({
        'status': 'KSP CrimeAI Backend is Live!',
        'version': '1.0.0',
        'agents': ['orchestrator', 'query', 'prediction', 'rag', 'speech', 'summary'],
        'timestamp': datetime.now().isoformat()
    }), 200

@app.route('/hotspot', methods=['POST'])
def hotspot():
    try:
        data = request.get_json()
        crime_type = data.get('crime_type', 'all')
        token = data.get('token', '') or get_fresh_token()

        from query_agent import execute_zcql

        if crime_type == 'all':
            crimes_query = "SELECT location_id, crime_type FROM crime_incidents LIMIT 300"
        else:
            crimes_query = f"SELECT location_id, crime_type FROM crime_incidents WHERE crime_type = '{crime_type}' LIMIT 2000"

        locs_query = "SELECT location_id, region, district, geo_coordinates FROM locations"

        crimes_result = execute_zcql(crimes_query, token)
        locs_result = execute_zcql(locs_query, token)

        crimes = crimes_result.get('data', [])
        locs = locs_result.get('data', [])

        loc_map = {}
        for row in locs:
            l = row.get('locations', row)
            loc_map[l['location_id']] = l

        merged = []
        for row in crimes:
            c = row.get('crime_incidents', row)
            loc = loc_map.get(c.get('location_id', ''), {})
            merged.append({
                'location_id': c.get('location_id'),
                'crime_type': c.get('crime_type'),
                'region': loc.get('region', ''),
                'district': loc.get('district', ''),
                'geo_coordinates': loc.get('geo_coordinates', '')
            })

        return jsonify({'data': merged}), 200

    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/export-pdf', methods=['POST'])
def export_pdf():
    try:
        data = request.get_json()
        chat_history = data.get('chat_history', [])
        officer_id = data.get('officer_id', 'unknown')
        
        html_content = f"""<html><head><style>
        body {{ font-family: Arial; padding: 20px; background: #fff; }}
        h1 {{ color: #1a1a2e; }}
        .officer {{ background: #e8f4f8; padding: 10px; margin: 8px 0; border-radius: 5px; }}
        .ai {{ background: #f0f0f0; padding: 10px; margin: 8px 0; border-radius: 5px; }}
        </style></head><body>
        <h1>KSP CrimeAI — Conversation Export</h1>
        <p><b>Officer:</b> {officer_id} | <b>Date:</b> {datetime.now().strftime('%d-%m-%Y %H:%M')}</p><hr/>"""
        
        for msg in chat_history:
            role = msg.get('role', 'user')
            content = msg.get('content', '')
            css_class = 'officer' if role == 'user' else 'ai'
            label = 'Officer' if role == 'user' else 'KSP CrimeAI'
            html_content += f'<div class="{css_class}"><b>{label}:</b> {content}</div>'
        
        html_content += "</body></html>"
        
        return jsonify({
            'html': html_content,
            'message': 'PDF will be generated after deployment using SmartBrowz',
            'timestamp': datetime.now().isoformat()
        }), 200

    except Exception as e:
        return jsonify({'error': str(e)}), 500

def handler(request: Request):
    with app.request_context(request.environ):
        return app.full_dispatch_request()

if __name__ == '__main__':
    app.run(debug=True, use_reloader=False)