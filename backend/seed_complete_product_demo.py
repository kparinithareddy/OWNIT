import os
import json
import urllib.request
import urllib.error
from datetime import datetime, timezone, timedelta

BASE_URL = "http://127.0.0.1:8000/api/v1"

def api_call(method, endpoint, token=None, data=None, files=None):
    url = f"{BASE_URL}{endpoint}"
    headers = {}
    if token:
        headers["Authorization"] = f"Bearer {token}"
    
    req_data = None
    if files:
        boundary = "----WebKitFormBoundary7MA4YWxkTrZu0gW"
        body = []
        for field, (fname, fcontent, ctype) in files.items():
            body.append(f"--{boundary}".encode())
            body.append(f'Content-Disposition: form-data; name="{field}"; filename="{fname}"'.encode())
            body.append(f"Content-Type: {ctype}".encode())
            body.append(b"")
            body.append(fcontent if isinstance(fcontent, bytes) else fcontent.encode())
        
        if data:
            for k, v in data.items():
                body.append(f"--{boundary}".encode())
                body.append(f'Content-Disposition: form-data; name="{k}"'.encode())
                body.append(b"")
                body.append(str(v).encode())
        
        body.append(f"--{boundary}--".encode())
        body.append(b"")
        req_data = b"\r\n".join(body)
        headers["Content-Type"] = f"multipart/form-data; boundary={boundary}"
    elif data is not None:
        req_data = json.dumps(data).encode("utf-8")
        headers["Content-Type"] = "application/json"

    req = urllib.request.Request(url, data=req_data, headers=headers, method=method)
    try:
        with urllib.request.urlopen(req) as response:
            resp_body = response.read().decode("utf-8")
            return response.status, json.loads(resp_body) if resp_body else {}
    except urllib.error.HTTPError as e:
        resp_body = e.read().decode("utf-8")
        try:
            return e.code, json.loads(resp_body)
        except Exception:
            return e.code, {"error": resp_body}
    except Exception as exc:
        return 500, {"error": str(exc)}

def seed_and_test_product():
    print("=" * 80)
    print("?? SEEDING COMPLETE PRODUCT WITH ALL FEATURES IN OWNIT")
    print("=" * 80)

    username = "demo_user"
    password = "Password123!"
    
    status, res = api_call("POST", "/auth/login", data={"username": username, "password": password})
    if status != 200:
        status, res = api_call("POST", "/auth/signup", data={
            "username": username,
            "password": password,
            "confirmPassword": password,
            "email": "demo@ownit.local",
            "fullName": "Parinitha Reddy"
        })
        assert status in [200, 201], f"Signup failed: {res}"
        token = res["accessToken"]
    else:
        token = res["accessToken"]

    print(f"?? [1/12] Authenticated user '{username}' (Token acquired).")

    today = datetime.now(timezone.utc).date()
    purchase_date = (today - timedelta(days=45)).isoformat()
    product_payload = {
        "name": "Sony Bravia XR 65 Inch 4K OLED Smart Google TV",
        "brand": "Sony",
        "model": "XR-65A80L",
        "category": "TV",
        "purchaseDate": purchase_date,
        "price": 189990.00,
        "quantity": 1,
        "seller": "Croma Electronics",
        "serialNumber": "SONY-OLED-65A80L-88219",
        "imei": None,
        "notes": "Premium OLED TV with Cognitive Processor XR & Acoustic Surface Audio+.",
        "returnDuration": "15 Days",
        "returnStartDate": purchase_date,
        "returnPolicySource": "verified_store_policy"
    }

    status, prod_res = api_call("POST", "/products/", token=token, data=product_payload)
    assert status in [200, 201], f"Product creation failed: {prod_res}"
    product_id = prod_res["id"]
    print(f"?? [2/12] Product Created in Vault: '{prod_res['name']}' (ID: {product_id})")

    pdf_content = b"%PDF-1.4\n%Demo Invoice Document for Sony Bravia XR 65 OLED TV\n%%EOF"
    status, doc_res = api_call("POST", "/documents/upload", token=token, data={
        "productId": product_id,
        "documentType": "Purchase Bill",
        "notes": "Original Croma Electronics Tax Invoice & Receipt"
    }, files={
        "file": ("Sony_Bravia_Invoice.pdf", pdf_content, "application/pdf")
    })
    assert status in [200, 201], f"Document upload failed: {doc_res}"
    doc_name = doc_res.get("filename") or doc_res.get("fileName") or "Sony_Bravia_Invoice.pdf"
    print(f"?? [3/12] Invoice Document Uploaded: '{doc_name}' (ID: {doc_res['id']})")

    w1_expiry = (today + timedelta(days=320)).isoformat()
    status, w1_res = api_call("POST", "/warranties/", token=token, data={
        "productId": product_id,
        "warrantyType": "Comprehensive",
        "provider": "Sony India Care",
        "startDate": purchase_date,
        "expiryDate": w1_expiry,
        "durationMonths": 12,
        "coverageDetails": "Full device warranty including parts, labor, motherboards and audio system.",
        "supportPhone": "1800-103-7799",
        "supportEmail": "support@sony.co.in",
        "supportUrl": "https://www.sony.co.in/electronics/support"
    })
    assert status in [200, 201], f"Warranty 1 failed: {w1_res}"

    w2_expiry = (today + timedelta(days=1050)).isoformat()
    status, w2_res = api_call("POST", "/warranties/", token=token, data={
        "productId": product_id,
        "warrantyType": "Component",
        "provider": "Sony Extended Panel Protection",
        "startDate": purchase_date,
        "expiryDate": w2_expiry,
        "durationMonths": 36,
        "coverageDetails": "OLED display panel burn-in, dead sub-pixels, and power board coverage.",
        "supportPhone": "1800-103-7799",
        "supportEmail": "support@sony.co.in",
        "supportUrl": "https://www.sony.co.in/electronics/support"
    })
    assert status in [200, 201], f"Warranty 2 failed: {w2_res}"
    print(f"?? [4/12] Multi-Tier Warranties Configured: Comprehensive (1Y) & OLED Panel (3Y).")

    m_date = (today - timedelta(days=10)).isoformat()
    next_m_date = (today + timedelta(days=80)).isoformat()
    status, m_res = api_call("POST", "/maintenance/", token=token, data={
        "productId": product_id,
        "title": "OLED Panel Pixel Refresher & Clean Air Vents",
        "description": "Routine display maintenance and dust clearance.",
        "date": m_date,
        "type": "Cleaning",
        "nextDueDate": next_m_date,
        "status": "Completed",
        "notes": "Cleaned display screen with optical microfiber cloth and ran manual pixel refresher cycle."
    })
    assert status in [200, 201], f"Maintenance task failed: {m_res}"
    print(f"?? [5/12] Preventive Maintenance Task Recorded: '{m_res['title']}'")

    status, s_res = api_call("POST", "/services/", token=token, data={
        "productId": product_id,
        "serviceCenter": "Sony Authorized Service Center - Banjara Hills",
        "serviceDate": purchase_date,
        "cost": 0.0,
        "warrantyCovered": True,
        "problem": "Initial Table-Top Installation & Acoustic Audio Calibration",
        "workPerformed": "Wall-mounted TV, calibrated Acoustic Surface Audio+ soundstage, connected ARC sound system.",
        "notes": "Complimentary first-time authorized technician setup. RMA: SONY-SRV-2025-09941"
    })
    assert status in [200, 201], f"Service history failed: {s_res}"
    print(f"?? [6/12] Authorized Service Record Added: '{s_res['problem']}'")

    status, timeline = api_call("GET", f"/products/{product_id}/timeline", token=token)
    assert status == 200, f"Timeline failed: {timeline}"
    print(f"?? [7/12] Lifecycle Timeline Generated ({len(timeline)} chronological milestones).")

    status, score_data = api_call("GET", f"/products/{product_id}/life-score", token=token)
    assert status == 200, f"Life score failed: {score_data}"
    print(f"?? [8/12] Product Life Score: {score_data['score']}/100 (Grade: {score_data['grade']})")

    chat_prompt = "What is the serial number of this TV, and what does the OLED panel warranty cover?"
    status, chat_res = api_call("POST", "/ai/chat", token=token, data={
        "productId": product_id,
        "message": chat_prompt
    })
    assert status == 200, f"AI chat failed: {chat_res}"
    print(f"?? [9/12] AI Assistant Responded to product question.")

    status, wi_res = api_call("POST", "/warranty-intelligence/analyze", token=token, data={
        "productId": product_id,
        "issueDescription": "Display panel shows vertical red line down the middle of the screen"
    })
    assert status == 200, f"Warranty Intelligence failed: {wi_res}"
    print(f"?? [10/12] Warranty Intelligence Coverage: {wi_res.get('assessment')}")

    status, claim_res = api_call("POST", "/claim-assistant/prepare", token=token, data={
        "productId": product_id,
        "problemDescription": "Vertical line on screen panel",
        "incidentDetails": "Attempted pixel refresher and restarting device."
    })
    assert status == 200, f"Claim Assistant failed: {claim_res}"
    print(f"?? [11/12] Claim Dossier Prepared (Draft support letter generated with {len(claim_res.get('checklist', []))} checklist items).")

    status, acc_res = api_call("GET", f"/accessories/recommendations?productId={product_id}&budgetMin=1000&budgetMax=25000", token=token)
    assert status == 200, f"Accessories failed: {acc_res}"
    status, recall_res = api_call("GET", f"/safety-recalls/check/{product_id}", token=token)
    assert status == 200, f"Recall check failed: {recall_res}"
    print(f"?? [12/12] Sourced {len(acc_res.get('items', []))} compatible accessories; Safety recall status: '{recall_res.get('status')}'.")

    print("\n" + "=" * 80)
    print("?? SUCCESS! Product fully seeded and every feature verified in OWNIT database!")
    print(f"?? User Login Credentials:")
    print(f"   Username: {username}")
    print(f"   Password: {password}")
    print(f"   Product ID: {product_id}")
    print("=" * 80)

if __name__ == "__main__":
    seed_and_test_product()
