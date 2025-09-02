import React from 'react';
import { Link, useLocation } from 'react-router-dom';
import styled from 'styled-components';
import { Icon } from '@iconify/react';

const SidebarContainer = styled.div`
  position: fixed;
  left: 0;
  top: 0;
  width: 280px;
  height: 100vh;
  background: linear-gradient(180deg, #1e293b 0%, #0f172a 100%);
  color: white;
  display: flex;
  flex-direction: column;
  z-index: 1000;
  box-shadow: 4px 0 20px rgba(0, 0, 0, 0.1);
`;

const Logo = styled.div`
  padding: 24px;
  border-bottom: 1px solid #334155;
  display: flex;
  align-items: center;
  gap: 12px;
  
  h1 {
    font-size: 20px;
    font-weight: 700;
    color: #f1f5f9;
    margin: 0;
  }
  
  .logo-icon {
    font-size: 32px;
    color: #3b82f6;
  }
`;

const Navigation = styled.nav`
  flex: 1;
  padding: 24px 0;
`;

const NavSection = styled.div`
  margin-bottom: 32px;
  
  &:last-child {
    margin-bottom: 0;
  }
`;

const SectionTitle = styled.h3`
  font-size: 12px;
  font-weight: 600;
  color: #64748b;
  text-transform: uppercase;
  letter-spacing: 0.5px;
  margin: 0 0 12px 24px;
`;

const NavItem = styled(Link)`
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 12px 24px;
  color: ${props => props.$active ? '#3b82f6' : '#cbd5e1'};
  text-decoration: none;
  font-weight: ${props => props.$active ? '600' : '500'};
  background-color: ${props => props.$active ? 'rgba(59, 130, 246, 0.1)' : 'transparent'};
  border-right: ${props => props.$active ? '3px solid #3b82f6' : '3px solid transparent'};
  transition: all 0.2s ease;
  
  &:hover {
    background-color: rgba(59, 130, 246, 0.1);
    color: #3b82f6;
  }
  
  .nav-icon {
    font-size: 20px;
    flex-shrink: 0;
  }
`;

const StatusIndicator = styled.div`
  margin: 24px;
  padding: 16px;
  background-color: rgba(15, 23, 42, 0.5);
  border-radius: 8px;
  border: 1px solid #334155;
  
  .status-title {
    font-size: 12px;
    font-weight: 600;
    color: #64748b;
    text-transform: uppercase;
    letter-spacing: 0.5px;
    margin-bottom: 8px;
  }
  
  .status-item {
    display: flex;
    align-items: center;
    justify-content: space-between;
    padding: 4px 0;
    font-size: 14px;
    
    .service-name {
      color: #cbd5e1;
    }
    
    .status-dot {
      width: 8px;
      height: 8px;
      border-radius: 50%;
      background-color: #10b981;
    }
  }
`;

const Sidebar = () => {
  const location = useLocation();
  
  const navigationItems = [
    {
      section: 'Overview',
      items: [
        { path: '/', label: 'Dashboard', icon: 'mdi:view-dashboard' }
      ]
    },
    {
      section: 'Services',
      items: [
        { path: '/orders', label: 'Order Service', icon: 'mdi:shopping' },
        { path: '/payments', label: 'Payment Service', icon: 'mdi:credit-card' },
        { path: '/inventory', label: 'Inventory Service', icon: 'mdi:package-variant' },
        { path: '/notifications', label: 'Notification Service', icon: 'mdi:bell' },
        { path: '/orchestrator', label: 'Orchestrator Service', icon: 'mdi:workflow' }
      ]
    },
    {
      section: 'Monitoring',
      items: [
        { path: '/monitoring', label: 'System Monitoring', icon: 'mdi:monitor-dashboard' }
      ]
    }
  ];

  return (
    <SidebarContainer>
      <Logo>
        <Icon icon="mdi:apache-kafka" className="logo-icon" />
        <h1>E-commerce Dashboard</h1>
      </Logo>
      
      <Navigation>
        {navigationItems.map((section, index) => (
          <NavSection key={index}>
            <SectionTitle>{section.section}</SectionTitle>
            {section.items.map((item) => (
              <NavItem
                key={item.path}
                to={item.path}
                $active={location.pathname === item.path}
              >
                <Icon icon={item.icon} className="nav-icon" />
                {item.label}
              </NavItem>
            ))}
          </NavSection>
        ))}
      </Navigation>
      
      <StatusIndicator>
        <div className="status-title">Quick Status</div>
        <div className="status-item">
          <span className="service-name">All Services</span>
          <div className="status-dot"></div>
        </div>
        <div className="status-item">
          <span className="service-name">Kafka</span>
          <div className="status-dot"></div>
        </div>
      </StatusIndicator>
    </SidebarContainer>
  );
};

export default Sidebar;