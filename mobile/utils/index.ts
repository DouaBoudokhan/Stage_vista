// Common utility formatting helpers

export const formatCurrency = (value: number): string => {
  return `€${value.toLocaleString()}`;
};

export const formatDate = (dateString: string): string => {
  return new Date(dateString).toLocaleDateString();
};

export const getStatusColor = (status: string): string => {
  switch (status) {
    case 'In Stock':
      return '#10B981';
    case 'Low Stock':
      return '#F59E0B';
    case 'Out of Stock':
      return '#EF4444';
    default:
      return '#64748B';
  }
};
