"use strict";
Object.defineProperty(exports, "__esModule", { value: true });
exports.convertToCSV = exports.formatDate = exports.formatNumber = void 0;
const formatNumber = (num) => {
    return new Intl.NumberFormat().format(num);
};
exports.formatNumber = formatNumber;
const formatDate = (date) => {
    return date.toLocaleDateString();
};
exports.formatDate = formatDate;
const convertToCSV = (data) => {
    if (data.length === 0)
        return '';
    const headers = Object.keys(data[0]);
    const rows = data.map(obj => headers.map(header => obj[header]));
    return [
        headers.join(','),
        ...rows.map(row => row.join(','))
    ].join('\n');
};
exports.convertToCSV = convertToCSV;
