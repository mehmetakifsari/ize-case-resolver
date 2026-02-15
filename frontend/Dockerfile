# Frontend Dockerfile
FROM node:18-alpine as build

WORKDIR /app

# Bağımlılık dosyalarını kopyala
COPY package.json yarn.lock* package-lock.json* ./

# Yarn/Corepack araçlarını hazırla
RUN corepack enable || true

# Bağımlılıkları yükle (lock dosyasına göre)
RUN if [ -f yarn.lock ]; then \
      yarn install --network-timeout 300000 --frozen-lockfile; \
    elif [ -f package-lock.json ]; then \
      npm ci; \
    else \
      npm install; \
    fi

# Kaynak kodu kopyala
COPY . .

# Build argümanları
ARG REACT_APP_BACKEND_URL
ENV REACT_APP_BACKEND_URL=$REACT_APP_BACKEND_URL

# Production build
RUN if [ -f yarn.lock ]; then \
      yarn build; \
    else \
      npm run build; \
    fi

# Nginx ile serve et
FROM nginx:alpine

# Nginx config
RUN rm /etc/nginx/conf.d/default.conf
COPY nginx.conf /etc/nginx/conf.d/

# Build dosyalarını kopyala
COPY --from=build /app/build /usr/share/nginx/html

EXPOSE 80

CMD ["nginx", "-g", "daemon off;"]
