require('dotenv').config();

module.exports = {
  // OpenAI/ChatGPT Configuration
  openai: {
    signupUrl: 'https://chat.openai.com/auth/login',
    apiUrl: 'https://api.openai.com'
  },

  // Browser Configuration
  browser: {
    headless: process.env.HEADLESS !== 'false',
    slowMo: parseInt(process.env.SLOW_MO) || 0,
    timeout: parseInt(process.env.TIMEOUT) || 30000,
    userAgent: process.env.USER_AGENT || 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
  },

  // Proxy Configuration
  proxy: {
    enabled: process.env.PROXY_ENABLED === 'true',
    url: process.env.PROXY_URL || '',
    username: process.env.PROXY_USERNAME || '',
    password: process.env.PROXY_PASSWORD || ''
  },

  // Email Configuration
  email: {
    provider: process.env.EMAIL_PROVIDER || 'tempmail', // 'gmail', 'tempmail', 'custom'
    gmailUsername: process.env.GMAIL_USERNAME || '',
    gmailPassword: process.env.GMAIL_PASSWORD || '', // Use app-specific password
    customSmtp: {
      host: process.env.SMTP_HOST || '',
      port: parseInt(process.env.SMTP_PORT) || 587,
      secure: process.env.SMTP_SECURE === 'true',
      user: process.env.SMTP_USER || '',
      pass: process.env.SMTP_PASS || ''
    }
  },

  // Database Configuration
  database: {
    type: process.env.DB_TYPE || 'sqlite', // 'sqlite' or 'mongodb'
    sqlite: {
      path: process.env.DB_PATH || './data/accounts.db'
    },
    mongodb: {
      url: process.env.MONGODB_URL || 'mongodb://localhost:27017/chatgpt-accounts'
    }
  },

  // Rate Limiting
  rateLimit: {
    accountsPerDay: parseInt(process.env.RATE_LIMIT_PER_DAY) || 5,
    delayBetweenCreations: parseInt(process.env.DELAY_BETWEEN) || 60000 // 1 minute
  },

  // Logging
  logging: {
    level: process.env.LOG_LEVEL || 'info',
    file: process.env.LOG_FILE || './logs/app.log'
  },

  // Server Configuration (for API mode)
  server: {
    port: parseInt(process.env.PORT) || 3000,
    host: process.env.HOST || 'localhost'
  }
};