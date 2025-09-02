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
const SERVICES = {
  order: { 
    port: 5011, 
    name: 'Order Service',
    url: process.env.REACT_APP_ORDER_SERVICE_URL || 'http://localhost:5011'
  },
  payment: { 
    port: 6002, 
    name: 'Payment Service',
    url: process.env.REACT_APP_PAYMENT_SERVICE_URL || 'http://localhost:6002'
  },
  inventory: { 
    port: 5003, 
    name: 'Inventory Service',
    url: process.env.REACT_APP_INVENTORY_SERVICE_URL || 'http://localhost:5003'
  },
  notification: { 
    port: 5004, 
    name: 'Notification Service',
    url: process.env.REACT_APP_NOTIFICATION_SERVICE_URL || 'http://localhost:5004'
  },
  orchestrator: { 
    port: 5005, 
    name: 'Orchestrator Service',
    url: process.env.REACT_APP_ORCHESTRATOR_SERVICE_URL || 'http://localhost:5005'
  },
  monitoring: { 
    port: 5005, 
    name: 'Monitoring Service',
    url: process.env.REACT_APP_MONITORING_SERVICE_URL || 'http://localhost:5005'
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
        const result = await apiCall(service, '/health');
        return {
          service,
          ...result,
          name: SERVICES[service].name,
          port: SERVICES[service].port
        };
      } catch (error) {
        return {
          service,
          success: false,
          error: error.message,
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