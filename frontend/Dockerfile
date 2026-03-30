FROM node:20-alpine AS build

WORKDIR /app

# 配置国内镜像源和优化设置
RUN npm config set registry https://registry.npmmirror.com/ && \
    npm config set fetch-retries 5 && \
    npm config set fetch-retry-mintimeout 20000 && \
    npm config set fetch-retry-maxtimeout 120000 && \
    npm config set prefer-offline true

COPY package.json package-lock.json* /app/
# 使用 --prefer-offline 优先使用缓存
RUN npm ci --no-audit --no-fund --prefer-offline || npm install --no-audit --no-fund

COPY . /app
RUN npm run build

FROM nginx:1.27-alpine

COPY nginx.conf /etc/nginx/conf.d/default.conf
COPY --from=build /app/dist /usr/share/nginx/html

EXPOSE 80
