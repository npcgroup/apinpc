export const formatNumber = (num: number): string => {
  return new Intl.NumberFormat('en-US', {
    notation: 'compact',
    maximumFractionDigits: 2
  }).format(num);
};

export const formatDate = (date: Date): string => {
  return new Date(date).toLocaleString('en-US', {
    timeZone: 'UTC',
    year: 'numeric',
    month: 'numeric',
    day: 'numeric',
    hour: '2-digit',
    minute: '2-digit'
  });
};

export const formatCurrency = (amount: number): string => {
  return new Intl.NumberFormat('en-US', {
    style: 'currency',
    currency: 'USD'
  }).format(amount);
}; 