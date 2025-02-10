"use strict";
Object.defineProperty(exports, "__esModule", { value: true });
exports.convertToCSV = exports.formatDate = exports.formatCurrency = exports.formatPercentage = exports.formatNumber = void 0;
const formatNumber = (num) => {
    return new Intl.NumberFormat('en-US', {
        minimumFractionDigits: 0,
        maximumFractionDigits: 2
    }).format(num);
};
exports.formatNumber = formatNumber;
const formatPercentage = (num) => {
    return new Intl.NumberFormat('en-US', {
        style: 'percent',
        minimumFractionDigits: 2,
        maximumFractionDigits: 2
    }).format(num / 100);
};
exports.formatPercentage = formatPercentage;
const formatCurrency = (num) => {
    return new Intl.NumberFormat('en-US', {
        style: 'currency',
        currency: 'USD',
        minimumFractionDigits: 2,
        maximumFractionDigits: 2
    }).format(num);
};
exports.formatCurrency = formatCurrency;
const formatDate = (date) => {
    return date.toLocaleDateString();
};
exports.formatDate = formatDate;
const convertToCSV = (data) => {
    if (data.length === 0)
        return '';
    const headers = Object.keys(data[0]);
    const rows = data.map(obj => headers.map(header => obj[header]));
    return [headers.join(','), ...rows.map(row => row.join(','))].join('\n');
};
exports.convertToCSV = convertToCSV;
