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
    color: #6366f1;
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
    border-color: #6366f1;
    box-shadow: 0 0 0 3px rgba(99, 102, 241, 0.1);
  }
`;

const Button = styled.button`
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 8px;
  padding: 12px 20px;
  background-color: #6366f1;
  color: white;
  border: none;
  border-radius: 6px;
  font-weight: 500;
  cursor: pointer;
  transition: all 0.2s ease;
  
  &:hover {
    background-color: #4f46e5;
  }
  
  &:disabled {
    background-color: #9ca3af;
    cursor: not-allowed;
  }
  
  .button-icon {
    font-size: 16px;
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
    max-height: 400px;
    overflow-y: auto;
  }
`;

const FlowVisualization = styled.div`
  margin-top: 16px;
  padding: 20px;
  background: linear-gradient(135deg, #f8fafc 0%, #e2e8f0 100%);
  border-radius: 8px;
  border: 1px solid #cbd5e1;
`;

const FlowStep = styled.div`
  display: flex;
  align-items: center;
  margin-bottom: 16px;
  padding: 12px;
  background: white;
  border-radius: 6px;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.1);
  
  &:last-child {
    margin-bottom: 0;
  }
  
  .step-icon {
    font-size: 20px;
    margin-right: 12px;
    color: ${props => {
      switch (props.status) {
        case 'completed': return '#10b981';
        case 'in_progress': return '#f59e0b';
        case 'failed': return '#ef4444';
        default: return '#6b7280';
      }
    }};
  }
  
  .step-content {
    flex: 1;
    
    .step-title {
      font-size: 14px;
      font-weight: 600;
      color: #1f2937;
      margin-bottom: 4px;
    }
    
    .step-description {
      font-size: 12px;
      color: #6b7280;
    }
    
    .step-timestamp {
      font-size: 11px;
      color: #9ca3af;
      margin-top: 4px;
    }
  }
  
  .step-status {
    padding: 4px 8px;
    border-radius: 4px;
    font-size: 11px;
    font-weight: 500;
    text-transform: uppercase;
    background-color: ${props => {
      switch (props.status) {
        case 'completed': return '#d1fae5';
        case 'in_progress': return '#fef3c7';
        case 'failed': return '#fee2e2';
        default: return '#f3f4f6';
      }
    }};
    color: ${props => {
      switch (props.status) {
        case 'completed': return '#065f46';
        case 'in_progress': return '#92400e';
        case 'failed': return '#991b1b';
        default: return '#374151';
      }
    }};
  }
`;

const OrchestratorService = () => {
  const { orchestratorService, loading } = useServices();
  
  // Get Order Flow State
  const [getFlowOrderId, setGetFlowOrderId] = useState('');
  const [getFlowResult, setGetFlowResult] = useState(null);
  
  // Get All Flows State
  const [getAllFlowsResult, setGetAllFlowsResult] = useState(null);
  
  // Get Metrics State
  const [getMetricsResult, setGetMetricsResult] = useState(null);

  const handleGetOrderFlow = async (e) => {
    e.preventDefault();
    
    if (!getFlowOrderId) {
      toast.error('Please enter an order ID');
      return;
    }
    
    const result = await orchestratorService.getOrderFlow(getFlowOrderId);
    setGetFlowResult(result);
    
    if (result.success) {
      toast.success('Order flow retrieved successfully!');
    }
  };

  const handleGetAllFlows = async (e) => {
    e.preventDefault();
    
    const result = await orchestratorService.getAllFlows();
    setGetAllFlowsResult(result);
    
    if (result.success) {
      toast.success('All flows retrieved successfully!');
    }
  };

  const handleGetMetrics = async (e) => {
    e.preventDefault();
    
    const result = await orchestratorService.getMetrics();
    setGetMetricsResult(result);
    
    if (result.success) {
      toast.success('Orchestrator metrics retrieved successfully!');
    }
  };

  const renderFlowVisualization = (flowData) => {
    if (!flowData || !flowData.data || !flowData.data.steps) {
      return null;
    }

    const steps = flowData.data.steps;
    const getStepIcon = (stepType, status) => {
      const iconMap = {
        'order_created': 'mdi:shopping-plus',
        'payment_processing': 'mdi:credit-card-processing',
        'inventory_check': 'mdi:warehouse',
        'notification_sent': 'mdi:bell-check',
        'order_confirmed': 'mdi:check-circle',
        'order_shipped': 'mdi:truck-delivery',
        'order_delivered': 'mdi:package-check'
      };
      
      if (status === 'failed') return 'mdi:alert-circle';
      if (status === 'in_progress') return 'mdi:loading';
      
      return iconMap[stepType] || 'mdi:circle';
    };

    return (
      <FlowVisualization>
        <h4 style={{ marginBottom: '16px', color: '#374151', fontSize: '16px', fontWeight: '600' }}>
          Order Flow Visualization
        </h4>
        {steps.map((step, index) => (
          <FlowStep key={index} status={step.status}>
            <Icon icon={getStepIcon(step.type, step.status)} className="step-icon" />
            <div className="step-content">
              <div className="step-title">{step.name || step.type?.replace('_', ' ').toUpperCase()}</div>
              <div className="step-description">{step.description || 'Processing step'}</div>
              {step.timestamp && (
                <div className="step-timestamp">
                  {new Date(step.timestamp).toLocaleString()}
                </div>
              )}
            </div>
            <div className="step-status">{step.status}</div>
          </FlowStep>
        ))}
      </FlowVisualization>
    );
  };

  return (
    <PageContainer>
      <PageHeader>
        <h1 className="page-title">Order Orchestrator Service</h1>
        <p className="page-description">
          Monitor and manage order flows, view orchestration metrics, and track order processing steps.
        </p>
      </PageHeader>

      <ActionsGrid>
        {/* Get Order Flow */}
        <ActionCard>
          <CardHeader>
            <Icon icon="mdi:workflow" className="card-icon" />
            <h2 className="card-title">Get Order Flow</h2>
          </CardHeader>
          
          <Form onSubmit={handleGetOrderFlow}>
            <FormGroup>
              <label>Order ID</label>
              <Input
                type="text"
                value={getFlowOrderId}
                onChange={(e) => setGetFlowOrderId(e.target.value)}
                placeholder="Enter order ID to view flow"
                required
              />
            </FormGroup>
            
            <Button type="submit" disabled={loading}>
              <Icon icon="mdi:magnify" className="button-icon" />
              Get Order Flow
            </Button>
          </Form>
          
          {getFlowResult && (
            <>
              {renderFlowVisualization(getFlowResult)}
              <ResultContainer>
                <div className="result-title">Raw Flow Data:</div>
                <div className="result-content">{JSON.stringify(getFlowResult, null, 2)}</div>
              </ResultContainer>
            </>
          )}
        </ActionCard>

        {/* Get All Flows */}
        <ActionCard>
          <CardHeader>
            <Icon icon="mdi:format-list-bulleted" className="card-icon" />
            <h2 className="card-title">Get All Flows</h2>
          </CardHeader>
          
          <Form onSubmit={handleGetAllFlows}>
            <Button type="submit" disabled={loading}>
              <Icon icon="mdi:view-list" className="button-icon" />
              Get All Order Flows
            </Button>
          </Form>
          
          {getAllFlowsResult && (
            <ResultContainer>
              <div className="result-title">All Order Flows:</div>
              <div className="result-content">{JSON.stringify(getAllFlowsResult, null, 2)}</div>
            </ResultContainer>
          )}
        </ActionCard>

        {/* Get Orchestrator Metrics */}
        <ActionCard>
          <CardHeader>
            <Icon icon="mdi:chart-line" className="card-icon" />
            <h2 className="card-title">Orchestrator Metrics</h2>
          </CardHeader>
          
          <Form onSubmit={handleGetMetrics}>
            <Button type="submit" disabled={loading}>
              <Icon icon="mdi:chart-bar" className="button-icon" />
              Get Orchestrator Metrics
            </Button>
          </Form>
          
          {getMetricsResult && (
            <ResultContainer>
              <div className="result-title">Orchestrator Performance Metrics:</div>
              <div className="result-content">{JSON.stringify(getMetricsResult, null, 2)}</div>
            </ResultContainer>
          )}
        </ActionCard>

        {/* Flow Statistics */}
        <ActionCard>
          <CardHeader>
            <Icon icon="mdi:chart-pie" className="card-icon" />
            <h2 className="card-title">Flow Statistics</h2>
          </CardHeader>
          
          <div style={{ padding: '16px 0' }}>
            <p style={{ color: '#6b7280', fontSize: '14px', marginBottom: '16px' }}>
              View comprehensive statistics about order flows, success rates, and processing times.
            </p>
            
            <div style={{ 
              display: 'grid', 
              gridTemplateColumns: 'repeat(auto-fit, minmax(120px, 1fr))', 
              gap: '12px',
              marginBottom: '16px'
            }}>
              <div style={{ 
                background: '#f0f9ff', 
                padding: '12px', 
                borderRadius: '6px', 
                textAlign: 'center',
                border: '1px solid #e0f2fe'
              }}>
                <div style={{ fontSize: '20px', fontWeight: '700', color: '#0369a1' }}>-</div>
                <div style={{ fontSize: '12px', color: '#075985' }}>Total Flows</div>
              </div>
              
              <div style={{ 
                background: '#f0fdf4', 
                padding: '12px', 
                borderRadius: '6px', 
                textAlign: 'center',
                border: '1px solid #dcfce7'
              }}>
                <div style={{ fontSize: '20px', fontWeight: '700', color: '#166534' }}>-</div>
                <div style={{ fontSize: '12px', color: '#15803d' }}>Successful</div>
              </div>
              
              <div style={{ 
                background: '#fef2f2', 
                padding: '12px', 
                borderRadius: '6px', 
                textAlign: 'center',
                border: '1px solid #fecaca'
              }}>
                <div style={{ fontSize: '20px', fontWeight: '700', color: '#991b1b' }}>-</div>
                <div style={{ fontSize: '12px', color: '#dc2626' }}>Failed</div>
              </div>
              
              <div style={{ 
                background: '#fffbeb', 
                padding: '12px', 
                borderRadius: '6px', 
                textAlign: 'center',
                border: '1px solid #fed7aa'
              }}>
                <div style={{ fontSize: '20px', fontWeight: '700', color: '#92400e' }}>-</div>
                <div style={{ fontSize: '12px', color: '#d97706' }}>In Progress</div>
              </div>
            </div>
            
            <p style={{ color: '#9ca3af', fontSize: '12px', fontStyle: 'italic' }}>
              * Statistics will be populated when you fetch flow data
            </p>
          </div>
        </ActionCard>
      </ActionsGrid>
    </PageContainer>
  );
};

export default OrchestratorService;