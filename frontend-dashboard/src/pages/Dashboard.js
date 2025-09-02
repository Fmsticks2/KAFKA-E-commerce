import React, { useEffect, useState } from 'react';
import styled from 'styled-components';
import { Icon } from '@iconify/react';
import { useServices } from '../context/ServiceContext';

const DashboardContainer = styled.div`
  display: flex;
  flex-direction: column;
  gap: 24px;
`;

const StatsGrid = styled.div`
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(280px, 1fr));
  gap: 20px;
  margin-bottom: 24px;
`;

const StatCard = styled.div`
  background: white;
  border-radius: 12px;
  padding: 24px;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.1);
  border: 1px solid #e2e8f0;
  transition: all 0.2s ease;
  
  &:hover {
    box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
  }
`;

const StatHeader = styled.div`
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 16px;
  
  .stat-title {
    font-size: 14px;
    font-weight: 600;
    color: #64748b;
    text-transform: uppercase;
    letter-spacing: 0.5px;
  }
  
  .stat-icon {
    font-size: 24px;
    color: #3b82f6;
  }
`;

const StatValue = styled.div`
  font-size: 32px;
  font-weight: 700;
  color: #1e293b;
  margin-bottom: 8px;
`;

const StatDescription = styled.div`
  font-size: 14px;
  color: #64748b;
`;

const ServicesGrid = styled.div`
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(350px, 1fr));
  gap: 20px;
`;

const ServiceCard = styled.div`
  background: white;
  border-radius: 12px;
  padding: 24px;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.1);
  border: 1px solid #e2e8f0;
  transition: all 0.2s ease;
  
  &:hover {
    box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
  }
`;

const ServiceHeader = styled.div`
  display: flex;
  align-items: center;
  justify-content: between;
  margin-bottom: 16px;
  
  .service-info {
    flex: 1;
    
    .service-name {
      font-size: 18px;
      font-weight: 600;
      color: #1e293b;
      margin-bottom: 4px;
    }
    
    .service-port {
      font-size: 14px;
      color: #64748b;
    }
  }
  
  .service-status {
    display: flex;
    align-items: center;
    gap: 8px;
    
    .status-dot {
      width: 12px;
      height: 12px;
      border-radius: 50%;
      background-color: ${props => {
        switch (props.$status) {
          case 'healthy': return '#10b981';
          case 'unhealthy': return '#ef4444';
          default: return '#f59e0b';
        }
      }};
    }
    
    .status-text {
      font-size: 14px;
      font-weight: 500;
      color: ${props => {
        switch (props.$status) {
          case 'healthy': return '#059669';
          case 'unhealthy': return '#dc2626';
          default: return '#d97706';
        }
      }};
    }
  }
`;

const ServiceMetrics = styled.div`
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 16px;
  
  .metric {
    .metric-label {
      font-size: 12px;
      color: #64748b;
      margin-bottom: 4px;
    }
    
    .metric-value {
      font-size: 16px;
      font-weight: 600;
      color: #1e293b;
    }
  }
`;

const QuickActions = styled.div`
  background: white;
  border-radius: 12px;
  padding: 24px;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.1);
  border: 1px solid #e2e8f0;
  
  .actions-title {
    font-size: 18px;
    font-weight: 600;
    color: #1e293b;
    margin-bottom: 16px;
  }
  
  .actions-grid {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
    gap: 12px;
  }
`;

const ActionButton = styled.button`
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 12px 16px;
  background-color: #f8fafc;
  border: 1px solid #e2e8f0;
  border-radius: 8px;
  color: #475569;
  font-weight: 500;
  cursor: pointer;
  transition: all 0.2s ease;
  
  &:hover {
    background-color: #3b82f6;
    color: white;
    border-color: #3b82f6;
  }
  
  .action-icon {
    font-size: 16px;
  }
`;

const Dashboard = () => {
  const { serviceStatus, checkAllServicesHealth, SERVICES } = useServices();
  const [systemMetrics, setSystemMetrics] = useState({
    totalRequests: 0,
    activeOrders: 0,
    totalRevenue: 0,
    errorRate: 0
  });

  useEffect(() => {
    checkAllServicesHealth();
    
    // Simulate some metrics (in real app, these would come from monitoring service)
    setSystemMetrics({
      totalRequests: Math.floor(Math.random() * 10000) + 5000,
      activeOrders: Math.floor(Math.random() * 100) + 50,
      totalRevenue: Math.floor(Math.random() * 50000) + 25000,
      errorRate: (Math.random() * 5).toFixed(2)
    });
  }, [checkAllServicesHealth]);

  const getServiceStatus = (service) => {
    const status = serviceStatus[service];
    if (!status) return 'unknown';
    if (status.success && status.data?.status === 'healthy') return 'healthy';
    return 'unhealthy';
  };

  const getServiceResponseTime = (service) => {
    const status = serviceStatus[service];
    if (!status || !status.success) return 'N/A';
    return status.data?.response_time ? `${(status.data.response_time * 1000).toFixed(0)}ms` : 'N/A';
  };

  const quickActions = [
    { label: 'Create Test Order', icon: 'mdi:plus-circle', action: () => window.location.href = '/orders' },
    { label: 'Process Payment', icon: 'mdi:credit-card-plus', action: () => window.location.href = '/payments' },
    { label: 'Check Inventory', icon: 'mdi:package-variant', action: () => window.location.href = '/inventory' },
    { label: 'Send Notification', icon: 'mdi:bell-plus', action: () => window.location.href = '/notifications' },
    { label: 'View Monitoring', icon: 'mdi:monitor-dashboard', action: () => window.location.href = '/monitoring' },
    { label: 'Check Flows', icon: 'mdi:workflow', action: () => window.location.href = '/orchestrator' }
  ];

  return (
    <DashboardContainer>
      <StatsGrid>
        <StatCard>
          <StatHeader>
            <span className="stat-title">Total Requests</span>
            <Icon icon="mdi:chart-line" className="stat-icon" />
          </StatHeader>
          <StatValue>{systemMetrics.totalRequests.toLocaleString()}</StatValue>
          <StatDescription>Requests processed today</StatDescription>
        </StatCard>
        
        <StatCard>
          <StatHeader>
            <span className="stat-title">Active Orders</span>
            <Icon icon="mdi:shopping" className="stat-icon" />
          </StatHeader>
          <StatValue>{systemMetrics.activeOrders}</StatValue>
          <StatDescription>Orders being processed</StatDescription>
        </StatCard>
        
        <StatCard>
          <StatHeader>
            <span className="stat-title">Total Revenue</span>
            <Icon icon="mdi:currency-usd" className="stat-icon" />
          </StatHeader>
          <StatValue>${systemMetrics.totalRevenue.toLocaleString()}</StatValue>
          <StatDescription>Revenue generated today</StatDescription>
        </StatCard>
        
        <StatCard>
          <StatHeader>
            <span className="stat-title">Error Rate</span>
            <Icon icon="mdi:alert-circle" className="stat-icon" />
          </StatHeader>
          <StatValue>{systemMetrics.errorRate}%</StatValue>
          <StatDescription>System error rate</StatDescription>
        </StatCard>
      </StatsGrid>

      <ServicesGrid>
        {Object.entries(SERVICES).map(([serviceKey, service]) => {
          const status = getServiceStatus(serviceKey);
          return (
            <ServiceCard key={serviceKey}>
              <ServiceHeader $status={status}>
                <div className="service-info">
                  <div className="service-name">{service.name}</div>
                  <div className="service-port">Port: {service.port}</div>
                </div>
                <div className="service-status">
                  <div className="status-dot"></div>
                  <span className="status-text">
                    {status === 'healthy' ? 'Online' : status === 'unhealthy' ? 'Offline' : 'Unknown'}
                  </span>
                </div>
              </ServiceHeader>
              
              <ServiceMetrics>
                <div className="metric">
                  <div className="metric-label">Response Time</div>
                  <div className="metric-value">{getServiceResponseTime(serviceKey)}</div>
                </div>
                <div className="metric">
                  <div className="metric-label">Last Check</div>
                  <div className="metric-value">{new Date().toLocaleTimeString()}</div>
                </div>
              </ServiceMetrics>
            </ServiceCard>
          );
        })}
      </ServicesGrid>

      <QuickActions>
        <div className="actions-title">Quick Actions</div>
        <div className="actions-grid">
          {quickActions.map((action, index) => (
            <ActionButton key={index} onClick={action.action}>
              <Icon icon={action.icon} className="action-icon" />
              {action.label}
            </ActionButton>
          ))}
        </div>
      </QuickActions>
    </DashboardContainer>
  );
};

export default Dashboard;