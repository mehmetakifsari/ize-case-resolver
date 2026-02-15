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
- Sınırsız kredi verme özelliği

### 3. User Management
- **Status**: ✅ COMPLETE (15 Şubat 2026 güncellemesi)
- Kullanıcı profili alanları: full_name, email, phone_number, branch, role
- Şifre karmaşıklık kuralları (8+ karakter, büyük/küçük harf, özel karakter)
- **YENİ**: Admin panelinden kullanıcı ekleme
- **YENİ**: Kredi miktarını manuel ayarlama
- **YENİ**: Sınırsız kredi verme/kaldırma
- Dinamik şube yönetimi

### 4. Admin Panel
- **Status**: ✅ COMPLETE (15 Şubat 2026 güncellemesi)
- Katlanabilir yan menü (sidebar)
- Analytics Dashboard (istatistikler)
- Kullanıcı yönetimi (CRUD, filtreleme, kredi ayarlama, sınırsız kredi)
- IZE case yönetimi (filtreleme, arşivleme, silme)
- Garanti kuralları yönetimi
- API key yönetimi (maskelenmiş gösterim)
- **YENİ**: Admin IZE Analizi yapabilme
- **YENİ**: Şube Yönetimi (ekleme/silme/aktif-pasif)
- **YENİ**: Fiyat Yönetimi (kredi paketleri)

### 5. User Features
- **Status**: ✅ COMPLETE (15 Şubat 2026 güncellemesi)
- PDF yükleme ve analiz (şube seçimi kaldırıldı - kayıttaki şube otomatik kullanılıyor)
- Kendi analizlerini görüntüleme
- Case detay sayfası (collapsible sections)

### 6. UI/UX
- **Status**: ✅ COMPLETE
- Mobile responsive design
- Dark/Light theme support
- Türkçe/İngilizce çoklu dil desteği

### 7. Branch Management
- **Status**: ✅ COMPLETE (15 Şubat 2026)
- Dinamik şube ekleme/silme
- Şube aktif/pasif yapma
- Varsayılan şubeler: Bursa, İzmit, Orhanlı, Hadımköy, Keşan

### 8. Pricing Management  
- **Status**: ✅ COMPLETE (15 Şubat 2026)
- Kredi paketleri yönetimi
- Fiyat, kredi miktarı, para birimi (TRY/USD/EUR)
- Özellikler listesi
- Öne çıkan plan işaretleme
- Paket/Abonelik tipi seçimi

### 9. Payment System
- **Status**: ⚠️ MOCKED (Ödeme entegrasyonları pasif)
- Stripe entegrasyonu (kod mevcut, test edilmedi)
- iyzico entegrasyonu (kod mevcut, API key gerekli)
- Banka transferi seçeneği

### 10. Invoice System
- **Status**: ⚠️ MOCKED (Fatura sistemi pasif)
- PDF fatura oluşturma
- E-fatura entegrasyonları (Paraşüt, Bizimhesap, Birfatura) - placeholder

### 11. Site Logo & Favicon
- **Status**: ✅ COMPLETE (15 Şubat 2026)
- Admin Site Ayarları'ndan Logo ve Favicon URL girişi
- Dinamik favicon ve title güncelleme
- Tüm sayfalarda dinamik logo gösterimi

### 12. Email Verification System
- **Status**: ✅ COMPLETE (15 Şubat 2026)
- Kayıt sonrası doğrulama e-postası gönderme
- 24 saat geçerli doğrulama linki
- Doğrulama sayfası (/verify-email/:token)
- Doğrulama e-postası yeniden gönderme özelliği
- Kullanıcı panelinde doğrulama banner'ı

### 13. Credit Purchase Flow
- **Status**: ✅ COMPLETE (15 Şubat 2026)
- Admin panelden tanımlanan fiyatlandırma planları
- Dinamik plan yükleme (public API)
- Kredi badge'ine tıklayarak ödeme sayfasına yönlendirme
- TRY/USD/EUR para birimi desteği

## Architecture

```
/app/
├── backend/
│   ├── server.py        # FastAPI main app
│   ├── database.py      # MongoDB connection
│   ├── models/          # Pydantic models
│   │   ├── user.py      # User, Branch, PricingPlan models
│   │   ├── case.py
│   │   ├── warranty.py
│   │   ├── settings.py
│   │   └── site_settings.py
│   ├── routes/          # API endpoints
│   │   ├── auth.py      # Login, Register, Email Verification
│   │   ├── cases.py
│   │   ├── admin.py     # User, Branch, Pricing management
│   │   ├── warranty.py
│   │   ├── settings.py  # Public pricing & branches
│   │   └── site_settings.py
│   └── services/        # Business logic
│       ├── auth.py
│       ├── email.py     # SMTP, Verification emails
│       ├── pdf_processor.py
│       └── ai_analyzer.py
├── frontend/
│   └── src/
│       ├── App.js       # React SPA
│       ├── translations.js # TR/EN translations
│       └── pages/
│           ├── PaymentPage.js
│           └── Admin/
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
  "is_email_verified": "boolean",
  "has_unlimited_credits": "boolean",
  "verification_token": "string (optional)",
  "verification_expires": "datetime (optional)",
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
- **NEW** PATCH /api/admin/users/{id}/set-credits - Set exact credit amount
- **NEW** PATCH /api/admin/users/{id}/set-unlimited-credits - Give/remove unlimited credits
- GET /api/admin/settings - Get API settings
- PUT /api/admin/settings - Update API settings

### Branch Management (NEW - 15 Feb 2026)
- GET /api/admin/branches - List all branches (Admin)
- POST /api/admin/branches - Create branch (Admin)
- DELETE /api/admin/branches/{id} - Delete branch (Admin)
- PATCH /api/admin/branches/{id}/toggle - Toggle branch active status (Admin)
- GET /api/settings/public/branches - List active branches (Public)

### Pricing Management (NEW - 15 Feb 2026)
- GET /api/admin/pricing-plans - List all pricing plans (Admin)
- POST /api/admin/pricing-plans - Create pricing plan (Admin)
- PUT /api/admin/pricing-plans/{id} - Update pricing plan (Admin)
- DELETE /api/admin/pricing-plans/{id} - Delete pricing plan (Admin)
- GET /api/settings/public/pricing-plans - List active pricing plans (Public)

### Email Settings (NEW)
- GET /api/admin/email-settings - Get SMTP settings (Admin only)
- PUT /api/admin/email-settings - Update SMTP settings (Admin only)
- POST /api/admin/email-settings/test - Test SMTP connection (Admin only)

### Site Settings
- GET /api/site-settings - Get site settings (Public)
- PUT /api/site-settings - Update site settings (Admin only)

### Payments (NEW - Session 4)
- GET /api/payments/packages/credits - List credit packages (Public)
- GET /api/payments/packages/subscriptions - List subscription plans (Public)
- GET /api/payments/bank-accounts - Get bank accounts for transfer (Public)
- POST /api/payments/checkout/stripe - Create Stripe checkout session
- POST /api/payments/checkout/iyzico - Create iyzico checkout form
- POST /api/payments/checkout/bank-transfer - Create bank transfer request
- GET /api/payments/status/{session_id} - Check payment status
- GET /api/payments/transactions - User's payment history
- GET /api/payments/admin/transactions - All transactions (Admin)
- PATCH /api/payments/admin/transactions/{id}/approve - Approve bank transfer (Admin)
- PATCH /api/payments/admin/transactions/{id}/reject - Reject bank transfer (Admin)
- GET /api/payments/admin/analytics - Payment statistics (Admin)

### Settings (NEW - Session 4)
- GET /api/settings/payment-providers - Get payment provider settings (Admin)
- PUT /api/settings/payment-providers - Update payment provider settings (Admin)
- GET /api/settings/invoice - Get invoice settings (Admin)
- PUT /api/settings/invoice - Update invoice settings (Admin)
- GET /api/settings/invoices - List all invoices (Admin)
- POST /api/settings/invoices/generate/{transaction_id} - Generate invoice for transaction (Admin)
- GET /api/settings/social-media - Get social media links (Public)
- PUT /api/settings/social-media - Update social media links (Admin)

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
22. ✅ Per-user email counter (emails_sent field)
23. ✅ Total emails sent on Dashboard
24. ✅ End-to-end email test completed (akifsari@kocaslanlar.com.tr) - VERIFIED BY USER

### Session 4 (2026-02-15)
25. ✅ Payment System - Full implementation
    - Stripe integration (Emergent key)
    - iyzico integration (sandbox - needs production keys)
    - Havale/EFT (manual approval)
26. ✅ 3 Credit packages (Başlangıç, Pro, Kurumsal)
27. ✅ 3 Subscription plans (monthly)
28. ✅ 3 Currency support (TRY, USD, EUR)
29. ✅ Payment management page in admin panel
30. ✅ Bank transfer approval/rejection workflow
31. ✅ Invoice System with PDF generation
    - Professional invoice design
    - Auto-generate after payment
    - Paraşüt integration (ready)
    - Bizimhesap integration (ready)
    - Birfatura integration (ready)
32. ✅ Payment Settings page (Stripe, iyzico, Bank Transfer config)
33. ✅ Invoice Settings page (Company info, E-fatura providers)
34. ✅ Social Media links in Site Settings
35. ✅ Footer with social media icons
36. ✅ README.md for GitHub
37. ✅ .env.example files
38. ✅ Docker & Coolify deployment ready

### Session 5 (2026-02-15 - Current)
39. ✅ PDF yüklemede şube seçimi kaldırıldı (kayıttaki şube otomatik kullanılıyor)
40. ✅ Admin panelden kullanıcı ekleme özelliği
41. ✅ Kullanıcı kredisi manuel ayarlama
42. ✅ Sınırsız kredi verme/kaldırma özelliği
43. ✅ Şube Yönetimi sayfası (dinamik şube ekleme/silme)
44. ✅ Fiyat Yönetimi sayfası (kredi paketleri yönetimi)
45. ✅ Admin IZE Analizi yapabilme (menüde IZE Analizi linki)
46. ✅ Public pricing API endpoint
47. ✅ Public branches API endpoint

## Test Credentials
- **Admin:** admin@ize.com / Admin@123!
- **Test User:** test@example.com / Test@123!
- **Akif (Test):** akifsari@kocaslanlar.com.tr / AkifTest@2024!

## SMTP Configuration
- **Host:** smtp.visupanel.com
- **Port:** 587
- **User:** info@visupanel.com
- **Sender:** IZE Case Resolver

## Upcoming Tasks (P1)
- [ ] E-posta doğrulama ZORUNLU yapma (opsiyonel ayarı)
- [ ] iyzico production API keys integration
- [ ] Paraşüt/Bizimhesap/Birfatura production API keys

## Future Tasks (P2)
- [ ] Sözleşme/Kontrat Kuralları (garanti kuralları gibi, pasif durumda)
- [ ] Export reports to Excel/PDF
- [ ] Bulk PDF upload
- [ ] API documentation (Swagger UI)
- [ ] Activity logging/audit trail
- [ ] Email templates customization
- [ ] Recurring subscription management (auto-renewal)
- [ ] User onboarding flow
