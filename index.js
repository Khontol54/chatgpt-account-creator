const Logger = require('./utils/logger');
const AccountCreator = require('./core/accountCreator');
const DatabaseManager = require('./database/dbManager');
const config = require('./config');

const logger = Logger.getLogger('MainBot');

async function main() {
  try {
    logger.info('Initializing ChatGPT Account Creator Bot...');
    
    // Initialize database
    await DatabaseManager.initialize();
    logger.info('Database initialized successfully');

    // Initialize account creator
    const accountCreator = new AccountCreator();
    
    // Check for command line arguments
    const args = process.argv.slice(2);
    
    if (args.length === 0) {
      logger.info('No arguments provided. Starting interactive mode...');
      await accountCreator.interactiveMode();
    } else if (args[0] === '--batch' && args[1]) {
      logger.info(`Creating batch of ${args[1]} accounts...`);
      await accountCreator.createBatchAccounts(parseInt(args[1]));
    } else if (args[0] === '--single') {
      logger.info('Creating single account...');
      await accountCreator.createSingleAccount();
    } else {
      logger.warn('Unknown command. Use: --single, --batch <count>');
    }

    process.exit(0);
  } catch (error) {
    logger.error('Fatal error in main process:', error);
    process.exit(1);
  }
}

main();