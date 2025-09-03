import React, { createContext, useContext, useState, useCallback } from 'react';
import axios from 'axios';
import { toast } from 'react-toastify';

const ServiceContext = createContext();

export const useServices = () => {
  const context = useContext(ServiceContext);
  if (!context) {
    throw new Error('useServices must be used within a ServiceProvider');
  }
  return context;
};

// Service configuration with environment variable support
const BASE_URL = process.env.REACT_APP_API_BASE_URL || 'https://kafka-ecommerce-production-b5e5.up.railway.app';

const SERVICES = {
  order: { 
    port: 5011, 
    name: 'Order Service',
    url: `${BASE_URL}/api/orders`,
    healthUrl: `${BASE_URL}/api/orders/health`
  },
  payment: { 
    port: 6002, 
    name: 'Payment Service',
    url: `${BASE_URL}/api/payments`,
    healthUrl: `${BASE_URL}/api/payments/health`
  },
  inventory: { 
    port: 5003, 
    name: 'Inventory Service',
    url: `${BASE_URL}/api/inventory`,
    healthUrl: `${BASE_URL}/api/inventory/health`
  },
  notification: { 
    port: 5004, 
    name: 'Notification Service',
    url: `${BASE_URL}/api/notifications`,
    healthUrl: `${BASE_URL}/api/notifications/health`
  },
  orchestrator: { 
    port: 5005, 
    name: 'Orchestrator Service',
    url: `${BASE_URL}/api/orchestrator`,
    healthUrl: `${BASE_URL}/api/orchestrator/health`
  },
  monitoring: { 
    port: 5005, 
    name: 'Monitoring Service',
    url: `${BASE_URL}/api/monitoring`,
    healthUrl: `${BASE_URL}/api/monitoring/health`
  }
};

export const ServiceProvider = ({ children }) => {
  const [serviceStatus, setServiceStatus] = useState({});
  const [loading, setLoading] = useState(false);

  // Generic API call function
  const apiCall = useCallback(async (service, endpoint, method = 'GET', data = null) => {
    try {
      setLoading(true);
      const serviceURL = SERVICES[service].url;
      const config = {
        method,
        url: `${serviceURL}${endpoint}`,
        timeout: 10000,
        headers: {
          'Content-Type': 'application/json',
        },
      };

      if (data && (method === 'POST' || method === 'PUT')) {
        config.data = data;
      }

      const response = await axios(config);
      return { success: true, data: response.data, status: response.status };
    } catch (error) {
      const errorMessage = error.response?.data?.error || error.message || 'Unknown error';
      toast.error(`${SERVICES[service].name}: ${errorMessage}`);
      return { 
        success: false, 
        error: errorMessage, 
        status: error.response?.status || 500 
      };
    } finally {
      setLoading(false);
    }
  }, []);

  // Health check for all services
  const checkAllServicesHealth = useCallback(async () => {
    const healthChecks = Object.keys(SERVICES).map(async (service) => {
      try {
        // Use direct health URL for health checks
        const config = {
          method: 'GET',
          url: SERVICES[service].healthUrl,
          timeout: 10000,
          headers: {
            'Content-Type': 'application/json',
          },
        };
        const response = await axios(config);
        return {
          service,
          success: true,
          data: response.data,
          status: response.status,
          name: SERVICES[service].name,
          port: SERVICES[service].port
        };
      } catch (error) {
        return {
          service,
          success: false,
          error: error.response?.data?.error || error.message,
          status: error.response?.status || 500,
          name: SERVICES[service].name,
          port: SERVICES[service].port
        };
      }
    });

    const results = await Promise.all(healthChecks);
    const statusMap = {};
    results.forEach(result => {
      statusMap[result.service] = result;
    });
    setServiceStatus(statusMap);
    return statusMap;
  }, [apiCall]);

  // Order Service APIs
  const orderService = {
    createOrder: (orderData) => apiCall('order', '/orders', 'POST', orderData),
    getOrder: (orderId) => apiCall('order', `/orders/${orderId}`),
    getCustomerOrders: (customerId) => apiCall('order', `/customers/${customerId}/orders`),
    validateOrder: (orderId) => apiCall('order', `/orders/${orderId}/validate`, 'POST'),
    getMetrics: () => apiCall('order', '/metrics')
  };

  // Payment Service APIs
  const paymentService = {
    processPayment: (paymentData) => apiCall('payment', '/payments', 'POST', paymentData),
    getPayment: (paymentId) => apiCall('payment', `/payments/${paymentId}`),
    getOrderPayments: (orderId) => apiCall('payment', `/orders/${orderId}/payments`),
    refundPayment: (paymentId, reason) => apiCall('payment', `/payments/${paymentId}/refund`, 'POST', { reason }),
    getMetrics: () => apiCall('payment', '/metrics')
  };

  // Inventory Service APIs
  const inventoryService = {
    getAllInventory: () => apiCall('inventory', '/inventory'),
    getProductInventory: (productId) => apiCall('inventory', `/inventory/${productId}`),
    updateInventory: (productId, data) => apiCall('inventory', `/inventory/${productId}`, 'PUT', data),
    createReservation: (reservationData) => apiCall('inventory', '/reservations', 'POST', reservationData),
    releaseReservation: (reservationId) => apiCall('inventory', `/reservations/${reservationId}/release`, 'POST'),
    getMetrics: () => apiCall('inventory', '/metrics')
  };

  // Notification Service APIs
  const notificationService = {
    sendNotification: (notificationData) => apiCall('notification', '/notifications', 'POST', notificationData),
    getNotification: (notificationId) => apiCall('notification', `/notifications/${notificationId}`),
    getRecipientNotifications: (recipient) => apiCall('notification', `/recipients/${recipient}/notifications`),
    getTemplates: () => apiCall('notification', '/templates'),
    getMetrics: () => apiCall('notification', '/metrics')
  };

  // Monitoring Service APIs
  const monitoringService = {
    getServicesHealth: () => apiCall('monitoring', '/services/health'),
    getKafkaMetrics: () => apiCall('monitoring', '/metrics/kafka'),
    getOrderMetrics: () => apiCall('monitoring', '/metrics/orders'),
    getSystemMetrics: () => apiCall('monitoring', '/metrics/system'),
    getPrometheusMetrics: () => apiCall('monitoring', '/metrics/prometheus'),
    getAlerts: () => apiCall('monitoring', '/alerts'),
    resolveAlert: (alertId) => apiCall('monitoring', `/alerts/${alertId}/resolve`, 'POST'),
    getDashboard: () => apiCall('monitoring', '/dashboard')
  };

  // Orchestrator Service APIs
  const orchestratorService = {
    getOrderFlow: (orderId) => apiCall('orchestrator', `/flows/${orderId}`),
    getAllFlows: () => apiCall('orchestrator', '/flows'),
    getMetrics: () => apiCall('orchestrator', '/metrics')
  };

  const value = {
    serviceStatus,
    loading,
    checkAllServicesHealth,
    orderService,
    paymentService,
    inventoryService,
    notificationService,
    monitoringService,
    orchestratorService,
    SERVICES
  };

  return (
    <ServiceContext.Provider value={value}>
      {children}
    </ServiceContext.Provider>
  );
};