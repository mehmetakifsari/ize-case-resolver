# EMERGENT AI – IZE Case Resolver

## 📋 Proje Hakkında

IZE Case Resolver, yurtdışı garanti dosyalarını (PDF) otomatik olarak analiz eden, garanti kapsamı değerlendirmesi yapan ve müşteri bildirimi için email taslağı oluşturan AI destekli bir sistemdir.

## 🚀 Özellikler

### ✅ Tamamlanan Özellikler (Faz 1)

- **PDF Analizi**: IZE PDF dosyalarından otomatik metin çıkarma (PyPDF2)
- **AI Değerlendirme**: OpenAI GPT-4o ile akıllı garanti analizi
- **Garanti Kuralları Yönetimi**: Değerlendirme için kullanılacak kuralları ekleme/silme
- **Geçmiş Analizler**: Tüm IZE case'lerini listeleme ve detaylı görüntüleme
- **Yapılandırılmış Çıktı**: JSON formatında standardize edilmiş sonuçlar

### 🎯 Analiz Edilen Bilgiler

- ✅ 2 yıllık garanti kapsamında mı?
- ✅ Garanti kararı (Kapsam dahili/dışı/ek bilgi gerekli)
- ✅ Arıza nedeni ve kök sebep analizi
- ✅ Yapılan işlemler
- ✅ Değiştirilen parçalar
- ✅ Tamir süreci özeti
- ✅ Email taslağı (Kurumsal ve kibar dil)

## 🛠️ Teknoloji Stack

### Backend
- **FastAPI** - Modern Python web framework
- **MongoDB** - NoSQL veritabanı
- **PyPDF2** - PDF metin çıkarma
- **OpenAI GPT-4o** - AI analizi (emergentintegrations)
- **Motor** - Async MongoDB driver

### Frontend
- **React 19** - Modern UI framework
- **React Router** - Sayfa yönlendirme
- **Shadcn/ui** - UI bileşenleri
- **Tailwind CSS** - Styling
- **Axios** - HTTP client

## 📁 Proje Yapısı

```
/app/
├── backend/
│   ├── server.py           # Ana FastAPI uygulaması
│   ├── requirements.txt    # Python bağımlılıkları
│   └── .env               # Ortam değişkenleri
├── frontend/
│   ├── src/
│   │   ├── App.js         # Ana React uygulaması
│   │   └── components/    # UI bileşenleri
│   ├── package.json       # Node bağımlılıkları
│   └── .env              # Frontend ortam değişkenleri
└── README.md
```

## 🔧 Kurulum ve Çalıştırma

### Gereksinimler
- Python 3.11+
- Node.js 18+
- MongoDB

### Backend Kurulumu
```bash
cd /app/backend
pip install -r requirements.txt
```

### Frontend Kurulumu
```bash
cd /app/frontend
yarn install
```

### Servisleri Başlatma
```bash
# Tüm servisleri başlat
sudo supervisorctl restart all

# Sadece backend
sudo supervisorctl restart backend

# Sadece frontend
sudo supervisorctl restart frontend
```

### Servis Durumu Kontrolü
```bash
sudo supervisorctl status
```

## 🌐 API Endpoints

### Garanti Kuralları
- `POST /api/warranty-rules` - Yeni kural ekle
- `GET /api/warranty-rules` - Tüm kuralları listele
- `DELETE /api/warranty-rules/{rule_id}` - Kural sil

### IZE Analizi
- `POST /api/analyze` - PDF yükle ve analiz et (multipart/form-data)
- `GET /api/cases` - Tüm case'leri listele
- `GET /api/cases/{case_id}` - Belirli bir case'i getir
- `DELETE /api/cases/{case_id}` - Case sil

## 📊 Veri Modelleri

### IZE Case Schema
```json
{
  "id": "uuid",
  "case_title": "IZE_NO - COMPANY - PLATE",
  "ize_no": "string",
  "company": "string",
  "plate": "string",
  "vin": "string",
  "warranty_start_date": "YYYY-MM-DD",
  "repair_date": "YYYY-MM-DD",
  "vehicle_age_months": "number",
  "repair_km": "number",
  "is_within_2_year_warranty": "boolean",
  "warranty_decision": "COVERED | OUT_OF_COVERAGE | ADDITIONAL_INFO_REQUIRED",
  "decision_rationale": ["string"],
  "failure_complaint": "string",
  "failure_cause": "string",
  "operations_performed": ["string"],
  "parts_replaced": [{"partName": "string", "description": "string", "qty": number}],
  "repair_process_summary": "string",
  "email_subject": "string",
  "email_body": "string",
  "pdf_file_name": "string",
  "extracted_text": "string",
  "created_at": "datetime",
  "binder_version_used": "string"
}
```

### Warranty Rule Schema
```json
{
  "id": "uuid",
  "rule_version": "string",
  "rule_text": "string",
  "keywords": ["string"],
  "created_at": "datetime"
}
```

## 🔑 Ortam Değişkenleri

### Backend (.env)
```env
MONGO_URL=mongodb://localhost:27017
DB_NAME=test_database
CORS_ORIGINS=*
EMERGENT_LLM_KEY=sk-emergent-xxxxx
```

### Frontend (.env)
```env
REACT_APP_BACKEND_URL=https://ize-dashboard.preview.emergentagent.com
```

## 💡 Kullanım Örnekleri

### 1. Garanti Kuralı Ekleme (cURL)
```bash
curl -X POST http://localhost:8001/api/warranty-rules \
  -H "Content-Type: application/json" \
  -d '{
    "rule_version": "1.0",
    "rule_text": "2 yıl içindeki araçlar garanti kapsamındadır...",
    "keywords": ["garanti", "2 yıl", "üretim hatası"]
  }'
```

### 2. PDF Analizi (cURL)
```bash
curl -X POST http://localhost:8001/api/analyze \
  -F "file=@/path/to/ize_file.pdf"
```

### 3. Case'leri Listeleme
```bash
curl http://localhost:8001/api/cases
```

## 🎨 Frontend Sayfaları

1. **Ana Sayfa (/)**: PDF yükleme ve analiz başlatma
2. **Geçmiş Analizler (/cases)**: Tüm IZE case'lerinin listesi
3. **Case Detay (/case/:id)**: Analiz sonuçlarının detaylı görünümü
   - Özet bilgiler
   - Analiz detayları
   - Email taslağı
   - Ham veri
4. **Garanti Kuralları (/rules)**: Kural ekleme ve yönetim

## 🔮 Gelecek Özellikler (Faz 2)

- [ ] Email gönderme entegrasyonu (SMTP/SendGrid)
- [ ] Batch PDF işleme
- [ ] Excel export
- [ ] Kullanıcı yetkilendirme sistemi
- [ ] Garanti Binder PDF'den otomatik kural çıkarma
- [ ] Dashboard ve istatistikler
- [ ] Ek dosya yükleme (fotoğraflar, job card, vb.)

## 🧪 Test

### Backend API Testi
```bash
# API health check
curl http://localhost:8001/api/

# Warranty rules test
curl http://localhost:8001/api/warranty-rules
```

### Frontend Test
Tarayıcınızda: `https://ize-dashboard.preview.emergentagent.com`

## 📝 Notlar

- **PDF Format**: Sadece PDF dosyaları desteklenir
- **AI Model**: OpenAI GPT-4o kullanılmaktadır
- **Dil**: Tüm analiz ve email çıktıları Türkçe'dir
- **Email**: Şu anda sadece taslak oluşturulmaktadır (gönderim Faz 2'de)

## 🤝 Katkıda Bulunma

Bu proje Emergent AI tarafından geliştirilmiştir.

## 📄 Lisans

Özel proje - Tüm hakları saklıdır.

---

**Geliştirici**: Emergent AI  
**Versiyon**: 1.0.0  
**Son Güncelleme**: Şubat 2026
