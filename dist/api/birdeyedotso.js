"use strict";
var __importDefault = (this && this.__importDefault) || function (mod) {
    return (mod && mod.__esModule) ? mod : { "default": mod };
};
Object.defineProperty(exports, "__esModule", { value: true });
const axios_1 = __importDefault(require("axios"));
const env_1 = require("../config/env");
const birdeyedotso = axios_1.default.create({
    baseURL: 'https://public-api.birdeye.so/v1',
    headers: {
        'x-api-key': env_1.env.BIRDEYE_API_KEY,
        'Accept': 'application/json',
        'Content-Type': 'application/json'
    }
});
// Add response interceptor for better error handling
birdeyedotso.interceptors.response.use(response => response, error => {
    console.error('Birdeye API error:', {
        status: error.response?.status,
        data: error.response?.data,
        config: {
            url: error.config?.url,
            method: error.config?.method
        }
    });
    return Promise.reject(error);
});
exports.default = birdeyedotso;
