# Frontend Dockerfile
FROM node:18-alpine as build

WORKDIR /app

# Bağımlılık dosyalarını kopyala
COPY package.json package-lock.json* ./

# Bağımlılıkları yükle
RUN if [ -f package-lock.json ]; then       npm ci;     else       npm install;     fi

# Kaynak kodu kopyala
COPY . .

# Build argümanları
ARG REACT_APP_BACKEND_URL
ENV REACT_APP_BACKEND_URL=$REACT_APP_BACKEND_URL

# Production build
RUN npm run build

# Nginx ile serve et
FROM nginx:alpine

# Nginx config
RUN rm /etc/nginx/conf.d/default.conf
COPY nginx.conf /etc/nginx/conf.d/

# Build dosyalarını kopyala
COPY --from=build /app/build /usr/share/nginx/html

EXPOSE 80

CMD ["nginx", "-g", "daemon off;"]
