import React, { useState } from 'react';
import styled from 'styled-components';
import { Icon } from '@iconify/react';
import { toast } from 'react-toastify';
import { useServices } from '../context/ServiceContext';

const PageContainer = styled.div`
  display: flex;
  flex-direction: column;
  gap: 24px;
`;

const PageHeader = styled.div`
  .page-title {
    font-size: 28px;
    font-weight: 700;
    color: #1e293b;
    margin-bottom: 8px;
  }
  
  .page-description {
    font-size: 16px;
    color: #64748b;
  }
`;

const ActionsGrid = styled.div`
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(400px, 1fr));
  gap: 24px;
`;

const ActionCard = styled.div`
  background: white;
  border-radius: 12px;
  padding: 24px;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.1);
  border: 1px solid #e2e8f0;
`;

const CardHeader = styled.div`
  display: flex;
  align-items: center;
  gap: 12px;
  margin-bottom: 20px;
  
  .card-icon {
    font-size: 24px;
    color: #dc2626;
  }
  
  .card-title {
    font-size: 18px;
    font-weight: 600;
    color: #1e293b;
  }
`;

const Form = styled.form`
  display: flex;
  flex-direction: column;
  gap: 16px;
`;

const FormGroup = styled.div`
  display: flex;
  flex-direction: column;
  gap: 6px;
  
  label {
    font-size: 14px;
    font-weight: 500;
    color: #374151;
  }
`;

const Input = styled.input`
  padding: 10px 12px;
  border: 1px solid #d1d5db;
  border-radius: 6px;
  font-size: 14px;
  transition: border-color 0.2s ease;
  
  &:focus {
    outline: none;
    border-color: #dc2626;
    box-shadow: 0 0 0 3px rgba(220, 38, 38, 0.1);
  }
`;

const Button = styled.button`
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 8px;
  padding: 12px 20px;
  background-color: #dc2626;
  color: white;
  border: none;
  border-radius: 6px;
  font-weight: 500;
  cursor: pointer;
  transition: all 0.2s ease;
  
  &:hover {
    background-color: #b91c1c;
  }
  
  &:disabled {
    background-color: #9ca3af;
    cursor: not-allowed;
  }
  
  .button-icon {
    font-size: 16px;
  }
`;

const SuccessButton = styled(Button)`
  background-color: #10b981;
  
  &:hover {
    background-color: #059669;
  }
`;

const ResultContainer = styled.div`
  margin-top: 16px;
  padding: 16px;
  background-color: #f8fafc;
  border-radius: 6px;
  border: 1px solid #e2e8f0;
  
  .result-title {
    font-size: 14px;
    font-weight: 600;
    color: #374151;
    margin-bottom: 8px;
  }
  
  .result-content {
    font-family: 'Monaco', 'Menlo', monospace;
    font-size: 12px;
    color: #1f2937;
    white-space: pre-wrap;
    background-color: white;
    padding: 12px;
    border-radius: 4px;
    border: 1px solid #e5e7eb;
    max-height: 300px;
    overflow-y: auto;
  }
`;

const MetricsGrid = styled.div`
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
  gap: 16px;
  margin-top: 16px;
`;

const MetricCard = styled.div`
  background: #f8fafc;
  border: 1px solid #e2e8f0;
  border-radius: 8px;
  padding: 16px;
  
  .metric-title {
    font-size: 14px;
    font-weight: 600;
    color: #374151;
    margin-bottom: 8px;
  }
  
  .metric-value {
    font-size: 24px;
    font-weight: 700;
    color: #1f2937;
  }
  
  .metric-description {
    font-size: 12px;
    color: #6b7280;
    margin-top: 4px;
  }
`;

const MonitoringService = () => {
  const { monitoringService, loading } = useServices();
  
  // Services Health State
  const [servicesHealthResult, setServicesHealthResult] = useState(null);
  
  // Kafka Metrics State
  const [kafkaMetricsResult, setKafkaMetricsResult] = useState(null);
  
  // Order Metrics State
  const [orderMetricsResult, setOrderMetricsResult] = useState(null);
  
  // System Metrics State
  const [systemMetricsResult, setSystemMetricsResult] = useState(null);
  
  // Prometheus Metrics State
  const [prometheusMetricsResult, setPrometheusMetricsResult] = useState(null);
  
  // Alerts State
  const [alertsResult, setAlertsResult] = useState(null);
  
  // Resolve Alert State
  const [resolveAlertId, setResolveAlertId] = useState('');
  const [resolveAlertResult, setResolveAlertResult] = useState(null);
  
  // Dashboard State
  const [dashboardResult, setDashboardResult] = useState(null);

  const handleGetServicesHealth = async (e) => {
    e.preventDefault();
    
    const result = await monitoringService.getServicesHealth();
    setServicesHealthResult(result);
    
    if (result.success) {
      toast.success('Services health retrieved successfully!');
    }
  };

  const handleGetKafkaMetrics = async (e) => {
    e.preventDefault();
    
    const result = await monitoringService.getKafkaMetrics();
    setKafkaMetricsResult(result);
    
    if (result.success) {
      toast.success('Kafka metrics retrieved successfully!');
    }
  };

  const handleGetOrderMetrics = async (e) => {
    e.preventDefault();
    
    const result = await monitoringService.getOrderMetrics();
    setOrderMetricsResult(result);
    
    if (result.success) {
      toast.success('Order metrics retrieved successfully!');
    }
  };

  const handleGetSystemMetrics = async (e) => {
    e.preventDefault();
    
    const result = await monitoringService.getSystemMetrics();
    setSystemMetricsResult(result);
    
    if (result.success) {
      toast.success('System metrics retrieved successfully!');
    }
  };

  const handleGetPrometheusMetrics = async (e) => {
    e.preventDefault();
    
    const result = await monitoringService.getPrometheusMetrics();
    setPrometheusMetricsResult(result);
    
    if (result.success) {
      toast.success('Prometheus metrics retrieved successfully!');
    }
  };

  const handleGetAlerts = async (e) => {
    e.preventDefault();
    
    const result = await monitoringService.getAlerts();
    setAlertsResult(result);
    
    if (result.success) {
      toast.success('Alerts retrieved successfully!');
    }
  };

  const handleResolveAlert = async (e) => {
    e.preventDefault();
    
    if (!resolveAlertId) {
      toast.error('Please enter an alert ID');
      return;
    }
    
    const result = await monitoringService.resolveAlert(resolveAlertId);
    setResolveAlertResult(result);
    
    if (result.success) {
      toast.success('Alert resolved successfully!');
      setResolveAlertId('');
    }
  };

  const handleGetDashboard = async (e) => {
    e.preventDefault();
    
    const result = await monitoringService.getDashboard();
    setDashboardResult(result);
    
    if (result.success) {
      toast.success('Dashboard data retrieved successfully!');
    }
  };

  const renderMetrics = (data, title) => {
    if (!data || !data.data) return null;
    
    const metrics = data.data;
    
    return (
      <div>
        <h3 style={{ fontSize: '16px', fontWeight: '600', marginBottom: '12px', color: '#374151' }}>
          {title}
        </h3>
        <MetricsGrid>
          {Object.entries(metrics).map(([key, value]) => (
            <MetricCard key={key}>
              <div className="metric-title">{key.replace(/_/g, ' ').toUpperCase()}</div>
              <div className="metric-value">
                {typeof value === 'number' ? value.toLocaleString() : String(value)}
              </div>
              <div className="metric-description">
                {typeof value === 'number' && value > 1000 ? 'High volume' : 'Current value'}
              </div>
            </MetricCard>
          ))}
        </MetricsGrid>
      </div>
    );
  };

  return (
    <PageContainer>
      <PageHeader>
        <h1 className="page-title">Monitoring Service Dashboard</h1>
        <p className="page-description">
          Monitor system health, view metrics, manage alerts, and access the monitoring dashboard.
        </p>
      </PageHeader>

      <ActionsGrid>
        {/* Services Health */}
        <ActionCard>
          <CardHeader>
            <Icon icon="mdi:heart-pulse" className="card-icon" />
            <h2 className="card-title">Services Health</h2>
          </CardHeader>
          
          <Form onSubmit={handleGetServicesHealth}>
            <Button type="submit" disabled={loading}>
              <Icon icon="mdi:medical-bag" className="button-icon" />
              Check Services Health
            </Button>
          </Form>
          
          {servicesHealthResult && (
            <ResultContainer>
              <div className="result-title">Services Health Status:</div>
              <div className="result-content">{JSON.stringify(servicesHealthResult, null, 2)}</div>
            </ResultContainer>
          )}
        </ActionCard>

        {/* Kafka Metrics */}
        <ActionCard>
          <CardHeader>
            <Icon icon="mdi:chart-line" className="card-icon" />
            <h2 className="card-title">Kafka Metrics</h2>
          </CardHeader>
          
          <Form onSubmit={handleGetKafkaMetrics}>
            <Button type="submit" disabled={loading}>
              <Icon icon="mdi:chart-bar" className="button-icon" />
              Get Kafka Metrics
            </Button>
          </Form>
          
          {kafkaMetricsResult && (
            <ResultContainer>
              <div className="result-title">Kafka Metrics:</div>
              {renderMetrics(kafkaMetricsResult, 'Kafka Performance') || (
                <div className="result-content">{JSON.stringify(kafkaMetricsResult, null, 2)}</div>
              )}
            </ResultContainer>
          )}
        </ActionCard>

        {/* Order Metrics */}
        <ActionCard>
          <CardHeader>
            <Icon icon="mdi:shopping" className="card-icon" />
            <h2 className="card-title">Order Metrics</h2>
          </CardHeader>
          
          <Form onSubmit={handleGetOrderMetrics}>
            <Button type="submit" disabled={loading}>
              <Icon icon="mdi:chart-pie" className="button-icon" />
              Get Order Metrics
            </Button>
          </Form>
          
          {orderMetricsResult && (
            <ResultContainer>
              <div className="result-title">Order Metrics:</div>
              {renderMetrics(orderMetricsResult, 'Order Statistics') || (
                <div className="result-content">{JSON.stringify(orderMetricsResult, null, 2)}</div>
              )}
            </ResultContainer>
          )}
        </ActionCard>

        {/* System Metrics */}
        <ActionCard>
          <CardHeader>
            <Icon icon="mdi:monitor" className="card-icon" />
            <h2 className="card-title">System Metrics</h2>
          </CardHeader>
          
          <Form onSubmit={handleGetSystemMetrics}>
            <Button type="submit" disabled={loading}>
              <Icon icon="mdi:server" className="button-icon" />
              Get System Metrics
            </Button>
          </Form>
          
          {systemMetricsResult && (
            <ResultContainer>
              <div className="result-title">System Metrics:</div>
              {renderMetrics(systemMetricsResult, 'System Performance') || (
                <div className="result-content">{JSON.stringify(systemMetricsResult, null, 2)}</div>
              )}
            </ResultContainer>
          )}
        </ActionCard>

        {/* Prometheus Metrics */}
        <ActionCard>
          <CardHeader>
            <Icon icon="mdi:chart-timeline-variant" className="card-icon" />
            <h2 className="card-title">Prometheus Metrics</h2>
          </CardHeader>
          
          <Form onSubmit={handleGetPrometheusMetrics}>
            <Button type="submit" disabled={loading}>
              <Icon icon="mdi:chart-multiple" className="button-icon" />
              Get Prometheus Metrics
            </Button>
          </Form>
          
          {prometheusMetricsResult && (
            <ResultContainer>
              <div className="result-title">Prometheus Metrics:</div>
              <div className="result-content">{JSON.stringify(prometheusMetricsResult, null, 2)}</div>
            </ResultContainer>
          )}
        </ActionCard>

        {/* Alerts */}
        <ActionCard>
          <CardHeader>
            <Icon icon="mdi:alert" className="card-icon" />
            <h2 className="card-title">System Alerts</h2>
          </CardHeader>
          
          <Form onSubmit={handleGetAlerts}>
            <Button type="submit" disabled={loading}>
              <Icon icon="mdi:bell-alert" className="button-icon" />
              Get All Alerts
            </Button>
          </Form>
          
          {alertsResult && (
            <ResultContainer>
              <div className="result-title">Active Alerts:</div>
              <div className="result-content">{JSON.stringify(alertsResult, null, 2)}</div>
            </ResultContainer>
          )}
        </ActionCard>

        {/* Resolve Alert */}
        <ActionCard>
          <CardHeader>
            <Icon icon="mdi:check-circle" className="card-icon" />
            <h2 className="card-title">Resolve Alert</h2>
          </CardHeader>
          
          <Form onSubmit={handleResolveAlert}>
            <FormGroup>
              <label>Alert ID</label>
              <Input
                type="text"
                value={resolveAlertId}
                onChange={(e) => setResolveAlertId(e.target.value)}
                placeholder="Enter alert ID to resolve"
                required
              />
            </FormGroup>
            
            <SuccessButton type="submit" disabled={loading}>
              <Icon icon="mdi:check" className="button-icon" />
              Resolve Alert
            </SuccessButton>
          </Form>
          
          {resolveAlertResult && (
            <ResultContainer>
              <div className="result-title">Resolution Result:</div>
              <div className="result-content">{JSON.stringify(resolveAlertResult, null, 2)}</div>
            </ResultContainer>
          )}
        </ActionCard>

        {/* Monitoring Dashboard */}
        <ActionCard>
          <CardHeader>
            <Icon icon="mdi:view-dashboard" className="card-icon" />
            <h2 className="card-title">Monitoring Dashboard</h2>
          </CardHeader>
          
          <Form onSubmit={handleGetDashboard}>
            <Button type="submit" disabled={loading}>
              <Icon icon="mdi:dashboard" className="button-icon" />
              Load Dashboard Data
            </Button>
          </Form>
          
          {dashboardResult && (
            <ResultContainer>
              <div className="result-title">Dashboard Overview:</div>
              <div className="result-content">{JSON.stringify(dashboardResult, null, 2)}</div>
            </ResultContainer>
          )}
        </ActionCard>
      </ActionsGrid>
    </PageContainer>
  );
};

export default MonitoringService;