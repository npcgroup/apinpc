"use strict";
Object.defineProperty(exports, "__esModule", { value: true });
exports.APIError = exports.DataIngestionError = exports.ValidationError = void 0;
class ValidationError extends Error {
    constructor(message) {
        super(message);
        this.name = 'ValidationError';
    }
}
exports.ValidationError = ValidationError;
class DataIngestionError extends Error {
    constructor(message) {
        super(message);
        this.name = 'DataIngestionError';
    }
}
exports.DataIngestionError = DataIngestionError;
class APIError extends Error {
    constructor(message) {
        super(message);
        this.name = 'APIError';
    }
}
exports.APIError = APIError;
