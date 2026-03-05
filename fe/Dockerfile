# Build stage
FROM oven/bun:latest AS build

WORKDIR /app

COPY package.json bun.lockb ./

# Install without frozen lockfile due to duplicate dep entries
RUN bun install

COPY . .

RUN bun run build

# Production stage
FROM nginx:stable-alpine

COPY --from=build /app/dist /usr/share/nginx/html

COPY nginx.conf /etc/nginx/conf.d/default.conf

EXPOSE 80

RUN sed -i 's/keepalive_timeout[[:space:]]*[0-9]\+;/keepalive_timeout 600;/g' /etc/nginx/nginx.conf

CMD ["nginx", "-g", "daemon off;"]
