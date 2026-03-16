# Frontend (React + Vite)

SPA cho Danang Hidden Gems: semantic search, b?n d?, bookmark, submit d?a di?m.

## Ch?y dev
```bash
npm install
npm run dev -- --host --port 3000
```
Env: `VITE_API_BASE` (m?c d?nh http://localhost:8080/api). Copy t? `../.env.example` n?u dùng docker-compose.

## Build & serve (dùng Dockerfile)
`docker build -t danang-frontend . && docker run -p 3000:80 danang-frontend`

## Tính nang chính
- Search ng? nghia (PhoBERT/FAISS) + map (Leaflet), toggle list/split/map.
- Chi ti?t d?a di?m, bookmark, reviews, submit d?a di?m (yêu c?u dang nh?p).
- Theme context (light/dark), skeleton/loading states, toast/thông báo l?i co b?n.

## TODO v2
- Playwright smoke flows.
- Nâng thông báo l?i/validation cho form submit & login.
- UI copywriting “Local mode”.
