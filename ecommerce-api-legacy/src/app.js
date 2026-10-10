const express = require('express');
const config = require('./config');
const logger = require('./config/logger');
const { initializeDatabase, createTransactionRunner } = require('./models/database');
const CourseModel = require('./models/course.model');
const UserModel = require('./models/user.model');
const EnrollmentModel = require('./models/enrollment.model');
const ReportModel = require('./models/report.model');
const FakePaymentGateway = require('./services/payment.gateway');
const InMemoryCache = require('./services/cache');
const CheckoutService = require('./services/checkout.service');
const ReportService = require('./services/report.service');
const UserService = require('./services/user.service');
const CheckoutController = require('./controllers/checkout.controller');
const ReportController = require('./controllers/report.controller');
const UserController = require('./controllers/user.controller');
const buildRoutes = require('./views/routes');
const errorHandler = require('./middlewares/errorHandler');

// Composition root: cria as dependências concretas, injeta-as e monta o app.
function createApp({ db }) {
    const withTransaction = createTransactionRunner(db);

    const courseModel = new CourseModel(db);
    const userModel = new UserModel({ db, withTransaction });
    const enrollmentModel = new EnrollmentModel({ db, withTransaction });
    const reportModel = new ReportModel(db);

    const checkoutService = new CheckoutService({
        courseModel,
        userModel,
        enrollmentModel,
        paymentGateway: new FakePaymentGateway({ apiKey: config.paymentGatewayKey }),
        cache: new InMemoryCache(),
    });
    const reportService = new ReportService({ reportModel });
    const userService = new UserService({ userModel });

    const app = express();
    app.use(express.json());
    app.use(
        buildRoutes({
            checkoutController: new CheckoutController(checkoutService),
            reportController: new ReportController(reportService),
            userController: new UserController(userService),
            adminToken: config.adminToken,
        }),
    );
    app.use(errorHandler);
    return app;
}

async function main() {
    const db = await initializeDatabase(config.databaseFile);
    createApp({ db }).listen(config.port, () => {
        logger.info('Frankenstein LMS rodando', { port: config.port });
    });
}

if (require.main === module) {
    main().catch((err) => {
        logger.error('Falha ao iniciar a aplicação', { error: err.message });
        process.exit(1);
    });
}

module.exports = { createApp };
