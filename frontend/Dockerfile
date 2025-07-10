FROM node:18-alpine

WORKDIR /app

COPY . .

EXPOSE 3000

RUN npm install --force

RUN npm run build

# Serve using a lightweight web server (optional: change to `vite preview` or `serve` if used)
RUN npm install -g serve

CMD ["serve", "-s", "build", "-l", "3000"]
