# Frontend Dockerfile
FROM node:18-alpine as build

WORKDIR /app

# Bağımlılıkları kopyala
COPY package.json ./

# Bağımlılıkları yükle (yarn.lock oluşturulacak)
RUN yarn install --network-timeout 100000

# Kaynak kodu kopyala
COPY . .

# Build argümanları
ARG REACT_APP_BACKEND_URL
ENV REACT_APP_BACKEND_URL=$REACT_APP_BACKEND_URL

# Production build
RUN yarn build

# Nginx ile serve et
FROM nginx:alpine

# Nginx config
RUN rm /etc/nginx/conf.d/default.conf
COPY nginx.conf /etc/nginx/conf.d/

# Build dosyalarını kopyala
COPY --from=build /app/build /usr/share/nginx/html

EXPOSE 80

CMD ["nginx", "-g", "daemon off;"]
