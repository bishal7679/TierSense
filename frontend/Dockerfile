# --- Builder stage ---
FROM node:20-alpine AS builder

WORKDIR /app

# Copy only package files first
COPY package.json package-lock.json ./

# Install dependencies
RUN npm install --legacy-peer-deps

# Copy rest of the application
COPY . .

# Build the frontend (Next.js)
RUN npm run build

# --- Runtime image (lightweight) ---
FROM node:20-alpine AS runner

WORKDIR /app

ENV NODE_ENV=production

# Copy built files and production dependencies
COPY --from=builder /app/public ./public
COPY --from=builder /app/.next ./.next
COPY --from=builder /app/node_modules ./node_modules
COPY --from=builder /app/package.json ./package.json

# Expose frontend port
EXPOSE 3000

# Run the production server
CMD ["npm", "start"]
