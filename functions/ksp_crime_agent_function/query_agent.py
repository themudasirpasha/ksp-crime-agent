import json
import zcatalyst_sdk
from datetime import datetime
import urllib.request
import urllib.error
from token_manager import get_fresh_token

# ============================================================
# KSP CrimeAI — Query Agent
# Fetches data from Catalyst Data Store using ZCQL 
# ============================================================

ZCQL_URL = "https://api.catalyst.zoho.in/baas/v1/project/43110000000018001/search"

def execute_zcql(query, token=None):
    try:
        if not token:
            token = get_fresh_token()

        url = "https://api.catalyst.zoho.in/baas/v1/project/43110000000018001/query"
        headers = {
            "Authorization": f"Zoho-oauthtoken {token}",
            "Content-Type": "application/json",
            "CATALYST-ORG": "60072886153",
            "Environment": "Development"
        }
        payload = json.dumps({"query": query}).encode("utf-8")
        print(f"Executing query: {query}")
        req = urllib.request.Request(url, data=payload, headers=headers, method="POST")
        with urllib.request.urlopen(req) as response:
            result = json.loads(response.read().decode("utf-8"))
            print(f"ZCQL Result: {result}")
            return result
    except urllib.error.HTTPError as e:
        error_body = e.read().decode("utf-8")
        print(f"ZCQL Error {e.code}: {error_body}")
        return {"error": f"HTTP {e.code}", "details": error_body}
    except Exception as e:
        print(f"ZCQL Exception: {str(e)}")
        return {"error": str(e)}


def get_fir_by_id(crime_id, token):
    """Get FIR details by crime_id"""
    query = f"SELECT * FROM crime_incidents WHERE crime_id = '{crime_id}'"
    return execute_zcql(query, token)


def get_offender_by_name(name, token):
    """Get offender details by name (Catalyst ZCQL uses * as wildcard, not %)"""
    query = f"SELECT * FROM offenders WHERE name LIKE '*{name}*' LIMIT 10"
    return execute_zcql(query, token)


def get_offender_history(offender_id, token):
    """Get complete crime history of an offender"""
    query = f"SELECT * FROM offenders WHERE offender_id = '{offender_id}'"
    return execute_zcql(query, token)


def get_victims_by_crime(crime_id, token):
    """Get all victims of a specific crime"""
    query = f"SELECT * FROM victims WHERE crime_id = '{crime_id}'"
    return execute_zcql(query, token)


def get_recent_crimes(limit, token):
    """Get most recent crimes"""
    query = f"SELECT * FROM crime_incidents ORDER BY crime_date DESC LIMIT {limit}"
    return execute_zcql(query, token)


def get_crimes_by_type(crime_type, token):
    """Get crimes by type"""
    query = f"SELECT * FROM crime_incidents WHERE crime_type = '{crime_type}' LIMIT 20"
    return execute_zcql(query, token)


def get_crimes_by_district(district, token):
    """Get all crimes in a given district (via locations join-less lookup)"""
    query = f"""SELECT crime_incidents.crime_id, crime_incidents.crime_type,
                crime_incidents.crime_date, crime_incidents.status,
                locations.district, locations.region
                FROM crime_incidents, locations
                WHERE crime_incidents.location_id = locations.location_id
                AND locations.district = '{district}'
                LIMIT 20"""
    return execute_zcql(query, token)


def get_financial_transactions_by_crime(crime_id, token):
    """Get financial transactions linked to a crime"""
    query = f"SELECT * FROM financial_transactions WHERE crime_id = '{crime_id}'"
    return execute_zcql(query, token)


def get_investigation_status(crime_id, token):
    """Get investigation status of a case"""
    query = f"SELECT * FROM investigations WHERE crime_id = '{crime_id}'"
    return execute_zcql(query, token)

def get_criminal_network(offender_id, token):
    """Get criminal network - offenders sharing same crime locations"""
    all_rows = []
    offset = 0
    page_size = 300

    while True:
        query = f"SELECT offender_id, name, crime_id FROM offenders LIMIT {page_size} OFFSET {offset}"
        result = execute_zcql(query, token)
        rows = result.get("data", [])
        if not rows:
            break
        all_rows.extend(rows)
        offset += page_size
        if len(rows) < page_size:
            break

    # Group offenders by crime_id
    crime_map = {}
    for r in all_rows:
        o = r.get("offenders", r)
        cid = o.get("crime_id")
        if cid:
            crime_map.setdefault(cid, []).append(o)

    # Build network: pairs of offenders sharing a crime
    network = []
    for cid, offenders in crime_map.items():
        if len(offenders) > 1:
            for i in range(len(offenders)):
                for j in range(len(offenders)):
                    if i != j:
                        network.append({
                            "offender_1_id": offenders[i].get("offender_id"),
                            "offender_1_name": offenders[i].get("name"),
                            "offender_2_id": offenders[j].get("offender_id"),
                            "offender_2_name": offenders[j].get("name"),
                            "crime_id": cid
                        })

    if offender_id:
        network = [n for n in network if n["offender_1_id"] == offender_id or n["offender_2_id"] == offender_id]

    return {"status": "success", "data": network[:20]}

def build_offender_features(name_or_id, token):
    """Fetch offender's real crime history from Data Store and compute ML features"""
    if not token:
        token = get_fresh_token()

    # Step 1: find offender rows by name or offender_id
    # NOTE: Catalyst ZCQL uses '*' as the wildcard character, not '%'
    query = f"SELECT * FROM offenders WHERE name LIKE '*{name_or_id}*' OR offender_id = '{name_or_id}' LIMIT 50"
    off_result = execute_zcql(query, token)

    rows = off_result.get("data", [])
    if not rows:
        return {"error": f"No offender found matching '{name_or_id}'"}

    first = rows[0].get("offenders", rows[0])
    offender_rowid = first.get("ROWID")
    offender_name = first.get("name")

    # Step 2: collect all crime_ids linked to this offender
    crime_ids = list({r.get("offenders", r).get("crime_id") for r in rows if r.get("offenders", r).get("crime_id")})

    if not crime_ids:
        return {"error": "No linked crimes found for this offender"}

    crime_id_list = "', '".join(crime_ids)
    crime_query = f"SELECT crime_id, crime_type, crime_date, location_id FROM crime_incidents WHERE crime_id IN ('{crime_id_list}')"
    crime_result = execute_zcql(crime_query, token)
    crime_rows = crime_result.get("data", [])

    if not crime_rows:
        return {"error": "Could not fetch linked crime details"}

    crime_types = set()
    locations = set()
    dates = []

    for r in crime_rows:
        c = r.get("crime_incidents", r)
        if c.get("crime_type"):
            crime_types.add(c.get("crime_type"))
        if c.get("location_id"):
            locations.add(c.get("location_id"))
        if c.get("crime_date"):
            dates.append(c.get("crime_date"))

    dates.sort()
    total_crimes = len(crime_rows)
    years_active = 0
    avg_gap_days = 0

    if len(dates) >= 2:
        d0 = datetime.strptime(dates[0], "%Y-%m-%d")
        d1 = datetime.strptime(dates[-1], "%Y-%m-%d")
        years_active = max(1, (d1 - d0).days // 365)
        avg_gap_days = (d1 - d0).days // max(1, len(dates) - 1)

    return {
        "offender_name": offender_name,
        "offender_rowid": int(offender_rowid) if offender_rowid else 0,
        "total_crimes": total_crimes,
        "crime_types_count": len(crime_types),
        "years_active": years_active,
        "repeat_offense_count": max(0, total_crimes - 1),
        "avg_crime_gap_days": avg_gap_days,
        "unique_locations": len(locations)
    }


def handle_query(intent, query, token):
    """Main query handler - routes to correct ZCQL function"""

    query_lower = query.lower()

    if intent == 'fir':
        # Extract crime ID if mentioned
        words = query.split()
        for word in words:
            if word.startswith('KA-'):
                return get_fir_by_id(word, token)
        return get_recent_crimes(10, token)

    elif intent == 'offender':
        # Extract name from query
        return get_offender_by_name(query, token)

    elif intent == 'victim':
        words = query.split()
        for word in words:
            if word.startswith('KA-'):
                return get_victims_by_crime(word, token)
        return {"message": "Please provide a crime ID to get victim details"}

    elif intent == 'location':
        districts = ['bengaluru', 'mysuru', 'hubli', 'mangaluru', 'belagavi',
                     'kalaburagi', 'davangere', 'ballari', 'tumakuru', 'shivamogga']
        for district in districts:
            if district in query_lower:
                return get_crimes_by_district(district.capitalize(), token)
        return get_recent_crimes(10, token)

    elif intent == 'network':
        words = query.split()
        for word in words:
            if word.startswith('OFF-'):
                return get_criminal_network(word, token)
        return get_criminal_network(None, token)

    elif intent == 'financial':
        words = query.split()
        for word in words:
            if word.startswith('KA-'):
                return get_financial_transactions_by_crime(word, token)
        return {"message": "Please provide a crime ID to get financial transactions"}

    elif intent == 'summary':
        words = query.split()
        for word in words:
            if word.startswith('KA-'):
                crime = get_fir_by_id(word, token)
                victims = get_victims_by_crime(word, token)
                investigation = get_investigation_status(word, token)
                return {
                    "crime": crime,
                    "victims": victims,
                    "investigation": investigation
                }
        return get_recent_crimes(5, token)

    else:
        return get_recent_crimes(10, token)


def get_hotspot_data(crime_type, token):
    """Get crime count per location for hotspot map"""
    if not token:
        token = get_fresh_token()

    if crime_type == 'all':
        query = "SELECT crime_incidents.location_id, crime_incidents.crime_type, locations.region, locations.district, locations.geo_coordinates FROM crime_incidents, locations WHERE crime_incidents.location_id = locations.location_id LIMIT 2000"
    else:
        query = f"SELECT crime_incidents.location_id, crime_incidents.crime_type, locations.region, locations.district, locations.geo_coordinates FROM crime_incidents, locations WHERE crime_incidents.location_id = locations.location_id AND crime_incidents.crime_type = '{crime_type}' LIMIT 2000"

    return execute_zcql(query, token)
