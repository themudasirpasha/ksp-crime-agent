import json
import urllib.request
import urllib.error
from token_manager import get_fresh_ml_token

# ============================================================
# KSP CrimeAI — Prediction Agent
# Calls 7 ML model endpoints and returns predictions
# ============================================================

BASE_URL = "https://api.catalyst.zoho.in/quickml/v1/project/48958000000013025/endpoints/predict"

ENDPOINT_KEYS = {
    "hotspot": "ee9a9d35dc86c926094bca2cd61f521670c694fc32be4993c8dd42254f41c99d32c12c458809c7fa463838b84f7d90a4",
    "offender_risk": "ebb1abe26a3857edb5c583cf9dcacc2392c3e290430c88fbf79d2e2a6b4ce415dbdb9ca0ebd14d7363a457719066438c",
    "crime_type": "4f4ebfac1f70cb47d2bd190085c26b46d8473ccc2f6b5575d05500e263f8254dcb87e8e3f737ac8f09c317daf97ae83a",
    "repeat_offender": "c6ce87887327862155241b8e401862c6f2a846ca3cdc1242d14fcc833799e95404e2a0c3784046f8d6011acf610912f3",
    "financial_anomaly": "2fe713ec892ac9db70dca7860994ead19410d0b0807fb631761e6ea1c85c77fe04b7d187cddf002cd363342156d452cf",
    "sociological_insights": "572317ec6c1a92ae39d8a993cc6b261466eebaa395e07208ba8876b8dfc7efeea3c43775c7b046cef72d7b398cd3a4b0",
    "gang_detection": "93535e464ebcdf499ab108e779419fcd6193cffa76d6be671e81971bacc5649958f21a26af161eccce6030449787f654"
}

# Decode maps
RISK_LEVEL = {0: "LOW RISK", 1: "MEDIUM RISK", 2: "HIGH RISK"}
CRIME_TYPE = {0: "Theft", 1: "Murder", 2: "Cybercrime", 3: "Assault", 4: "Robbery", 5: "Fraud", 6: "Kidnapping"}
DEMOGRAPHIC_RISK = {0: "LOW vulnerability", 1: "MEDIUM vulnerability", 2: "HIGH vulnerability"}


def call_ml_endpoint(model_key, payload, oauth_token=None):
    """Call a ML model endpoint"""
    try:
        # HAMESHA fresh ML token force karein, bhale hi bahar se koi bhi token pass ho raha ho!
        oauth_token = get_fresh_ml_token()

        if not oauth_token:
            return {"error": "Could not get OAuth token"}

        endpoint_key = ENDPOINT_KEYS.get(model_key)
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Zoho-oauthtoken {oauth_token}",
            "X-QUICKML-ENDPOINT-KEY": endpoint_key,
            "CATALYST-ORG": "60076171671",
            "Environment": "Development"
        }
        req_data = json.dumps({"data": payload}).encode("utf-8")
        req = urllib.request.Request(BASE_URL, data=req_data, headers=headers, method="POST")
        with urllib.request.urlopen(req) as response:
            return json.loads(response.read().decode("utf-8"))
    except urllib.error.HTTPError as e:
        return {"error": f"HTTP {e.code}", "details": e.read().decode("utf-8")}
    except Exception as e:
        return {"error": str(e)}


def predict_hotspot(location_rowid, month, year, theft_count, cybercrime_count,
                     assault_count, murder_count, fraud_count, oauth_token):
    """Predict crime count for a location"""
    payload = {
        "location_rowid": location_rowid,
        "month": month,
        "year": year,
        "theft_count": theft_count,
        "cybercrime_count": cybercrime_count,
        "assault_count": assault_count,
        "murder_count": murder_count,
        "fraud_count": fraud_count
    }
    result = call_ml_endpoint("hotspot", payload, oauth_token)
    if "error" not in result:
        raw_val = str(result.get("result", {})).strip("[]'\" ")
        count_val = float(raw_val) if raw_val else 0.0
        return {
            "prediction": count_val,
            "message": f"Predicted {count_val} crimes expected. {'HIGH RISK — Deploy extra patrol!' if count_val > 5 else 'Normal activity expected.'}"
        }
    return result


def predict_offender_risk(offender_rowid, total_crimes, crime_types_count,
                           years_active, repeat_offense_count, avg_crime_gap_days,
                           unique_locations, oauth_token):
    """Predict offender risk level"""
    payload = {
        "offender_rowid": offender_rowid,
        "total_crimes": total_crimes,
        "crime_types_count": crime_types_count,
        "years_active": years_active,
        "repeat_offense_count": repeat_offense_count,
        "avg_crime_gap_days": avg_crime_gap_days,
        "unique_locations": unique_locations
    }
    result = call_ml_endpoint("offender_risk", payload, oauth_token)
    if "error" not in result:
        raw_risk = str(result.get("result", 0)).strip("[]'\" ")
        risk_val = int(raw_risk.split('.')[0]) if raw_risk else 0

        risk_label = RISK_LEVEL.get(risk_val, "UNKNOWN")
        return {
            "prediction": risk_val,
            "risk_label": risk_label,
            "message": f"Offender is {risk_label}. {'Immediate surveillance recommended!' if risk_label == 'HIGH RISK' else 'Monitor regularly.' if risk_label == 'MEDIUM RISK' else 'No immediate action needed.'}"
        }
    return result


def predict_crime_type(location_rowid, month, year, hour_of_day, day_of_week,
                        past_theft, past_cybercrime, past_assault, oauth_token):
    """Predict crime type likely to occur"""
    payload = {
        "location_rowid": location_rowid,
        "month": month,
        "year": year,
        "hour_of_day": hour_of_day,
        "day_of_week": day_of_week,
        "past_theft": past_theft,
        "past_cybercrime": past_cybercrime,
        "past_assault": past_assault
    }
    result = call_ml_endpoint("crime_type", payload, oauth_token)
    if "error" not in result:
        raw_val = str(result.get("result", 0)).strip("[]'\" ")
        crime_code = int(raw_val.split('.')[0]) if raw_val else 0
        crime_label = CRIME_TYPE.get(crime_code, "Unknown")
        return {
            "prediction": crime_code,
            "crime_type": crime_label,
            "message": f"{crime_label} likely to occur at this location and time. Alert nearby stations!"
        }
    return result


def predict_repeat_offender(offender_rowid, crime_count, unique_locations,
                             unique_crime_types, first_crime_year, last_crime_year,
                             avg_crime_gap_days, oauth_token):
    """Predict if offender will repeat crime"""
    payload = {
        "offender_rowid": offender_rowid,
        "crime_count": crime_count,
        "unique_locations": unique_locations,
        "unique_crime_types": unique_crime_types,
        "first_crime_year": first_crime_year,
        "last_crime_year": last_crime_year,
        "avg_crime_gap_days": avg_crime_gap_days
    }
    result = call_ml_endpoint("repeat_offender", payload, oauth_token)
    if "error" not in result:
        raw_val = str(result.get("result", 0)).strip("[]'\" ")
        is_repeat_val = int(raw_val.split('.')[0]) if raw_val else 0
        return {
            "prediction": is_repeat_val,
            "is_repeat": bool(is_repeat_val),
            "message": f"This offender {'WILL repeat crime — Issue surveillance order!' if is_repeat_val == 1 else 'is unlikely to repeat crime.'}"
        }
    return result


def predict_financial_anomaly(transaction_rowid, amount, transaction_hour,
                               transactions_per_day, avg_amount, amount_deviation,
                               crime_rowid, oauth_token):
    """Predict if financial transaction is suspicious"""
    payload = {
        "transaction_rowid": transaction_rowid,
        "amount": amount,
        "transaction_hour": transaction_hour,
        "transactions_per_day": transactions_per_day,
        "avg_amount": avg_amount,
        "amount_deviation": amount_deviation,
        "crime_rowid": crime_rowid
    }
    result = call_ml_endpoint("financial_anomaly", payload, oauth_token)
    if "error" not in result:
        raw_val = str(result.get("result", 0)).strip("[]'\" ")
        is_suspicious_val = int(raw_val.split('.')[0]) if raw_val else 0
        return {
            "prediction": is_suspicious_val,
            "is_suspicious": bool(is_suspicious_val),
            "message": f"Transaction is {'SUSPICIOUS — Possible money laundering! Freeze account and investigate!' if is_suspicious_val == 1 else 'NORMAL — No action needed.'}"
        }
    return result


def predict_sociological_risk(age_group, gender_encoded, location_rowid, month,
                               crime_type_encoded, victim_count, offender_count, oauth_token):
    """Predict demographic vulnerability"""
    payload = {
        "age_group": age_group,
        "gender_encoded": gender_encoded,
        "location_rowid": location_rowid,
        "month": month,
        "crime_type_encoded": crime_type_encoded,
        "victim_count": victim_count,
        "offender_count": offender_count
    }
    result = call_ml_endpoint("sociological_insights", payload, oauth_token)
    if "error" not in result:
        raw_val = str(result.get("result", 0)).strip("[]'\" ")
        risk_val = int(raw_val.split('.')[0]) if raw_val else 0
        risk_label = DEMOGRAPHIC_RISK.get(risk_val, "UNKNOWN")
        age_labels = {0: "Minors (<18)", 1: "Young Adults (18-30)", 2: "Adults (31-45)", 3: "Middle-aged (46-60)", 4: "Elderly (60+)"}
        gender_labels = {0: "Male", 1: "Female", 2: "Other"}
        return {
            "prediction": risk_val,
            "risk_label": risk_label,
            "message": f"{age_labels.get(age_group, 'Unknown')} {gender_labels.get(gender_encoded, 'Unknown')} group shows {risk_label} — {'Community awareness program recommended!' if risk_val == 2 else 'Monitor this demographic.'}"
        }
    return result


def predict_gang_member(offender_rowid, shared_location_count, shared_victim_count,
                         shared_crime_type_count, co_accused_count,
                         location_overlap_score, crime_timing_similarity, oauth_token):
    """Predict if offender is a gang member"""
    payload = {
        "offender_rowid": offender_rowid,
        "shared_location_count": shared_location_count,
        "shared_victim_count": shared_victim_count,
        "shared_crime_type_count": shared_crime_type_count,
        "co_accused_count": co_accused_count,
        "location_overlap_score": location_overlap_score,
        "crime_timing_similarity": crime_timing_similarity
    }
    result = call_ml_endpoint("gang_detection", payload, oauth_token)
    if "error" not in result:
        raw_val = str(result.get("result", 0)).strip("[]'\" ")
        is_gang_val = int(raw_val.split('.')[0]) if raw_val else 0
        return {
            "prediction": is_gang_val,
            "is_gang_member": bool(is_gang_val),
            "message": f"Offender {'IS A GANG MEMBER — Alert organized crime unit! Connected to ' + str(co_accused_count) + ' co-accused.' if is_gang_val == 1 else 'is a lone criminal — No gang links detected.'}"
        }
    return result


def handle_prediction(intent, query, data, oauth_token):
    """Route to correct prediction based on intent"""
    q = query.lower()

    if 'hotspot' in q or 'forecast' in q:
        return predict_hotspot(
            data.get('location_rowid', 43110000000034001),
            data.get('month', 7), data.get('year', 2026),
            data.get('theft_count', 5), data.get('cybercrime_count', 3),
            data.get('assault_count', 2), data.get('murder_count', 0),
            data.get('fraud_count', 2), oauth_token
        )
    elif 'gang' in q:
        return predict_gang_member(
            data.get('offender_rowid', 43110000000038001),
            data.get('shared_location_count', 3), data.get('shared_victim_count', 2),
            data.get('shared_crime_type_count', 2), data.get('co_accused_count', 2),
            data.get('location_overlap_score', 0.6), data.get('crime_timing_similarity', 0.7),
            oauth_token
        )
    elif 'transaction' in q or 'suspicious' in q or 'financial' in q or 'money' in q:
        return predict_financial_anomaly(
            data.get('transaction_rowid', 43110000000040001), data.get('amount', 500000),
            data.get('transaction_hour', 2), data.get('transactions_per_day', 5),
            data.get('avg_amount', 15000), data.get('amount_deviation', 485000),
            data.get('crime_rowid', 43110000000034001), oauth_token
        )
    elif 'repeat' in q:
        return predict_repeat_offender(
            data.get('offender_rowid', 43110000000038001), data.get('crime_count', 3),
            data.get('unique_locations', 2), data.get('unique_crime_types', 2),
            data.get('first_crime_year', 2023), data.get('last_crime_year', 2025),
            data.get('avg_crime_gap_days', 90), oauth_token
        )
    elif 'risk' in q and 'offender' in q:
        return predict_offender_risk(
            data.get('offender_rowid', 43110000000038001), data.get('total_crimes', 3),
            data.get('crime_types_count', 2), data.get('years_active', 2),
            data.get('repeat_offense_count', 2), data.get('avg_crime_gap_days', 90),
            data.get('unique_locations', 2), oauth_token
        )
    elif 'crime type' in q or 'likely crime' in q or 'what crime' in q:
        return predict_crime_type(
            data.get('location_rowid', 43110000000034001), data.get('month', 7),
            data.get('year', 2026), data.get('hour_of_day', 22), data.get('day_of_week', 5),
            data.get('past_theft', 10), data.get('past_cybercrime', 3),
            data.get('past_assault', 4), oauth_token
        )
    elif 'sociological' in q or 'vulnerab' in q or 'demographic' in q:
        return predict_sociological_risk(
            data.get('age_group', 1), data.get('gender_encoded', 1),
            data.get('location_rowid', 43110000000034001), data.get('month', 7),
            data.get('crime_type_encoded', 0), data.get('victim_count', 3),
            data.get('offender_count', 2), oauth_token
        )
    else:
        return {"message": "No prediction available for this query type"}