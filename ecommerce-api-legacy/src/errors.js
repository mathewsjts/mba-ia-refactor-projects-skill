// Erros de domínio (módulo neutro, importado por services, controllers e middlewares).
class AppError extends Error {
    constructor(message, statusCode = 500) {
        super(message);
        this.statusCode = statusCode;
    }
}

class NotFoundError extends AppError {
    constructor(message) {
        super(message, 404);
    }
}

class ValidationError extends AppError {
    constructor(message) {
        super(message, 400);
    }
}

module.exports = { AppError, NotFoundError, ValidationError };
