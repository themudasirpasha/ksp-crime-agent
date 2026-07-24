import json
import urllib.request
import urllib.error
from datetime import datetime, timedelta

# ============================================================
# KSP CrimeAI — Token Manager
# Two separate tokens: Data Store (own account) + ML (friend's account)
# ============================================================

# ---- DATA STORE (your own account) ----
DS_CLIENT_ID = "1000.7Z4TEPKFGHSGWE9IMBNN4JPCDL67VE"
DS_CLIENT_SECRET = "7dea0f281476ea96a47ca3b4fc3ffab4da84438148"
DS_REFRESH_TOKEN = "1000.b212ceb84be848934d20c1c4703409bc.03dab7e31245b932c7fea9ed5413d1c9"

# ---- ML MODELS (friend's account) ----
ML_CLIENT_ID = "1000.9KID9D77BQRTI5GO1A3BMFMRDQMK7A"
ML_CLIENT_SECRET = "93a9ac517c861850e79238b103a6b56e6b81937511"
ML_REFRESH_TOKEN = "1000.76cacb250cdcbe95f56d6d9dfd04e83f.c617255e73c3a61bfeeca5a2569e3ceb"

_ds_token_cache = {"access_token": None, "expires_at": None}
_ml_token_cache = {"access_token": None, "expires_at": None}


def _refresh(client_id, client_secret, refresh_token, cache):
    if cache["access_token"] and cache["expires_at"] and datetime.now() < cache["expires_at"]:
        return cache["access_token"]
    try:
        url = f"https://accounts.zoho.in/oauth/v2/token?refresh_token={refresh_token}&client_id={client_id}&client_secret={client_secret}&grant_type=refresh_token"
        req = urllib.request.Request(url, method="POST")
        with urllib.request.urlopen(req) as response:
            data = json.loads(response.read().decode("utf-8"))
            access_token = data.get("access_token")
            if access_token:
                cache["access_token"] = access_token
                cache["expires_at"] = datetime.now() + timedelta(minutes=55)
                print(f"Token refreshed at {datetime.now()}")
                return access_token
            print(f"Token refresh failed: {data}")
            return None
    except Exception as e:
        print(f"Token refresh error: {str(e)}")
        return None


def get_fresh_token():
    """Data Store token — your own account"""
    return _refresh(DS_CLIENT_ID, DS_CLIENT_SECRET, DS_REFRESH_TOKEN, _ds_token_cache)


def get_fresh_ml_token():
    """ML Models token — friend's account"""
    return _refresh(ML_CLIENT_ID, ML_CLIENT_SECRET, ML_REFRESH_TOKEN, _ml_token_cache)