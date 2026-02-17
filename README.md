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
