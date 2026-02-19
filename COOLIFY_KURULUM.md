# IZE Case Resolver - Coolify Kurulum Rehberi

## 🎯 Hızlı Başlangıç

Bu rehber, IZE Case Resolver uygulamasını Coolify üzerinde deploy etmenizi sağlar.

---

## 📋 Ön Gereksinimler

- Coolify kurulu bir sunucu (VDS/VPS)
- Domain adı (örn: visupanel.com)
- GitHub hesabı
- OpenAI API Key (https://platform.openai.com/api-keys)

---

## 🌐 Domain Yapılandırması

| Servis | Domain | Açıklama |
|--------|--------|----------|
| Frontend | `ize.visupanel.com` | Ana uygulama |
| Backend | `api-ize.visupanel.com` | API servisi |

---

## Adım 1: DNS Ayarları (Hostinger)

Hostinger DNS yönetiminde **A kayıtları** ekleyin:

```
Tip: A
Host: ize
Değer: SUNUCU_IP_ADRESİ
TTL: 14400

Tip: A  
Host: api.ize
Değer: SUNUCU_IP_ADRESİ
TTL: 14400
```

### ⚠️ ÖNEMLİ SSL AYARLARI

3. **Cloudflare kullanıyorsanız (turuncu bulut/proxy açık)**
   - SSL/TLS mode mutlaka **Full (strict)** olmalı
   - **Flexible kullanmayın** (Coolify/Traefik origin HTTPS ile çalıştığı için handshake bozulur)
   - `api.ize.visupanel.com` için origin sertifikası geçerli olmalı (Coolify'da "Generate SSL Certificate" + redeploy)
   - Sertifika henüz hazır değilse geçici olarak DNS kaydını **DNS only (gri bulut)** yapıp testi öyle yapın

4. **Cloudflare hata koduna göre teşhis**
   - **525**: Cloudflare ↔ origin TLS handshake başarısız (çoğunlukla origin cert yok/yanlış)
   - **526**: Origin sertifikası geçersiz (expired, domain mismatch, self-signed)
   - **522/524**: SSL değil, origin erişim/timeout problemi (firewall/port/routing)

5. **Doğru doğrulama komutları (ReqBin yerine kendi terminalinizde)**
   ```bash
   curl -Iv https://api.ize.visupanel.com/api/health
   openssl s_client -connect api.ize.visupanel.com:443 -servername api.ize.visupanel.com </dev/null | openssl x509 -noout -issuer -subject -dates
   nslookup api.ize.visupanel.com
   ``

**Hostinger DNS kullanıyorsanız:**
- Ek bir ayar gerekmez, Coolify SSL sertifikasını otomatik alır

**Port Erişimi:**
- 3000 ve 8001 portlarına doğrudan erişim **gerekmez**
- Traefik reverse proxy tüm trafiği 80/443 üzerinden yönlendirir
- Tarayıcıda `ize.visupanel.com:3000` şeklinde **denemeyin** - sadece `https://ize.visupanel.com` kullanın

---

## Adım 2: GitHub'a Push

Emergent platformunda **"Save to GitHub"** butonunu kullanın.

**Veya manuel olarak:**
```bash
git init
git add .
git commit -m "Initial commit - IZE Case Resolver"
git remote add origin https://github.com/KULLANICI/ize-case-resolver.git
git push -u origin main
```

---

## Adım 3: Coolify'da Proje Oluşturma

### 3.1 Network Oluşturma (İlk seferde)

Coolify terminalinde:
```bash
docker network create coolify
```

### 3.2 Docker Compose Projesi Oluştur

1. Coolify paneline giriş yapın
2. **"+ Add Resource"** → **"Docker Compose"** seçin
3. **"GitHub"** veya **"Public Repository"** seçin
4. Repo URL'nizi girin
5. Ayarlar:
   - **Branch:** `main`
   - **Docker Compose Location:** `docker-compose.yml`
   - **Build Pack:** Docker Compose

### 3.3 Domain Ayarları (Coolify Panelinde)

**ÖNEMLİ:** Coolify'da her servis için domain'leri ayrı ayrı tanımlayın:

1. **Backend servisi** seçin → Settings
   - Domain: `api.ize.visupanel.com`
   - ✅ "Generate SSL Certificate" aktif

2. **Frontend servisi** seçin → Settings  
   - Domain: `ize.visupanel.com`
   - ✅ "Generate SSL Certificate" aktif

---

## Adım 4: Environment Variables

Coolify'da **Environment Variables** bölümüne ekleyin:

```env
# ZORUNLU
OPENAI_API_KEY=sk-proj-xxx (OpenAI'den aldığınız key)
JWT_SECRET_KEY=rastgele-guclu-32-karakter-key

# OPSİYONEL (Admin panelinden de ayarlanabilir)
# STRIPE_API_KEY=sk_live_xxx
# IYZICO_API_KEY=xxx
# IYZICO_SECRET_KEY=xxx
# SMTP_HOST=smtp.gmail.com
# SMTP_PORT=587
# SMTP_USER=email@domain.com
# SMTP_PASSWORD=xxx
```

**JWT Key Oluşturma (Terminal):**
```bash
openssl rand -hex 32
```

---

## Adım 5: Deploy

1. **"Deploy"** butonuna tıklayın
2. Build loglarını takip edin (~5-10 dakika)
3. Tüm servisler yeşil olduğunda hazır!

### 💾 Kalıcı MongoDB Volume Kontrolü (ÇOK ÖNEMLİ)

Sunucu reboot olduğunda kullanıcılar ve panel şifreleri siliniyorsa MongoDB kalıcı disk mount edilmemiştir.

Coolify'da `mongodb` servisi için:
- **Persistent Storage / Volume** aktif olmalı
- Container path: `/data/db`
- Volume adı örnek: `mongodb_data`

Doğrulama komutu:
```bash
docker inspect ize-mongodb --format '{{json .Mounts}}'
```
Çıktıda `/data/db` için bir volume görmelisiniz.


**İlk deploy'da SSL sertifikası alınması 1-2 dakika sürebilir.**

---

## Adım 6: İlk Admin Hesabı Oluşturma

Deploy sonrası Coolify'da **ize-backend** container'ına terminal açın:

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

## ✅ Erişim Bilgileri

| | |
|---|---|
| **Frontend URL** | https://ize.visupanel.com |
| **API URL** | https://api.ize.visupanel.com |
| **API Health Check** | https://api.ize.visupanel.com/api/health |
| **Admin Email** | admin@visupanel.com |
| **Admin Şifre** | Admin@123! (değiştirin!) |

---

## 🔧 Sorun Giderme

### SSL Hatası Alıyorum

1. **DNS propagasyonunu bekleyin** (24 saate kadar sürebilir)
   ```bash
   # DNS kontrolü
   nslookup ize.visupanel.com
   nslookup api.ize.visupanel.com
   ```

2. **Coolify'da SSL sertifikasını yenileyin**
   - Servis → Settings → "Generate SSL Certificate" → Redeploy

3. **Cloudflare kullanıyorsanız**
   - Proxy'yi kapatın (DNS Only)
   - VEYA SSL ayarını "Full (Strict)" yapın

### Port Erişim Hatası

- `ize.visupanel.com:3000` şeklinde **erişmeyin**
- Sadece `https://ize.visupanel.com` kullanın
- Traefik tüm trafiği 80/443 üzerinden yönlendirir

### Build Hatası

```bash
# Coolify'da "Redeploy" → "Force Rebuild" seçin
```

### Container Logları

```bash
docker logs ize-backend -f --tail 100
docker logs ize-frontend -f --tail 100
docker logs ize-mongodb -f --tail 100
```

### MongoDB Bağlantı Testi

```bash
docker exec -it ize-mongodb mongosh --eval "db.stats()"
```

### Backend Health Check

```bash
curl https://api.ize.visupanel.com/api/health
```

### OCR Dil Kontrolü

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
