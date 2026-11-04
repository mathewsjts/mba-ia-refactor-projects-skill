const crypto = require('node:crypto');
const express = require('express');

const { loadConfig } = require('./config');
const logger = require('./config/logger');
const { openDatabase, initSchema, seedDatabase } = require('./models/database');
const UserModel = require('./models/user.model');
const CourseModel = require('./models/course.model');
const EnrollmentModel = require('./models/enrollment.model');
const { PaymentModel } = require('./models/payment.model');
const AuditModel = require('./models/audit.model');
const ReportModel = require('./models/report.model');
const { hashPassword } = require('./services/password');
const FakePaymentGateway = require('./services/payment.gateway');
const InMemoryCache = require('./services/cache');
const CheckoutService = require('./services/checkout.service');
const ReportService = require('./services/report.service');
const UserService = require('./services/user.service');
const CheckoutController = require('./controllers/checkout.controller');
const ReportController = require('./controllers/report.controller');
const UserController = require('./controllers/user.controller');
const buildRoutes = require('./views/routes');
const buildRequireAdmin = require('./middlewares/requireAdmin');
const buildErrorHandler = require('./middlewares/errorHandler');

// Composition root: único lugar que conhece as implementações concretas.
function createApp({ config, database }) {
  const userModel = new UserModel(database);
  const reportModel = new ReportModel(database);

  const checkoutService = new CheckoutService({
    transaction: database.transaction,
    userModel,
    courseModel: new CourseModel(database),
    enrollmentModel: new EnrollmentModel(database),
    paymentModel: new PaymentModel(database),
    auditModel: new AuditModel(database),
    paymentGateway: new FakePaymentGateway({ apiKey: config.paymentGatewayKey, logger }),
    cache: new InMemoryCache({ logger }),
    hashPassword,
  });

  const app = express();
  app.use(express.json());
  app.use(buildRoutes({
    checkoutController: new CheckoutController({ checkoutService }),
    reportController: new ReportController({ reportService: new ReportService({ reportModel }) }),
    userController: new UserController({ userService: new UserService({ userModel }) }),
    requireAdmin: buildRequireAdmin(config),
  }));
  app.use(buildErrorHandler({ logger }));
  return app;
}

async function main() {
  const config = loadConfig();
  if (!config.adminTokenConfigured) {
    logger.warn('ADMIN_TOKEN não definido: rotas administrativas recusarão todas as requisições');
  }

  const database = openDatabase(config.databaseFile);
  initSchema(database);
  // O usuário do seed nunca faz login; a senha dele é aleatória, gravada só como hash.
  seedDatabase(database, { seedUserPasswordHash: await hashPassword(crypto.randomBytes(16).toString('hex')) });

  createApp({ config, database }).listen(config.port, () => {
    logger.info('LMS API iniciada', { port: config.port });
  });
}

if (require.main === module) {
  main().catch((err) => {
    logger.error('Falha ao iniciar a aplicação', { error: err.message, stack: err.stack });
    process.exit(1);
  });
}

module.exports = { createApp };
