# IZE Case Resolver - Coolify Kurulum Rehberi

## 🎯 Hızlı Başlangıç

Bu rehber, IZE Case Resolver uygulamasını Coolify üzerinde deploy etmenizi sağlar.

---

## 📋 Ön Gereksinimler

- Coolify kurulu bir sunucu
- Domain adı (örn: visupanel.com)
- GitHub hesabı

---

## 🌐 Domain Yapılandırması

| Servis | Domain | Açıklama |
|--------|--------|----------|
| Frontend | `ize.visupanel.com` | Ana uygulama |
| Backend | `api.ize.visupanel.com` | API servisi |

---

## Adım 1: DNS Ayarları

Cloudflare veya domain sağlayıcınızda A kayıtları ekleyin:

```
ize.visupanel.com       →  SUNUCU_IP
api.ize.visupanel.com   →  SUNUCU_IP
```

> ⚠️ **Önemli:** Coolify SSL sertifikası alacağı için Cloudflare proxy'yi kapatın veya Full (Strict) SSL kullanın.

---

## Adım 2: GitHub'a Push

Emergent platformunda **"Save to GitHub"** butonunu kullanın veya manuel olarak:

```bash
git init
git add .
git commit -m "Initial commit - IZE Case Resolver"
git remote add origin https://github.com/KULLANICI/ize-case-resolver.git
git push -u origin main
```

---

## Adım 3: Coolify'da Proje Oluşturma

### 3.1 Docker Compose Projesi Oluştur

1. Coolify paneline giriş yapın
2. **"+ Add Resource"** → **"Docker Compose"** seçin
3. **"GitHub"** seçin ve repo'nuzu bağlayın
4. Ayarlar:
   - **Branch:** `main`
   - **Docker Compose Location:** `docker-compose.yml`
   - **Build Pack:** Docker Compose

### 3.2 Domain Ayarları

Coolify'da her servis için domain ekleyin:

**Frontend servisi için:**
- Domain: `ize.visupanel.com`
- Port: `3000`

**Backend servisi için:**
- Domain: `api.ize.visupanel.com`
- Port: `8001`

---

## Adım 4: Environment Variables

Coolify'da **Environment Variables** bölümüne şu değişkenleri ekleyin:

### Backend (.env)

```env
# MongoDB (Coolify içinde)
MONGO_URL=mongodb://mongodb:27017
DB_NAME=ize_database

# CORS
CORS_ORIGINS=*

# JWT Secret (Güçlü bir key oluşturun!)
JWT_SECRET_KEY=cok-guclu-rastgele-bir-anahtar-32-karakter

# OpenAI / Emergent LLM Key
EMERGENT_LLM_KEY=sk-emergent-xxxxx

# Stripe (Opsiyonel - Panelden de ayarlanabilir)
STRIPE_API_KEY=sk_live_xxxxx

# iyzico (Opsiyonel - Panelden de ayarlanabilir)
IYZICO_API_KEY=xxxxx
IYZICO_SECRET_KEY=xxxxx
IYZICO_BASE_URL=api.iyzipay.com
```

### Frontend (.env)

```env
REACT_APP_BACKEND_URL=https://api.ize.visupanel.com
```

---

## Adım 5: Deploy

1. **"Deploy"** butonuna tıklayın
2. Build loglarını takip edin (~5-10 dakika)
3. Tüm servisler yeşil olduğunda hazır!

---

## Adım 6: İlk Admin Hesabı Oluşturma

Deploy sonrası Coolify'da terminal açın:

```bash
docker exec -it ize-backend python3 << 'EOF'
from pymongo import MongoClient
from passlib.context import CryptContext
import uuid
from datetime import datetime, timezone

client = MongoClient('mongodb://mongodb:27017')
db = client['ize_database']
pwd_context = CryptContext(schemes=['bcrypt'], deprecated='auto')

admin = {
    'id': str(uuid.uuid4()),
    'email': 'admin@visupanel.com',
    'full_name': 'Admin User',
    'phone_number': '+905551234567',
    'branch': 'Merkez',
    'role': 'admin',
    'is_active': True,
    'free_analyses_remaining': 9999,
    'total_analyses': 0,
    'emails_sent': 0,
    'hashed_password': pwd_context.hash('Admin@123!'),
    'created_at': datetime.now(timezone.utc).isoformat()
}

db.users.update_one({'email': admin['email']}, {'$set': admin}, upsert=True)
print('✅ Admin oluşturuldu!')
print('   Email: admin@visupanel.com')
print('   Şifre: Admin@123!')
EOF
```

---

## Adım 7: Panelden Yapılacak Ayarlar

Admin paneline giriş yapın: `https://ize.visupanel.com/login`

### 7.1 Ödeme Ayarları (`/admin/payment-settings`)

**Stripe:**
- Mode: Live (Production için)
- Live Publishable Key: `pk_live_xxx`
- Live Secret Key: `sk_live_xxx`

**iyzico:**
- Mode: Production
- Production API Key: `xxx`
- Production Secret Key: `xxx`

### 7.2 Fatura Ayarları (`/admin/payment-settings` → Fatura sekmesi)

**Şirket Bilgileri:**
- Şirket Adı
- Vergi Dairesi
- Vergi Numarası
- Adres, Telefon, Email

**E-Fatura Entegrasyonu (Opsiyonel):**
- Paraşüt, Bizimhesap veya Birfatura API bilgileri

### 7.3 E-posta Ayarları (`/admin/email-settings`)

**SMTP Ayarları:**
- Host: `smtp.yourprovider.com`
- Port: `587`
- Kullanıcı: `info@visupanel.com`
- Şifre: `xxx`

### 7.4 Site Ayarları (`/admin/site-settings`)

- Site başlığı, açıklaması
- SEO meta bilgileri
- Google Analytics / Yandex Metrica kodları
- Sosyal medya linkleri

---

## ✅ Erişim Bilgileri

| | |
|---|---|
| **Frontend URL** | https://ize.visupanel.com |
| **API URL** | https://api.ize.visupanel.com |
| **Admin Email** | admin@visupanel.com |
| **Admin Şifre** | Admin@123! (değiştirin!) |

---

## 🔧 Sorun Giderme

### Build hatası
```bash
# Coolify'da "Redeploy" → "Force Rebuild" seçin
```

### Container logları
```bash
docker logs ize-backend -f --tail 100
docker logs ize-frontend -f --tail 100
```

### MongoDB bağlantı testi
```bash
docker exec -it ize-mongodb mongosh --eval "db.stats()"
```

### Backend sağlık kontrolü
```bash
curl https://api.ize.visupanel.com/api/health
```

### OCR kontrolü
```bash
docker exec -it ize-backend tesseract --list-langs
# deu, eng, tur görünmeli
```

---

## 💾 Yedekleme

### MongoDB Yedekleme
```bash
# Yedek al
docker exec ize-mongodb mongodump --out /data/backup
docker cp ize-mongodb:/data/backup ./mongodb_backup_$(date +%Y%m%d)

# Geri yükle
docker cp ./mongodb_backup_TARIH ize-mongodb:/data/backup
docker exec ize-mongodb mongorestore /data/backup
```

---

## 🔄 Güncelleme

### Otomatik (Webhook)
1. Coolify'da projeye gidin
2. **Settings** → **Webhooks** → Enable
3. GitHub repo'da webhook URL'i ekleyin

### Manuel
1. GitHub'a push yapın
2. Coolify'da **"Redeploy"** butonuna tıklayın

---

## 📞 Destek

Sorunlarınız için:
- GitHub Issues açın
- info@visupanel.com adresine yazın

---

**IZE Case Resolver** - Renault Trucks Yetkili Servisleri için geliştirilmiştir.
