# IZE Case Resolver - Coolify Kurulum Rehberi

## Ön Gereksinimler
- Coolify paneline erişim
- Bir domain (örn: yourdomain.com)
- Emergent LLM Key

---

## Adım 1: GitHub'a Push

Önce bu projeyi GitHub'a yükleyin:
```bash
git init
git add .
git commit -m "Initial commit"
git remote add origin https://github.com/KULLANICI/ize-case-resolver.git
git push -u origin main
```

---

## Adım 2: Coolify'da Proje Oluşturma

1. Coolify paneline giriş yapın
2. **"+ Add Resource"** butonuna tıklayın
3. **"Docker Compose"** seçin
4. GitHub repo'nuzu bağlayın

---

## Adım 3: Environment Variables

Coolify'da şu environment variable'ları ekleyin:

| Variable | Değer | Açıklama |
|----------|-------|----------|
| `EMERGENT_LLM_KEY` | `sk-emergent-xxx` | AI analiz için |
| `BACKEND_DOMAIN` | `api.ize.yourdomain.com` | Backend domain |
| `FRONTEND_DOMAIN` | `ize.yourdomain.com` | Frontend domain |
| `JWT_SECRET_KEY` | `rastgele-guclu-bir-key` | Güvenlik için |

---

## Adım 4: Domain Ayarları

Coolify'da her servis için domain ekleyin:

### Backend:
- Domain: `api.ize.yourdomain.com`
- Port: `8001`
- SSL: ✅ Enable

### Frontend:
- Domain: `ize.yourdomain.com`
- Port: `80`
- SSL: ✅ Enable

---

## Adım 5: DNS Ayarları

Domain sağlayıcınızda A kayıtları ekleyin:

```
api.ize.yourdomain.com  →  SUNUCU_IP
ize.yourdomain.com      →  SUNUCU_IP
```

---

## Adım 6: Deploy

1. Coolify'da **"Deploy"** butonuna tıklayın
2. Build loglarını takip edin
3. Başarılı olduğunda uygulamaya erişin

---

## İlk Admin Kullanıcı Oluşturma

Deploy sonrası terminal ile admin oluşturun:

```bash
# Coolify'da backend container'a bağlanın
docker exec -it ize-backend python3 -c "
from pymongo import MongoClient
from passlib.context import CryptContext
import uuid
from datetime import datetime, timezone

client = MongoClient('mongodb://mongodb:27017')
db = client['ize_database']
pwd_context = CryptContext(schemes=['bcrypt'], deprecated='auto')

admin = {
    'id': str(uuid.uuid4()),
    'email': 'admin@sirketiniz.com',
    'full_name': 'Admin',
    'phone_number': '',
    'branch': 'Hadımköy',
    'role': 'admin',
    'is_active': True,
    'free_analyses_remaining': 999,
    'total_analyses': 0,
    'hashed_password': pwd_context.hash('GucluSifre123!'),
    'created_at': datetime.now(timezone.utc).isoformat()
}

db.users.update_one({'email': admin['email']}, {'\$set': admin}, upsert=True)
print('Admin oluşturuldu!')
"
```

---

## Sorun Giderme

### Build hatası alıyorsanız:
```bash
# Coolify'da Redeploy with --no-cache seçin
```

### MongoDB bağlantı hatası:
```bash
# Container loglarını kontrol edin
docker logs ize-backend
```

### OCR çalışmıyor:
Tesseract dil paketleri Dockerfile'da yüklü, kontrol edin:
```bash
docker exec -it ize-backend tesseract --list-langs
```

---

## Yedekleme

MongoDB verilerini yedeklemek için:
```bash
docker exec ize-mongodb mongodump --out /data/backup
docker cp ize-mongodb:/data/backup ./backup
```

---

## Destek

Sorularınız için: [GitHub Issues]
