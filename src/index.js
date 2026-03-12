const express = require('express');
const config = require('./config');
const server = require('./server');

const app = express();

app.use(express.json());

server.start(app, config);