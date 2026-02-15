# IZE Case Resolver - Product Requirements Document

## Overview
IZE Case Resolver, Renault Trucks için yurtdışı garanti dosyalarını (IZE PDF'leri) yapay zeka ile analiz eden bir web uygulamasıdır.

## Core Features

### 1. PDF Analysis Engine
- **Status**: ✅ COMPLETE
- Text-based ve scanned/OCR destekli PDF okuma
- OpenAI GPT-4o ile garanti kurallarına göre analiz
- Türkçe ve Almanca dil desteği

### 2. Authentication & Authorization
- **Status**: ✅ COMPLETE
- JWT tabanlı authentication
- İki rol: Admin ve User
- 5 ücretsiz analiz kredisi yeni kullanıcılara

### 3. User Management
- **Status**: ✅ COMPLETE
- Kullanıcı profili alanları: full_name, email, phone_number, branch, role
- Şifre karmaşıklık kuralları (8+ karakter, büyük/küçük harf, özel karakter)
- Şube listesi: Bursa, İzmit, Orhanlı, Hadımköy, Keşan

### 4. Admin Panel
- **Status**: ✅ COMPLETE
- Katlanabilir yan menü (sidebar)
- Analytics Dashboard (istatistikler)
- Kullanıcı yönetimi (CRUD, filtreleme, kredi ekleme)
- IZE case yönetimi (filtreleme, arşivleme, silme)
- Garanti kuralları yönetimi
- API key yönetimi (maskelenmiş gösterim)

### 5. User Features
- **Status**: ✅ COMPLETE
- PDF yükleme ve analiz
- Kendi analizlerini görüntüleme
- Case detay sayfası (collapsible sections)

### 6. UI/UX
- **Status**: ✅ COMPLETE
- Mobile responsive design
- Dark/Light theme support
- Türkçe arayüz

## Architecture

```
/app/
├── backend/
│   ├── server.py        # FastAPI main app
│   ├── database.py      # MongoDB connection
│   ├── models/          # Pydantic models
│   │   ├── user.py
│   │   ├── case.py
│   │   ├── warranty.py
│   │   ├── settings.py
│   │   └── site_settings.py
│   ├── routes/          # API endpoints
│   │   ├── auth.py
│   │   ├── cases.py
│   │   ├── admin.py
│   │   ├── warranty.py
│   │   └── site_settings.py
│   └── services/        # Business logic
│       ├── auth.py
│       ├── pdf_processor.py
│       └── ai_analyzer.py
├── frontend/
│   └── src/
│       ├── App.js       # React SPA
│       └── translations.js # TR/EN translations
└── memory/
    └── PRD.md
```

## Database Schema

### users
```json
{
  "id": "uuid",
  "email": "string",
  "full_name": "string",
  "phone_number": "string",
  "branch": "string",
  "role": "admin|user",
  "is_active": "boolean",
  "free_analyses_remaining": "integer",
  "total_analyses": "integer",
  "hashed_password": "string",
  "created_at": "datetime"
}
```

### ize_cases
```json
{
  "id": "uuid",
  "user_id": "string",
  "branch": "string",
  "ize_no": "string",
  "company": "string",
  "warranty_decision": "COVERED|OUT_OF_COVERAGE|ADDITIONAL_INFO_REQUIRED",
  "is_archived": "boolean",
  "month": "integer",
  "year": "integer"
}
```

### site_settings
```json
{
  "id": "site_settings",
  "site_name": "string",
  "site_title": "string",
  "site_description": "string",
  "default_language": "tr|en",
  "meta_title": "string",
  "meta_description": "string",
  "meta_keywords": "string",
  "google_analytics_id": "string",
  "google_tag_manager_id": "string",
  "yandex_metrica_id": "string",
  "contact_email": "string",
  "contact_phone": "string",
  "company_name": "string",
  "footer_text": "string"
}
```

### warranty_rules
```json
{
  "id": "uuid",
  "rule_version": "string",
  "rule_text": "string",
  "keywords": ["string"],
  "source_type": "manual|pdf",
  "source_filename": "string|null",
  "is_active": "boolean",
  "created_at": "datetime"
}
```

## API Endpoints

### Authentication
- POST /api/auth/register - User registration
- POST /api/auth/login - User login
- GET /api/auth/me - Current user info

### Cases
- POST /api/cases/analyze - Upload and analyze PDF (with auto email notification)
- GET /api/cases - List user's cases
- GET /api/cases/{id} - Get case details
- DELETE /api/cases/{id} - Delete case
- PATCH /api/cases/{id}/archive - Archive/unarchive case

### Admin
- GET /api/admin/analytics - Dashboard statistics
- GET /api/admin/users - List all users
- POST /api/admin/users - Create user
- PUT /api/admin/users/{id} - Update user
- DELETE /api/admin/users/{id} - Delete user
- PATCH /api/admin/users/{id}/toggle-active - Toggle user status
- PATCH /api/admin/users/{id}/add-credit - Add credits
- GET /api/admin/settings - Get API settings
- PUT /api/admin/settings - Update API settings

### Email Settings (NEW)
- GET /api/admin/email-settings - Get SMTP settings (Admin only)
- PUT /api/admin/email-settings - Update SMTP settings (Admin only)
- POST /api/admin/email-settings/test - Test SMTP connection (Admin only)

### Site Settings
- GET /api/site-settings - Get site settings (Public)
- PUT /api/site-settings - Update site settings (Admin only)

### Warranty Rules (UPDATED)
- GET /api/warranty-rules - List rules
- GET /api/warranty-rules?active_only=true - List active rules only
- POST /api/warranty-rules - Create manual rule
- POST /api/warranty-rules/upload-pdf - Upload PDF to create rule (NEW)
- PUT /api/warranty-rules/{id} - Update rule
- PATCH /api/warranty-rules/{id}/toggle-active - Toggle active status (NEW)
- DELETE /api/warranty-rules/{id} - Delete rule

## Completed Tasks

### Session 1 (2026-02-14)
1. ✅ Backend refactoring (monolithic → modular)
2. ✅ User model update (phone_number, branch, role)
3. ✅ Password complexity validation
4. ✅ Admin panel with collapsible sidebar
5. ✅ Analytics dashboard
6. ✅ User management page
7. ✅ Case management with filtering
8. ✅ API key management with masking
9. ✅ Registration form with new fields
10. ✅ Mobile responsive UI
11. ✅ Testing (100% pass rate)

### Session 2 (2026-02-14 - Current)
12. ✅ Site Settings page (General, SEO, Analytics, Contact tabs)
13. ✅ Multi-language support (TR/EN) with language switcher
14. ✅ Warranty Rules versioning with PDF upload
15. ✅ Warranty Rules active/inactive toggle
16. ✅ Professional Pricing page with 3 plans and FAQ
17. ✅ All features tested (100% pass rate)

### Session 3 (2026-02-15 - Current)
18. ✅ Email Settings page (SMTP configuration)
19. ✅ Automatic email notification after analysis with PDF attachment
20. ✅ SMTP connection test feature
21. ✅ Email enabled/disabled toggle
22. ✅ All features tested (100% pass rate)

## Upcoming Tasks (P1)
- [ ] Deploy to Coolify (visupanel.com)
- [ ] Configure production SMTP settings
- [ ] User onboarding flow

## Future Tasks (P2)
- [ ] Export reports to Excel/PDF
- [ ] Bulk PDF upload
- [ ] API documentation (Swagger UI)
- [ ] Activity logging/audit trail
