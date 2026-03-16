# Build stage
FROM node:20-alpine AS build
WORKDIR /app
ARG VITE_API_BASE=http://localhost:8080/api
ENV VITE_API_BASE=$VITE_API_BASE
COPY package*.json ./
RUN npm install
COPY . /app
RUN npm run build

# Serve stage
FROM nginx:1.25-alpine
COPY --from=build /app/dist /usr/share/nginx/html
COPY nginx.conf /etc/nginx/conf.d/default.conf
EXPOSE 80
