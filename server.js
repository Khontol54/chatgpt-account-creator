const express = require('express');
const bodyParser = require('body-parser');
const cors = require('cors');
const Logger = require('./utils/logger');
const AccountCreator = require('./core/accountCreator');
const DatabaseManager = require('./database/dbManager');
const config = require('./config');

const logger = Logger.getLogger('Server');
const app = express();

// Middleware
app.use(cors());
app.use(bodyParser.json());

// Initialize
let accountCreator;

/**
 * Health check
 */
app.get('/health', (req, res) => {
  res.json({ status: 'ok', timestamp: new Date() });
});

/**
 * Create single account
 */
app.post('/api/create-account', async (req, res) => {
  try {
    logger.info('API request: Create single account');
    const result = await accountCreator.createSingleAccount();
    res.json(result);
  } catch (error) {
    logger.error('Error creating account via API:', error);
    res.status(500).json({ error: error.message });
  }
});

/**
 * Create batch accounts
 */
app.post('/api/create-batch', async (req, res) => {
  try {
    const { count } = req.body;
    if (!count || count < 1) {
      return res.status(400).json({ error: 'Invalid count' });
    }
    logger.info(`API request: Create batch of ${count} accounts`);
    const results = await accountCreator.createBatchAccounts(count);
    res.json({ results, summary: {
      total: results.length,
      successful: results.filter(r => r.success).length,
      failed: results.filter(r => !r.success).length
    }});
  } catch (error) {
    logger.error('Error creating batch via API:', error);
    res.status(500).json({ error: error.message });
  }
});

/**
 * Get all accounts
 */
app.get('/api/accounts', async (req, res) => {
  try {
    const accounts = await DatabaseManager.getAllAccounts();
    res.json({ accounts, total: accounts.length });
  } catch (error) {
    logger.error('Error fetching accounts:', error);
    res.status(500).json({ error: error.message });
  }
});

/**
 * Get account by email
 */
app.get('/api/accounts/:email', async (req, res) => {
  try {
    const account = await DatabaseManager.getAccountByEmail(req.params.email);
    if (!account) {
      return res.status(404).json({ error: 'Account not found' });
    }
    res.json(account);
  } catch (error) {
    logger.error('Error fetching account:', error);
    res.status(500).json({ error: error.message });
  }
});

/**
 * Start server
 */
async function startServer() {
  try {
    await DatabaseManager.initialize();
    accountCreator = new AccountCreator();
    
    app.listen(config.server.port, config.server.host, () => {
      logger.info(`Server running on ${config.server.host}:${config.server.port}`);
    });
  } catch (error) {
    logger.error('Failed to start server:', error);
    process.exit(1);
  }
}

startServer();

// Graceful shutdown
process.on('SIGINT', async () => {
  logger.info('Shutting down...');
  await DatabaseManager.close();
  process.exit(0);
});