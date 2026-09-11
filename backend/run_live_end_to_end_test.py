import sys
import json
import urllib.request
import urllib.parse
import urllib.error
import io
import uuid
import time
import os
import pymupdf

if sys.stdout.encoding != 'utf-8':
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')

BASE_URL = "http://127.0.0.1:8000/api/v1"

def api_call(method, endpoint, token=None, data=None, files=None):
    url = f"{BASE_URL}{endpoint}"
    headers = {}
    if token:
        headers["Authorization"] = f"Bearer {token}"
    
    body = None
    if files:
        boundary = f"----WebKitFormBoundary{uuid.uuid4().hex}"
        headers["Content-Type"] = f"multipart/form-data; boundary={boundary}"
        buffer = io.BytesIO()
        for field_name, (filename, file_bytes, content_type) in files.items():
            buffer.write(f"--{boundary}\r\n".encode())
            buffer.write(f'Content-Disposition: form-data; name="{field_name}"; filename="{filename}"\r\n'.encode())
            buffer.write(f"Content-Type: {content_type}\r\n\r\n".encode())
            buffer.write(file_bytes)
            buffer.write(b"\r\n")
        if data:
            for k, v in data.items():
                buffer.write(f"--{boundary}\r\n".encode())
                buffer.write(f'Content-Disposition: form-data; name="{k}"\r\n\r\n'.encode())
                buffer.write(str(v).encode())
                buffer.write(b"\r\n")
        buffer.write(f"--{boundary}--\r\n".encode())
        body = buffer.getvalue()
    elif data is not None:
        headers["Content-Type"] = "application/json"
        body = json.dumps(data).encode("utf-8")
        
    req = urllib.request.Request(url, data=body, headers=headers, method=method)
    try:
        with urllib.request.urlopen(req) as response:
            res_body = response.read().decode("utf-8")
            return response.status, json.loads(res_body) if res_body else {}
    except urllib.error.HTTPError as e:
        err_body = e.read().decode("utf-8")
        try:
            return e.code, json.loads(err_body)
        except Exception:
            return e.code, {"error": err_body}

def run_comprehensive_live_test():
    print("================================================================================")
    print("🚀 OWNIT COMPREHENSIVE LIVE SYSTEM & FEATURE VERIFICATION")
    print("================================================================================\n")
    
    unique_id = uuid.uuid4().hex[:6]
    test_username = f"live_tester_{unique_id}"
    test_password = "LiveSecurePassword123!"
    
    # -------------------------------------------------------------------------
    # 1. USER REGISTRATION & AUTHENTICATION
    # -------------------------------------------------------------------------
    print("👉 [1/19] User Signup & Login...")
    signup_payload = {
        "username": test_username,
        "password": test_password,
        "confirmPassword": test_password,
        "preferredLanguage": "en"
    }
    status, res = api_call("POST", "/auth/signup", data=signup_payload)
    assert status == 201, f"Signup failed: {res}"
    token = res["accessToken"]
    user_id = res["user"]["id"]
    print(f"   ✅ User registered successfully: ID={user_id}, Username='{test_username}'")
    
    # Verify /auth/me
    status, me_res = api_call("GET", "/auth/me", token=token)
    assert status == 200 and me_res["id"] == user_id
    print("   ✅ Auth session verified via /auth/me")
    
    # -------------------------------------------------------------------------
    # 2. PRODUCT CREATION VIA OCR SCANNER
    # -------------------------------------------------------------------------
    print("\n👉 [2/19] Product Ingestion via OCR Scanner...")
    # Create synthetic PDF invoice
    doc = pymupdf.open()
    page = doc.new_page(width=595, height=842)
    sample_text = (
        "RELIANCE DIGITAL RETAIL LTD\n"
        "Tax Invoice: INV-2025-8899\n"
        "Date: 2025-01-15\n\n"
        "1. Samsung 55 Inch 4K Smart TV UA55DU8000\n"
        "   Qty: 1   Price: 54,990.00\n"
        "   Serial: SAMSUNG-TV-LIVE99\n\n"
        "Warranty: 1 Year Manufacturer Warranty\n"
        "Total Amount: INR 54,990.00\n"
    )
    p = pymupdf.Point(50, 72)
    for line in sample_text.split("\n"):
        page.insert_text(p, line, fontsize=12, color=(0, 0, 0))
        p.y += 24
    pdf_bytes = doc.tobytes()
    
    # Call /ocr/scan
    status, scan_res = api_call(
        "POST",
        "/ocr/scan",
        token=token,
        files={"file": ("Reliance_Invoice.pdf", pdf_bytes, "application/pdf")}
    )
    assert status == 200, f"OCR scan failed: {scan_res}"
    temp_token = scan_res.get("tempFileToken")
    extracted_items = scan_res.get("items", [])
    assert len(extracted_items) >= 1, f"OCR did not extract items: {scan_res}"
    print(f"   ✅ OCR Scan extracted {len(extracted_items)} item(s). Temp Token: {temp_token}")
    
    # Confirm & Save Products from OCR
    confirm_payload = {
        "items": [
            {
                "name": "Samsung 55 Inch 4K Smart TV",
                "brand": "Samsung",
                "model": "UA55DU8000",
                "category": "TV",
                "purchaseDate": "2025-01-15",
                "price": 54990.0,
                "quantity": 1,
                "seller": "Reliance Digital",
                "serialNumber": "SAMSUNG-TV-LIVE99"
            }
        ],
        "tempFileToken": temp_token
    }
    status, save_ocr_res = api_call("POST", "/ocr/confirm", token=token, data=confirm_payload)
    assert status == 201 or status == 200, f"OCR confirm and save failed: {save_ocr_res}"
    ocr_product = save_ocr_res["createdProducts"][0]
    ocr_product_id = ocr_product["id"]
    print(f"   ✅ OCR Product saved to Vault: '{ocr_product['name']}' (ID: {ocr_product_id})")
    
    # -------------------------------------------------------------------------
    # 3. PRODUCT CREATION VIA MANUAL METHOD
    # -------------------------------------------------------------------------
    print("\n👉 [3/19] Product Creation via Manual Method...")
    manual_payload = {
        "name": "Apple MacBook Pro 16",
        "brand": "Apple",
        "model": "MK183HN/A",
        "category": "Laptop",
        "purchaseDate": "2025-03-01",
        "price": 239900.0,
        "quantity": 1,
        "seller": "Apple Store Mumbai",
        "serialNumber": "C02G1234MD6R",
        "returnDuration": "14 Days",
        "notes": "Work development laptop"
    }
    status, manual_res = api_call("POST", "/products/", token=token, data=manual_payload)
    assert status == 201 or status == 200, f"Manual creation failed: {manual_res}"
    manual_product_id = manual_res["id"]
    print(f"   ✅ Manual Product saved to Vault: '{manual_res['name']}' (ID: {manual_product_id})")
    
    # -------------------------------------------------------------------------
    # 4. VERIFYING DATABASE PERSISTENCE & VAULT LISTING
    # -------------------------------------------------------------------------
    print("\n👉 [4/19] Verifying MongoDB Persistence & Vault Listing...")
    status, products_res = api_call("GET", "/products/", token=token)
    assert status == 200
    assert len(products_res) == 2, f"Expected 2 products, found {len(products_res)}"
    p_ids = [p["id"] for p in products_res]
    assert ocr_product_id in p_ids and manual_product_id in p_ids
    print(f"   ✅ MongoDB confirmed 2 vaulted products for user: {[p['name'] for p in products_res]}")
    
    # -------------------------------------------------------------------------
    # 5. DOCUMENT UPLOAD & ATTACHMENT
    # -------------------------------------------------------------------------
    print("\n👉 [5/19] Document Upload & Attachment...")
    dummy_cert = b"%PDF-1.4\n1 0 obj<</Type/Catalog/Pages 2 0 R>>endobj\nxref\n0 2\ntrailer<</Size 2/Root 1 0 R>>\nstartxref\n50\n%%EOF"
    status, doc_res = api_call(
        "POST",
        "/documents/upload",
        token=token,
        data={"productId": ocr_product_id, "documentType": "Warranty Card"},
        files={"file": ("Samsung_Care_Plus.pdf", dummy_cert, "application/pdf")}
    )
    assert status == 201 or status == 200, f"Doc upload failed: {doc_res}"
    doc_id = doc_res["id"]
    print(f"   ✅ Document uploaded & attached: '{doc_res['originalFilename']}' (ID: {doc_id})")
    
    # -------------------------------------------------------------------------
    # 6. MULTI-TIER WARRANTIES & STATUS DETERMINATION
    # -------------------------------------------------------------------------
    print("\n👉 [6/19] Multi-Tier Warranty Registration & Status Computation...")
    # Add Comprehensive Warranty (1 Year -> Expiry calculated)
    w1_payload = {
        "productId": ocr_product_id,
        "type": "Comprehensive Warranty",
        "provider": "Samsung India",
        "duration": "12 Months",
        "startDate": "2025-01-15",
        "benefits": "Panel, motherboard, technician visit",
        "exclusions": "Physical crack, water ingress",
        "serviceInformation": "1800-40-SAMSUNG"
    }
    status, w1_res = api_call("POST", "/warranties/", token=token, data=w1_payload)
    assert status == 201 or status == 200
    w1_id = w1_res["id"]
    print(f"   ✅ Comprehensive Warranty added: Expiry={w1_res['expiryDate']}, Status={w1_res['status']}")
    
    # Add Panel Warranty (10 Years)
    w2_payload = {
        "productId": ocr_product_id,
        "type": "Panel Warranty",
        "provider": "Samsung Care+",
        "duration": "120 Months",
        "startDate": "2025-01-15",
        "benefits": "Display panel lines, dead pixels",
        "exclusions": "Physical impact",
        "serviceInformation": "1800-40-SAMSUNG"
    }
    status, w2_res = api_call("POST", "/warranties/", token=token, data=w2_payload)
    assert status == 201 or status == 200
    print(f"   ✅ Panel Warranty added: Expiry={w2_res['expiryDate']}, Status={w2_res['status']}")
    
    # Check Warranty Summary
    status, summary_res = api_call("GET", "/warranties/summary", token=token)
    assert status == 200 and summary_res["totalWarranties"] >= 2
    print(f"   ✅ Warranty Summary: Total={summary_res['totalWarranties']}, Active={summary_res['activeCount']}")
    
    # -------------------------------------------------------------------------
    # 7. MILESTONE NOTIFICATIONS & REMINDERS
    # -------------------------------------------------------------------------
    print("\n👉 [7/19] Milestone Notifications Evaluation...")
    status, notif_res = api_call("GET", "/notifications/", token=token)
    assert status == 200
    status, unread_res = api_call("GET", "/notifications/unread-count", token=token)
    assert status == 200
    print(f"   ✅ Notifications API verified. Current unread count: {unread_res.get('unreadCount', 0)}")
    
    # -------------------------------------------------------------------------
    # 8. LIFECYCLE TIMELINE
    # -------------------------------------------------------------------------
    print("\n👉 [8/19] Product Lifecycle Timeline...")
    status, timeline_res = api_call("GET", f"/products/{ocr_product_id}/timeline", token=token)
    assert status == 200
    events = timeline_res.get("events", [])
    assert len(events) >= 1
    event_titles = [e["title"] for e in events]
    print(f"   ✅ Lifecycle Timeline generated {len(events)} events: {event_titles}")
    
    # -------------------------------------------------------------------------
    # 9. PREVENTIVE MAINTENANCE & LOGGING
    # -------------------------------------------------------------------------
    print("\n👉 [9/19] Preventive Maintenance & Service Recommendations...")
    status, recs_res = api_call("GET", f"/maintenance/product/{ocr_product_id}/recommendations", token=token)
    assert status == 200
    recs = recs_res if isinstance(recs_res, list) else recs_res.get("recommendations", [])
    print(f"   ✅ Sourced Preventive Care Recommendations: {len(recs)} available")
    
    # Add maintenance task
    maint_payload = {
        "productId": ocr_product_id,
        "title": "Clean screen with microfiber & clear dust vents",
        "type": "Cleaning",
        "date": "2025-02-01",
        "status": "Completed",
        "notes": "No dust accumulation found"
    }
    status, maint_entry = api_call("POST", "/maintenance/", token=token, data=maint_payload)
    assert status == 201 or status == 200, f"Maintenance creation failed: {maint_entry}"
    print(f"   ✅ Maintenance task logged: '{maint_entry['title']}' (Status: {maint_entry['status']})")
    
    # -------------------------------------------------------------------------
    # 10. PRODUCT LIFE SCORE (0-100)
    # -------------------------------------------------------------------------
    print("\n👉 [10/19] Product Life Score Calculation...")
    status, score_res = api_call("GET", f"/products/{ocr_product_id}/life-score", token=token)
    assert status == 200
    print(f"   ✅ Product Life Score: {score_res['score']}/100 (Grade: {score_res['grade']})")
    print(f"      Positive Factors: {len(score_res.get('positiveReasons', []))}")
    print(f"      Penalty Factors: {len(score_res.get('penaltyReasons', []))}")
    
    # -------------------------------------------------------------------------
    # 11. PRODUCT AI ASSISTANT CHAT
    # -------------------------------------------------------------------------
    print("\n👉 [11/19] Product-Specific AI Assistant Conversation...")
    ai_query = {
        "productId": ocr_product_id,
        "message": "What is the serial number of my TV and is horizontal line defect covered under warranty?"
    }
    status, ai_res = api_call("POST", "/ai/chat", token=token, data=ai_query)
    assert status == 200, f"AI chat failed: {ai_res}"
    reply_text = ai_res["assistantMessage"]["content"]
    citations = ai_res["assistantMessage"].get("sourceReferences", [])
    print(f"   ✅ AI Assistant Reply: \"{reply_text[:120]}...\"")
    print(f"      Verified Citations: {len(citations)} source citation(s) attached.")
    
    # -------------------------------------------------------------------------
    # 12. WARRANTY INTELLIGENCE (PROBLEM COVERAGE ANALYSIS)
    # -------------------------------------------------------------------------
    print("\n👉 [12/19] Warranty Intelligence Issue Coverage Analysis...")
    intel_payload = {
        "productId": ocr_product_id,
        "issueDescription": "Green flickering lines appearing on display panel during normal video playback."
    }
    status, intel_res = api_call("POST", "/warranty-intelligence/analyze", token=token, data=intel_payload)
    assert status == 200
    print(f"   ✅ Coverage Assessment: {intel_res.get('coverageLikelihood')} - {intel_res.get('statusLabel')}")
    print(f"      Action Recommendation: {intel_res.get('recommendedAction')[:100]}...")
    
    # -------------------------------------------------------------------------
    # 13. CLAIM ASSISTANT (DOSSIER & DRAFT LETTER SYNTHESIS)
    # -------------------------------------------------------------------------
    print("\n👉 [13/19] Warranty Claim Assistant Dossier Preparation...")
    claim_payload = {
        "productId": ocr_product_id,
        "problemDescription": "Horizontal green lines flickering on the screen.",
        "problemStartDate": "2025-02-10",
        "incidentDetails": "TV wall-mounted, factory reset did not resolve issue."
    }
    status, claim_res = api_call("POST", "/claim-assistant/prepare", token=token, data=claim_payload)
    assert status == 200
    print(f"   ✅ Claim Dossier Prepared for '{claim_res['productName']}'")
    print(f"      Draft Support Letter Length: {len(claim_res['draftSupportMessage'])} characters")
    print(f"      Checklist Items: {len(claim_res['confirmationChecklist'])} confirmation steps")
    
    # -------------------------------------------------------------------------
    # 14. SERVICE HISTORY (REPAIR LOGGING)
    # -------------------------------------------------------------------------
    print("\n👉 [14/19] Service & Repair History Logging...")
    service_payload = {
        "productId": ocr_product_id,
        "serviceDate": "2025-02-15",
        "problem": "Loose HDMI Port 1",
        "serviceCenter": "Samsung Authorized Plaza",
        "workPerformed": "Replaced HDMI daughterboard connector",
        "cost": 0.0,
        "warrantyCovered": True,
        "notes": "RMA-99281 - Repaired free under warranty"
    }
    status, s_res = api_call("POST", "/services/", token=token, data=service_payload)
    assert status == 201 or status == 200, f"Service history creation failed: {s_res}"
    print(f"   ✅ Service Record created: '{s_res['problem']}' at {s_res['serviceCenter']} (Covered: {s_res['warrantyCovered']})")
    
    # -------------------------------------------------------------------------
    # 15. COMPATIBLE ACCESSORY RECOMMENDATIONS
    # -------------------------------------------------------------------------
    print("\n👉 [15/19] Compatible Accessory Finder...")
    status, acc_res = api_call(
        "GET",
        f"/accessories/recommendations?productId={ocr_product_id}&minBudget=1000&maxBudget=10000",
        token=token
    )
    assert status == 200
    acc_list = acc_res.get("recommendations", [])
    assert len(acc_list) > 0
    print(f"   ✅ Accessory Finder returned {len(acc_list)} recommendations within budget ₹1,000-₹10,000:")
    for acc in acc_list[:3]:
        print(f"      - {acc['name']} ({acc['category']}) | ₹{acc['price']:,.2f} | Status: {acc['compatibilityStatus']}")
        
    # -------------------------------------------------------------------------
    # 16. SAFETY & RECALL ALERT SCANNING
    # -------------------------------------------------------------------------
    print("\n👉 [16/19] Safety & Recall Bulletins Scanning...")
    status, recall_res = api_call("GET", f"/safety-recalls/check/{manual_product_id}", token=token)
    assert status == 200
    print(f"   ✅ Safety Recall Check on MacBook Pro: Possible Recall={recall_res.get('hasPossibleRecall')}")
    status, vault_recalls = api_call("GET", "/safety-recalls/vault-scan", token=token)
    assert status == 200
    print(f"   ✅ Vault-Wide Safety Scan: {vault_recalls.get('totalScanned')} products scanned.")
    
    # -------------------------------------------------------------------------
    # 17. MULTILINGUAL PREFERENCES TOGGLE
    # -------------------------------------------------------------------------
    print("\n👉 [17/19] Multilingual Preferences Toggle...")
    status, pref_res = api_call("PATCH", "/auth/preferences", token=token, data={"preferredLanguage": "hi"})
    assert status == 200 and pref_res["preferredLanguage"] == "hi"
    print("   ✅ Language updated to Hindi ('hi')")
    status, pref_res = api_call("PATCH", "/auth/preferences", token=token, data={"preferredLanguage": "en"})
    assert status == 200 and pref_res["preferredLanguage"] == "en"
    print("   ✅ Language restored to English ('en')")
    
    # -------------------------------------------------------------------------
    # 18. SEARCH & FILTERING IN PRODUCT VAULT
    # -------------------------------------------------------------------------
    print("\n👉 [18/19] Product Vault Search & Filters...")
    status, search_tv = api_call("GET", "/products/?search=Samsung", token=token)
    assert status == 200 and len(search_tv) == 1 and search_tv[0]["brand"] == "Samsung", f"Search failed: {search_tv}"
    print(f"   ✅ Search query 'search=Samsung' matched: '{search_tv[0]['name']}'")
    status, filter_laptop = api_call("GET", "/products/?category=Laptop", token=token)
    assert status == 200 and len(filter_laptop) == 1 and filter_laptop[0]["category"] == "Laptop", f"Filter failed: {filter_laptop}"
    print(f"   ✅ Category filter 'Laptop' matched: '{filter_laptop[0]['name']}'")
    
    # -------------------------------------------------------------------------
    # 19. PRODUCT DELETION & CASCADING CLEANUP
    # -------------------------------------------------------------------------
    print("\n👉 [19/19] Product Deletion & Cascading Cleanup...")
    # Delete OCR Product
    status, del_res1 = api_call("DELETE", f"/products/{ocr_product_id}", token=token)
    assert status == 200
    print(f"   ✅ Deleted OCR product: ID {ocr_product_id}")
    
    # Delete Manual Product
    status, del_res2 = api_call("DELETE", f"/products/{manual_product_id}", token=token)
    assert status == 200
    print(f"   ✅ Deleted Manual product: ID {manual_product_id}")
    
    # Verify Vault is empty for this test user
    status, final_products = api_call("GET", "/products/", token=token)
    assert status == 200 and len(final_products) == 0
    print("   ✅ Verified vault is completely empty after deletion.")
    
    # Verify Warranties are cleaned up
    status, final_w = api_call("GET", "/warranties/", token=token)
    assert status == 200 and len(final_w) == 0
    print("   ✅ Verified associated warranties were cascaded and deleted.")
    
    print("\n================================================================================")
    print("🎉 ALL 19 COMPREHENSIVE LIVE FEATURE CHECKS PASSED WITH 0 ERRORS!")
    print("================================================================================")

if __name__ == "__main__":
    run_comprehensive_live_test()
