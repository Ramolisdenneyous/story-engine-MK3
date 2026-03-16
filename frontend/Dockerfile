FROM node:22-alpine AS build
WORKDIR /app
COPY package.json package-lock.json* ./
RUN npm install
COPY . .
ARG VITE_API_BASE=http://localhost:8001
ENV VITE_API_BASE=${VITE_API_BASE}
RUN npm run build

FROM node:22-alpine
WORKDIR /app
COPY package.json package-lock.json* ./
RUN npm install --omit=dev
COPY --from=build /app/dist ./dist
EXPOSE 5173
CMD ["sh", "-c", "npm exec vite preview --host 0.0.0.0 --port ${PORT:-5173}"]
