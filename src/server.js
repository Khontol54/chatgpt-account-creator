const logger = require('./utils/logger');

module.exports.start = (app, config) => {
    app.listen(config.port, () => {
        logger.log(`Server running on port ${config.port}`);
    });
};