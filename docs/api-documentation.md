# OWNIT - REST API Reference Documentation

> **Base URL**: `http://localhost:8000/api/v1`  
> **Interactive Swagger UI**: `http://localhost:8000/docs`  
> **ReDoc Specification**: `http://localhost:8000/redoc`  
> **Auth Scheme**: HTTP Bearer Token (`Authorization: Bearer <JWT_ACCESS_TOKEN>`)

---

## 1. Global API Standards

### 1.1 Response Envelope & Status Codes
- `200 OK`: Successful synchronous request.
- `201 Created`: Resource successfully created.
- `400 Bad Request / 422 Unprocessable Entity`: Schema or business logic validation failure.
- `401 Unauthorized`: Missing, expired, or invalid JWT Bearer token.
- `404 Not Found`: Resource does not exist or user does not have ownership permission.
- `409 Conflict`: Unique constraint collision (e.g., username already taken).
- `500 Internal Server Error`: Unhandled server exception.
- `503 Service Unavailable`: MongoDB or critical engine offline.

### 1.2 Standardized Error Model
All error responses adhere to the unified `AppException` payload:
```json
{
  "success": false,
  "error": {
    "code": "VALIDATION_ERROR",
    "message": "File format '.exe' is not supported. Allowed formats: .pdf, .jpg, .jpeg, .png, .webp",
    "details": {
      "allowedExtensions": [".pdf", ".jpg", ".jpeg", ".png", ".webp"]
    }
  }
}
```

---

## 2. API Endpoints Catalog

### 2.1 Authentication & Profile (`/api/v1/auth`)

#### `POST /api/v1/auth/signup`
Registers a new user account.
- **Request Body**:
  ```json
  {
    "username": "kparinitha",
    "password": "SecurePassword123!",
    "confirmPassword": "SecurePassword123!",
    "preferredLanguage": "en"
  }
  ```
- **Response `201 Created`**:
  ```json
  {
    "accessToken": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
    "tokenType": "bearer",
    "user": {
      "id": "66dbb01234abcd5678ef9012",
      "username": "kparinitha",
      "preferredLanguage": "en",
      "createdAt": "2026-09-10T08:00:00Z",
      "updatedAt": "2026-09-10T08:00:00Z"
    }
  }
  ```

#### `POST /api/v1/auth/login`
Authenticates existing credentials and issues a JWT token.
- **Request Body**:
  ```json
  {
    "username": "kparinitha",
    "password": "SecurePassword123!"
  }
  ```
- **Response `200 OK`**: Same schema as signup `TokenResponse`.

#### `GET /api/v1/auth/me` *(Protected)*
Fetches current authenticated user profile.
- **Headers**: `Authorization: Bearer <TOKEN>`
- **Response `200 OK`**: `UserResponse` object.

#### `PATCH /api/v1/auth/preferences` *(Protected)*
Updates preferred language (`en`, `hi`, `te`).
- **Request Body**: `{"preferredLanguage": "hi"}`
- **Response `200 OK`**: Updated `UserResponse`.

---

### 2.2 Products Management (`/api/v1/products`)

#### `GET /api/v1/products` *(Protected)*
Lists all products belonging to the authenticated user with optional search & filters.
- **Query Parameters**:
  - `q`: Search string (searches name, brand, model, serial number)
  - `category`: Category filter
  - `brand`: Brand filter
  - `warranty_status`: `Active`, `Expiring Soon`, `Expired`
  - `return_status`: `Active`, `Ending Soon`, `Expired`
  - `maintenance_status`: `Overdue`, `Up to Date`
  - `sort_by`: `purchaseDate`, `createdAt`, `name`, `price`, `returnDeadline`
  - `order`: `asc` or `desc`
- **Response `200 OK`**: `List[ProductResponse]`

#### `POST /api/v1/products` *(Protected)*
Registers a new product manually into the vault.
- **Request Body**:
  ```json
  {
    "name": "Samsung 55 Inch 4K Smart TV",
    "brand": "Samsung",
    "model": "UA55DU8000",
    "category": "TV",
    "purchaseDate": "2025-01-15",
    "price": 54990.0,
    "quantity": 1,
    "seller": "Reliance Digital",
    "serialNumber": "SAMSUNG-TV-991823",
    "returnDuration": "7 Days",
    "notes": "Living room TV"
  }
  ```
- **Response `201 Created`**: `ProductResponse`

#### `GET /api/v1/products/{id}` *(Protected)*
Fetches complete product record by ID.

#### `PUT /api/v1/products/{id}` *(Protected)*
Updates an existing product record.

#### `DELETE /api/v1/products/{id}` *(Protected)*
Deletes a product and its associated warranties, documents, maintenance, and service records.

---

### 2.3 Warranties (`/api/v1/warranties`)

#### `GET /api/v1/warranties` *(Protected)*
Lists all user warranties with computed real-time status.
- **Query Parameters**: `product_id` (optional), `status` (`Active`, `Expiring Soon`, `Expired`)

#### `GET /api/v1/warranties/summary` *(Protected)*
Returns aggregate count metrics for dashboard cards (`totalWarranties`, `activeCount`, `expiringSoonCount`, `expiredCount`, `expiringSoonItems`).

#### `POST /api/v1/warranties` *(Protected)*
Adds a warranty component to a product.
- **Request Body**:
  ```json
  {
    "productId": "66dbb01234abcd5678ef9012",
    "type": "Comprehensive Warranty",
    "provider": "Samsung India",
    "duration": "12 Months",
    "startDate": "2025-01-15",
    "benefits": "Panel Coverage, Mainboard Replacement, Technician Visit",
    "exclusions": "Physical impact, liquid spill",
    "serviceInformation": "1800-40-SAMSUNG"
  }
  ```

---

### 2.4 OCR & Receipt Scanning (`/api/v1/ocr`)

#### `POST /api/v1/ocr/scan` *(Protected)*
Processes an uploaded bill/invoice image or PDF.
- **Form Data**: `file` (Binary upload)
- **Response `200 OK`**:
  ```json
  {
    "detectedSeller": "Reliance Digital",
    "detectedDate": "2025-01-15",
    "detectedInvoiceNumber": "INV-2025-00918",
    "detectedWarrantyDuration": "1 Year",
    "extractedItems": [
      {
        "name": "Samsung 55 Inch 4K Smart TV",
        "brand": "Samsung",
        "model": "UA55DU8000",
        "category": "TV",
        "price": 54990.0,
        "quantity": 1,
        "serialNumber": "SAMSUNG-TV-991823"
      }
    ],
    "tempFileToken": "tmp_9a8f7c6e5d4b3a2"
  }
  ```

#### `POST /api/v1/ocr/confirm-and-save` *(Protected)*
Batch creates confirmed products and attaches the permanent document.
- **Request Body**: `OCRConfirmRequest` containing reviewed `items` and `tempFileToken`.

---

### 2.5 AI Assistant & Chat (`/api/v1/ai`)

#### `POST /api/v1/ai/chat` *(Protected)*
Interactive contextual conversation anchored to a product.
- **Request Body**:
  ```json
  {
    "productId": "66dbb01234abcd5678ef9012",
    "message": "Is horizontal line distortion covered under warranty?",
    "language": "en"
  }
  ```
- **Response `200 OK`**:
  ```json
  {
    "reply": "Based on your uploaded Samsung Comprehensive and Panel Warranty documents, horizontal line distortion without external physical impact is typically covered under your active Display Panel Warranty.",
    "sourceReferences": [
      {
        "tier": 1,
        "title": "Samsung_TV_Warranty.pdf",
        "citation": "Tier 1: User Uploaded Warranty Document",
        "isVerified": true
      }
    ],
    "language": "en"
  }
  ```

#### `GET /api/v1/ai/health`
Checks whether Ollama is running and reports model status.

---

### 2.6 Warranty Intelligence & Claims (`/api/v1/warranty-intelligence` & `/api/v1/claim-assistant`)

#### `POST /api/v1/warranty-intelligence/analyze` *(Protected)*
Evaluates issue coverage likelihood across 4 tiers (`confirmed_coverage`, `likely_coverage`, `unclear_coverage`, `excluded_issue`).

#### `POST /api/v1/claim-assistant/prepare-claim` *(Protected)*
Synthesizes a complete claim preparation dossier with provenance tags and editable draft email.

---

### 2.7 Lifecycle Timeline, Maintenance, Life Score, Accessories, Recalls

| Endpoint | Method | Description |
|:---|:---:|:---|
| `/api/v1/products/{id}/timeline` | `GET` | Chronological lifecycle timeline events |
| `/api/v1/products/{id}/life-score` | `GET` | 0–100 Product Life Score breakdown |
| `/api/v1/maintenance` | `GET`, `POST` | List and create maintenance tasks |
| `/api/v1/maintenance/recommendations/{id}` | `GET` | Sourced category preventive care recommendations |
| `/api/v1/service-history/product/{id}` | `GET` | List repair and servicing history records |
| `/api/v1/service-history` | `POST` | Register a new service/repair record |
| `/api/v1/accessories/recommendations/{id}` | `GET` | Compatible & potentially compatible accessories |
| `/api/v1/safety-recalls/check/{id}` | `GET` | Evaluate product against safety recall bulletins |
| `/api/v1/safety-recalls/vault-summary` | `GET` | Scan entire vault for active recall alerts |
| `/api/v1/notifications` | `GET` | List milestone expiry notifications |
| `/api/v1/notifications/unread-count` | `GET` | Get unread notification counter |
| `/api/v1/notifications/{id}/read` | `PATCH`| Mark single notification as read |
| `/api/v1/notifications/mark-all-read` | `POST` | Mark all user notifications as read |

---

*OWNIT REST API Documentation — Fully compliant with OpenAPI v3.1.*
