import React, { useEffect } from 'react';
import styled from 'styled-components';
import { Icon } from '@iconify/react';
import { useServices } from '../context/ServiceContext';

const HeaderContainer = styled.header`
  background: white;
  border-bottom: 1px solid #e2e8f0;
  padding: 16px 24px;
  display: flex;
  justify-content: space-between;
  align-items: center;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.1);
`;

const PageTitle = styled.h1`
  font-size: 24px;
  font-weight: 700;
  color: #1e293b;
  margin: 0;
`;

const HeaderActions = styled.div`
  display: flex;
  align-items: center;
  gap: 16px;
`;

const ServiceStatusContainer = styled.div`
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 8px 16px;
  background-color: #f8fafc;
  border-radius: 8px;
  border: 1px solid #e2e8f0;
`;

const ServiceStatus = styled.div`
  display: flex;
  align-items: center;
  gap: 6px;
  font-size: 14px;
  font-weight: 500;
  
  .status-dot {
    width: 8px;
    height: 8px;
    border-radius: 50%;
    background-color: ${props => {
      switch (props.$status) {
        case 'healthy': return '#10b981';
        case 'unhealthy': return '#ef4444';
        case 'unknown': return '#f59e0b';
        default: return '#6b7280';
      }
    }};
  }
  
  .status-text {
    color: ${props => {
      switch (props.$status) {
        case 'healthy': return '#059669';
        case 'unhealthy': return '#dc2626';
        case 'unknown': return '#d97706';
        default: return '#4b5563';
      }
    }};
  }
`;

const RefreshButton = styled.button`
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 8px 16px;
  background-color: #3b82f6;
  color: white;
  border: none;
  border-radius: 6px;
  font-weight: 500;
  cursor: pointer;
  transition: all 0.2s ease;
  
  &:hover {
    background-color: #2563eb;
  }
  
  &:disabled {
    background-color: #9ca3af;
    cursor: not-allowed;
  }
  
  .refresh-icon {
    font-size: 16px;
    animation: ${props => props.$loading ? 'spin 1s linear infinite' : 'none'};
  }
  
  @keyframes spin {
    from { transform: rotate(0deg); }
    to { transform: rotate(360deg); }
  }
`;

const TimeStamp = styled.div`
  font-size: 12px;
  color: #64748b;
  font-weight: 500;
`;

const Header = () => {
  const { serviceStatus, loading, checkAllServicesHealth } = useServices();
  
  useEffect(() => {
    // Initial health check
    checkAllServicesHealth();
    
    // Set up periodic health checks every 30 seconds
    const interval = setInterval(checkAllServicesHealth, 30000);
    
    return () => clearInterval(interval);
  }, [checkAllServicesHealth]);
  
  const getOverallStatus = () => {
    const services = Object.values(serviceStatus);
    if (services.length === 0) return 'unknown';
    
    const healthyServices = services.filter(service => service.success && service.data?.status === 'healthy');
    
    if (healthyServices.length === services.length) return 'healthy';
    if (healthyServices.length === 0) return 'unhealthy';
    return 'partial';
  };
  
  const getStatusText = (status) => {
    switch (status) {
      case 'healthy': return 'All Services Online';
      case 'unhealthy': return 'Services Offline';
      case 'partial': return 'Some Services Offline';
      default: return 'Checking Services...';
    }
  };
  
  const overallStatus = getOverallStatus();
  const healthyCount = Object.values(serviceStatus).filter(service => 
    service.success && service.data?.status === 'healthy'
  ).length;
  const totalCount = Object.keys(serviceStatus).length;
  
  return (
    <HeaderContainer>
      <PageTitle>Kafka E-commerce Backend Testing Dashboard</PageTitle>
      
      <HeaderActions>
        <ServiceStatusContainer>
          <ServiceStatus $status={overallStatus}>
            <div className="status-dot"></div>
            <span className="status-text">
              {getStatusText(overallStatus)} ({healthyCount}/{totalCount})
            </span>
          </ServiceStatus>
        </ServiceStatusContainer>
        
        <RefreshButton 
          onClick={checkAllServicesHealth}
          disabled={loading}
          $loading={loading}
        >
          <Icon icon="mdi:refresh" className="refresh-icon" />
          {loading ? 'Checking...' : 'Refresh'}
        </RefreshButton>
        
        <TimeStamp>
          Last updated: {new Date().toLocaleTimeString()}
        </TimeStamp>
      </HeaderActions>
    </HeaderContainer>
  );
};

export default Header;