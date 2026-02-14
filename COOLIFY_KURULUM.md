# IZE Case Resolver - Coolify Kurulum Rehberi (visupanel.com)

## Domain Yapılandırması

| Servis | Domain | Açıklama |
|--------|--------|----------|
| Frontend | `ize.visupanel.com` | Ana uygulama |
| Backend | `api.visupanel.com` | API servisi |

---

## Adım 1: DNS Ayarları

Cloudflare veya domain sağlayıcınızda A kayıtları ekleyin:

```
ize.visupanel.com   →  SUNUCU_IP  (Proxy: OFF veya DNS Only)
api.visupanel.com   →  SUNUCU_IP  (Proxy: OFF veya DNS Only)
```

> ⚠️ Coolify SSL sertifikası alacağı için Cloudflare proxy'yi kapatın veya Full (Strict) SSL kullanın.

---

## Adım 2: GitHub'a Push

Projeyi GitHub'a yükleyin:
```bash
git init
git add .
git commit -m "Initial commit"
git remote add origin https://github.com/KULLANICI/ize-case-resolver.git
git push -u origin main
```

---

## Adım 3: Coolify'da Proje Oluşturma

1. Coolify paneline giriş yapın
2. **"+ Add Resource"** → **"Docker Compose"** seçin
3. GitHub repo'nuzu bağlayın
4. **Branch:** `main`
5. **Docker Compose Location:** `docker-compose.yml`

---

## Adım 4: Environment Variables

Coolify'da şu değişkenleri ekleyin:

```env
EMERGENT_LLM_KEY=sk-emergent-xxx
JWT_SECRET_KEY=guclu-rastgele-bir-anahtar-olusturun
```

---

## Adım 5: Deploy

1. **"Deploy"** butonuna tıklayın
2. Build loglarını takip edin (~5-10 dakika)
3. Başarılı olduğunda:
   - Frontend: https://ize.visupanel.com
   - API: https://api.visupanel.com/api/

---

## Adım 6: İlk Admin Oluşturma

Deploy sonrası Coolify'da terminal açın veya SSH ile bağlanın:

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
    'full_name': 'Admin',
    'phone_number': '',
    'branch': 'Hadımköy',
    'role': 'admin',
    'is_active': True,
    'free_analyses_remaining': 999,
    'total_analyses': 0,
    'hashed_password': pwd_context.hash('AdminSifre123!'),
    'created_at': datetime.now(timezone.utc).isoformat()
}

db.users.update_one({'email': admin['email']}, {'$set': admin}, upsert=True)
print('✅ Admin oluşturuldu: admin@visupanel.com / AdminSifre123!')
EOF
```

---

## Erişim Bilgileri

| | |
|---|---|
| **URL** | https://ize.visupanel.com |
| **Admin Email** | admin@visupanel.com |
| **Admin Şifre** | AdminSifre123! (değiştirin!) |

---

## Emergent LLM Key Nasıl Alınır?

1. [Emergent Platform](https://emergentagent.com)'a giriş yapın
2. Profile → Universal Key bölümüne gidin
3. Key'i kopyalayın ve Coolify'da `EMERGENT_LLM_KEY` olarak ekleyin

**Veya** admin panelinden (API Ayarları) ekleyebilirsiniz.

---

## Sorun Giderme

### Build hatası:
```bash
# Coolify'da "Redeploy" → "Force Rebuild" seçin
```

### Container logları:
```bash
docker logs ize-backend
docker logs ize-frontend
```

### MongoDB bağlantı hatası:
```bash
docker exec -it ize-mongodb mongosh --eval "db.stats()"
```

### OCR çalışmıyor:
```bash
docker exec -it ize-backend tesseract --list-langs
# deu, eng, tur görünmeli
```

---

## Yedekleme

```bash
# MongoDB yedekleme
docker exec ize-mongodb mongodump --out /data/backup
docker cp ize-mongodb:/data/backup ./mongodb_backup_$(date +%Y%m%d)

# Geri yükleme
docker cp ./mongodb_backup_TARIH ize-mongodb:/data/backup
docker exec ize-mongodb mongorestore /data/backup
```

---

## Güncelleme

GitHub'a push yaptığınızda Coolify otomatik deploy edebilir:

1. Coolify'da projeye gidin
2. **Settings** → **Webhooks** → Enable
3. GitHub repo'da webhook ekleyin

Veya manuel:
1. Coolify'da **"Redeploy"** butonuna tıklayın
