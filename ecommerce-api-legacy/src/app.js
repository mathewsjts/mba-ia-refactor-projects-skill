const express = require('express');
const loadConfig = require('./config');
const createLogger = require('./config/logger');
const { Database, initSchema, seed } = require('./models/database');
const AuditModel = require('./models/audit.model');
const CourseModel = require('./models/course.model');
const EnrollmentModel = require('./models/enrollment.model');
const { PaymentModel } = require('./models/payment.model');
const ReportModel = require('./models/report.model');
const UserModel = require('./models/user.model');
const BoundedCache = require('./services/cache');
const CheckoutService = require('./services/checkout.service');
const FakePaymentGateway = require('./services/payment.gateway');
const { hashPassword } = require('./services/password');
const ReportService = require('./services/report.service');
const UserService = require('./services/user.service');
const CheckoutController = require('./controllers/checkout.controller');
const ReportController = require('./controllers/report.controller');
const UserController = require('./controllers/user.controller');
const buildRoutes = require('./views/routes');
const errorHandler = require('./middlewares/errorHandler');
const requireAdmin = require('./middlewares/requireAdmin');

// Único lugar que conhece as implementações concretas.
function createApp({ config, database, logger }) {
  const userModel = new UserModel();

  const checkoutService = new CheckoutService({
    database,
    courseModel: new CourseModel(database),
    userModel,
    enrollmentModel: new EnrollmentModel(),
    paymentModel: new PaymentModel(),
    auditModel: new AuditModel(),
    paymentGateway: new FakePaymentGateway({ apiKey: config.paymentGatewayKey, logger }),
    cache: new BoundedCache({ logger }),
    hashPassword,
  });
  const reportService = new ReportService({ reportModel: new ReportModel(database) });
  const userService = new UserService({ database, userModel });

  const app = express();
  app.use(express.json());
  app.use(buildRoutes({
    checkoutController: new CheckoutController(checkoutService),
    reportController: new ReportController(reportService),
    userController: new UserController(userService),
    requireAdmin: requireAdmin(config.adminToken),
  }));
  app.use(errorHandler(logger));
  return app;
}

async function start() {
  const config = loadConfig();
  const logger = createLogger(config.logLevel);

  const database = await Database.open(config.databaseFile, {
    verbose: config.sqliteVerbose,
    logger,
  });
  await initSchema(database);
  await seed(database, { hashPassword, seedUserPassword: config.seedUserPassword });

  if (!config.adminToken) {
    logger.warn('ADMIN_TOKEN não definido: rotas administrativas responderão 401');
  }

  createApp({ config, database, logger }).listen(config.port, () => {
    logger.info(`LMS API rodando na porta ${config.port}`);
  });
}

if (require.main === module) {
  start().catch((err) => {
    console.error(err);
    process.exit(1);
  });
}

module.exports = { createApp, start };
