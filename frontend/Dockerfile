FROM node:18-alpine AS builder

WORKDIR /app

# Копирование package.json
COPY package*.json ./
RUN npm install

# Копирование исходников
COPY . .

# Сборка
RUN npm run build

# Production образ
FROM nginx:alpine

# Копирование собранного приложения
COPY --from=builder /app/build /usr/share/nginx/html

# Копирование конфигурации nginx
COPY nginx.conf /etc/nginx/conf.d/default.conf

EXPOSE 3000

CMD ["nginx", "-g", "daemon off;"]