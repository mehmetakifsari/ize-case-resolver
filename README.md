# IZE Case Resolver

🚀 **Renault Trucks Yurtdışı Garanti Dosyası Analiz Sistemi**

IZE Case Resolver, Renault Trucks yetkili servislerinin yurtdışı garanti (IZE) taleplerini yapay zeka ile analiz eden, fatura ve ödeme yönetimi sunan full-stack bir web uygulamasıdır.

![IZE Case Resolver](https://img.shields.io/badge/version-1.0.0-blue)
![License](https://img.shields.io/badge/license-MIT-green)
![Docker](https://img.shields.io/badge/docker-ready-brightgreen)

## 📋 Özellikler

### Temel Özellikler
- 📄 **PDF Analizi**: Text-based ve OCR destekli PDF okuma
- 🤖 **AI Analiz**: OpenAI GPT-4o ile garanti kurallarına göre değerlendirme
- 📧 **E-posta Bildirimi**: Otomatik analiz sonucu e-postası (PDF eki ile)
- 🌐 **Çoklu Dil**: Türkçe ve İngilizce arayüz desteği
- 🌙 **Tema**: Dark/Light mod desteği

### Ödeme Sistemi
- 💳 **Stripe**: Uluslararası kart ödemeleri
- 🏦 **iyzico**: Türk kartları için ödeme
- 🏧 **Havale/EFT**: Manuel onaylı banka transferi
- 💰 **3 Para Birimi**: TL, USD, EUR desteği

### Fatura Sistemi
- 📃 **PDF Fatura**: Profesyonel tasarımlı otomatik fatura
- 🔗 **E-Fatura Entegrasyonu**: 
  - Paraşüt
  - Bizimhesap
  - Birfatura

### Admin Panel
- 📊 **Dashboard**: Analitik istatistikler
- 👥 **Kullanıcı Yönetimi**: CRUD, kredi ekleme, filtreleme
- 📁 **IZE Dosya Yönetimi**: Arşivleme, silme, filtreleme
- ⚙️ **Ayarlar**: Site, SEO, E-posta, Ödeme, Fatura yapılandırması
- 📜 **Garanti Kuralları**: Versiyon yönetimi, PDF yükleme

## 🏗️ Teknoloji Stack

### Backend
- **Framework**: FastAPI (Python 3.11+)
- **Database**: MongoDB
- **AI**: OpenAI GPT-4o
- **PDF**: pdfplumber, pytesseract (OCR)
- **Email**: SMTP (smtplib)

### Frontend
- **Framework**: React 18
- **Styling**: Tailwind CSS
- **UI Components**: shadcn/ui
- **i18n**: react-i18next
- **Icons**: Lucide React

### Deployment
- **Container**: Docker & Docker Compose
- **Reverse Proxy**: Nginx
- **Platform**: Coolify ready

## 🚀 Kurulum

### Gereksinimler
- Docker & Docker Compose
- MongoDB (veya Coolify içinde)
- OpenAI API Key
- SMTP sunucusu (e-posta için)

### Hızlı Başlangıç

1. **Repoyu klonlayın**
```bash
git clone https://github.com/yourusername/ize-case-resolver.git
cd ize-case-resolver
```

2. **Environment dosyalarını düzenleyin**
```bash
# Backend
cp backend/.env.example backend/.env
# Frontend
cp frontend/.env.example frontend/.env
```

3. **Backend .env düzenleme**
```env
MONGO_URL=mongodb://mongodb:27017
DB_NAME=ize_resolver
EMERGENT_LLM_KEY=your-openai-api-key
STRIPE_API_KEY=sk_test_xxx
IYZICO_API_KEY=sandbox-xxx
IYZICO_SECRET_KEY=sandbox-xxx
IYZICO_BASE_URL=sandbox-api.iyzipay.com
```

4. **Docker ile başlatın**
```bash
docker-compose up -d --build
```

5. **Uygulamaya erişin**
- Frontend: http://localhost:3000
- Backend API: http://localhost:8001
- API Docs: http://localhost:8001/docs

### Coolify ile Deploy

1. Coolify'da yeni bir proje oluşturun
2. GitHub reposunu bağlayın
3. Environment değişkenlerini ayarlayın
4. Deploy edin

Detaylı kurulum için `COOLIFY_KURULUM.md` dosyasına bakın.

## 📁 Proje Yapısı

```
ize-case-resolver/
├── backend/
│   ├── models/           # Pydantic modelleri
│   ├── routes/           # API endpoint'leri
│   ├── services/         # İş mantığı servisleri
│   ├── server.py         # FastAPI ana uygulama
│   ├── database.py       # MongoDB bağlantısı
│   ├── Dockerfile
│   └── requirements.txt
├── frontend/
│   ├── src/
│   │   ├── components/   # React bileşenleri
│   │   ├── pages/        # Sayfa bileşenleri
│   │   ├── locales/      # i18n çevirileri
│   │   └── App.js        # Ana uygulama
│   ├── Dockerfile
│   └── nginx.conf
├── docker-compose.yml
├── COOLIFY_KURULUM.md
└── README.md
```

## 🔐 Varsayılan Hesaplar

| Rol | Email | Şifre |
|-----|-------|-------|
| Admin | admin@ize.com | Admin@123! |
| User | test@example.com | Test@123! |

⚠️ **Önemli**: Production ortamında bu şifreleri mutlaka değiştirin!

## 📊 API Endpoint'leri

### Authentication
- `POST /api/auth/register` - Kayıt
- `POST /api/auth/login` - Giriş
- `GET /api/auth/me` - Kullanıcı bilgisi

### Cases
- `POST /api/cases/analyze` - PDF yükle ve analiz et
- `GET /api/cases` - Kullanıcının dosyaları
- `GET /api/cases/{id}` - Dosya detayı

### Payments
- `GET /api/payments/packages/credits` - Kredi paketleri
- `POST /api/payments/checkout/stripe` - Stripe ödeme
- `POST /api/payments/checkout/iyzico` - iyzico ödeme
- `POST /api/payments/checkout/bank-transfer` - Havale bildirimi

### Admin
- `GET /api/admin/analytics` - Dashboard istatistikleri
- `GET /api/admin/users` - Kullanıcı listesi
- `PATCH /api/admin/users/{id}/add-credit` - Kredi ekle

Tüm API dokümantasyonu için: `/docs` veya `/redoc`

## 🛠️ Geliştirme

### Backend
```bash
cd backend
pip install -r requirements.txt
uvicorn server:app --reload --port 8001
```

### Frontend
```bash
cd frontend
yarn install
yarn start
```

## 📝 Lisans

Bu proje MIT lisansı altında lisanslanmıştır. Detaylar için `LICENSE` dosyasına bakın.

## 🤝 Katkıda Bulunma

1. Fork edin
2. Feature branch oluşturun (`git checkout -b feature/amazing-feature`)
3. Commit edin (`git commit -m 'Add amazing feature'`)
4. Push edin (`git push origin feature/amazing-feature`)
5. Pull Request açın

## 📞 Destek

Sorularınız için issue açabilir veya iletişime geçebilirsiniz.

---

**IZE Case Resolver** - Renault Trucks Yetkili Servisleri için geliştirilmiştir.
