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
    color: #10b981;
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
    border-color: #10b981;
    box-shadow: 0 0 0 3px rgba(16, 185, 129, 0.1);
  }
`;

const Select = styled.select`
  padding: 10px 12px;
  border: 1px solid #d1d5db;
  border-radius: 6px;
  font-size: 14px;
  background-color: white;
  transition: border-color 0.2s ease;
  
  &:focus {
    outline: none;
    border-color: #10b981;
    box-shadow: 0 0 0 3px rgba(16, 185, 129, 0.1);
  }
`;

const Button = styled.button`
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 8px;
  padding: 12px 20px;
  background-color: #10b981;
  color: white;
  border: none;
  border-radius: 6px;
  font-weight: 500;
  cursor: pointer;
  transition: all 0.2s ease;
  
  &:hover {
    background-color: #059669;
  }
  
  &:disabled {
    background-color: #9ca3af;
    cursor: not-allowed;
  }
  
  .button-icon {
    font-size: 16px;
  }
`;

const RefundButton = styled(Button)`
  background-color: #ef4444;
  
  &:hover {
    background-color: #dc2626;
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
  }
`;

const PaymentService = () => {
  const { paymentService, loading } = useServices();
  
  // Process Payment State
  const [processPaymentData, setProcessPaymentData] = useState({
    order_id: '',
    amount: 0,
    payment_method: 'credit_card',
    payment_details: {
      card_number: '',
      expiry_date: '',
      cvv: '',
      cardholder_name: ''
    }
  });
  const [processPaymentResult, setProcessPaymentResult] = useState(null);
  
  // Get Payment State
  const [getPaymentId, setGetPaymentId] = useState('');
  const [getPaymentResult, setGetPaymentResult] = useState(null);
  
  // Get Order Payments State
  const [orderPaymentsId, setOrderPaymentsId] = useState('');
  const [orderPaymentsResult, setOrderPaymentsResult] = useState(null);
  
  // Refund Payment State
  const [refundPaymentId, setRefundPaymentId] = useState('');
  const [refundAmount, setRefundAmount] = useState(0);
  const [refundReason, setRefundReason] = useState('');
  const [refundResult, setRefundResult] = useState(null);

  const handleProcessPayment = async (e) => {
    e.preventDefault();
    
    if (!processPaymentData.order_id || processPaymentData.amount <= 0) {
      toast.error('Please fill in all required fields');
      return;
    }
    
    const result = await paymentService.processPayment(processPaymentData);
    setProcessPaymentResult(result);
    
    if (result.success) {
      toast.success('Payment processed successfully!');
      // Reset form
      setProcessPaymentData({
        order_id: '',
        amount: 0,
        payment_method: 'credit_card',
        payment_details: {
          card_number: '',
          expiry_date: '',
          cvv: '',
          cardholder_name: ''
        }
      });
    }
  };

  const handleGetPayment = async (e) => {
    e.preventDefault();
    
    if (!getPaymentId) {
      toast.error('Please enter a payment ID');
      return;
    }
    
    const result = await paymentService.getPayment(getPaymentId);
    setGetPaymentResult(result);
    
    if (result.success) {
      toast.success('Payment retrieved successfully!');
    }
  };

  const handleGetOrderPayments = async (e) => {
    e.preventDefault();
    
    if (!orderPaymentsId) {
      toast.error('Please enter an order ID');
      return;
    }
    
    const result = await paymentService.getOrderPayments(orderPaymentsId);
    setOrderPaymentsResult(result);
    
    if (result.success) {
      toast.success('Order payments retrieved successfully!');
    }
  };

  const handleRefundPayment = async (e) => {
    e.preventDefault();
    
    if (!refundPaymentId || refundAmount <= 0) {
      toast.error('Please enter payment ID and refund amount');
      return;
    }
    
    const refundData = {
      amount: refundAmount,
      reason: refundReason || 'Customer request'
    };
    
    const result = await paymentService.refundPayment(refundPaymentId, refundData);
    setRefundResult(result);
    
    if (result.success) {
      toast.success('Refund processed successfully!');
      // Reset form
      setRefundPaymentId('');
      setRefundAmount(0);
      setRefundReason('');
    }
  };

  const updatePaymentDetails = (field, value) => {
    setProcessPaymentData(prev => ({
      ...prev,
      payment_details: {
        ...prev.payment_details,
        [field]: value
      }
    }));
  };

  return (
    <PageContainer>
      <PageHeader>
        <h1 className="page-title">Payment Service Testing</h1>
        <p className="page-description">
          Test the Payment Service endpoints including processing payments, retrieving payments, and handling refunds.
        </p>
      </PageHeader>

      <ActionsGrid>
        {/* Process Payment */}
        <ActionCard>
          <CardHeader>
            <Icon icon="mdi:credit-card" className="card-icon" />
            <h2 className="card-title">Process Payment</h2>
          </CardHeader>
          
          <Form onSubmit={handleProcessPayment}>
            <FormGroup>
              <label>Order ID</label>
              <Input
                type="text"
                value={processPaymentData.order_id}
                onChange={(e) => setProcessPaymentData(prev => ({ ...prev, order_id: e.target.value }))}
                placeholder="Enter order ID"
                required
              />
            </FormGroup>
            
            <FormGroup>
              <label>Amount</label>
              <Input
                type="number"
                step="0.01"
                value={processPaymentData.amount}
                onChange={(e) => setProcessPaymentData(prev => ({ ...prev, amount: parseFloat(e.target.value) || 0 }))}
                placeholder="Enter payment amount"
                min="0"
                required
              />
            </FormGroup>
            
            <FormGroup>
              <label>Payment Method</label>
              <Select
                value={processPaymentData.payment_method}
                onChange={(e) => setProcessPaymentData(prev => ({ ...prev, payment_method: e.target.value }))}
              >
                <option value="credit_card">Credit Card</option>
                <option value="debit_card">Debit Card</option>
                <option value="paypal">PayPal</option>
                <option value="bank_transfer">Bank Transfer</option>
              </Select>
            </FormGroup>
            
            {processPaymentData.payment_method === 'credit_card' && (
              <>
                <FormGroup>
                  <label>Card Number</label>
                  <Input
                    type="text"
                    value={processPaymentData.payment_details.card_number}
                    onChange={(e) => updatePaymentDetails('card_number', e.target.value)}
                    placeholder="1234 5678 9012 3456"
                    maxLength="19"
                  />
                </FormGroup>
                
                <FormGroup>
                  <label>Cardholder Name</label>
                  <Input
                    type="text"
                    value={processPaymentData.payment_details.cardholder_name}
                    onChange={(e) => updatePaymentDetails('cardholder_name', e.target.value)}
                    placeholder="John Doe"
                  />
                </FormGroup>
                
                <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '16px' }}>
                  <FormGroup>
                    <label>Expiry Date</label>
                    <Input
                      type="text"
                      value={processPaymentData.payment_details.expiry_date}
                      onChange={(e) => updatePaymentDetails('expiry_date', e.target.value)}
                      placeholder="MM/YY"
                      maxLength="5"
                    />
                  </FormGroup>
                  
                  <FormGroup>
                    <label>CVV</label>
                    <Input
                      type="text"
                      value={processPaymentData.payment_details.cvv}
                      onChange={(e) => updatePaymentDetails('cvv', e.target.value)}
                      placeholder="123"
                      maxLength="4"
                    />
                  </FormGroup>
                </div>
              </>
            )}
            
            <Button type="submit" disabled={loading}>
              <Icon icon="mdi:cash" className="button-icon" />
              Process Payment
            </Button>
          </Form>
          
          {processPaymentResult && (
            <ResultContainer>
              <div className="result-title">Result:</div>
              <div className="result-content">{JSON.stringify(processPaymentResult, null, 2)}</div>
            </ResultContainer>
          )}
        </ActionCard>

        {/* Get Payment */}
        <ActionCard>
          <CardHeader>
            <Icon icon="mdi:file-search" className="card-icon" />
            <h2 className="card-title">Get Payment</h2>
          </CardHeader>
          
          <Form onSubmit={handleGetPayment}>
            <FormGroup>
              <label>Payment ID</label>
              <Input
                type="text"
                value={getPaymentId}
                onChange={(e) => setGetPaymentId(e.target.value)}
                placeholder="Enter payment ID"
                required
              />
            </FormGroup>
            
            <Button type="submit" disabled={loading}>
              <Icon icon="mdi:magnify" className="button-icon" />
              Get Payment
            </Button>
          </Form>
          
          {getPaymentResult && (
            <ResultContainer>
              <div className="result-title">Result:</div>
              <div className="result-content">{JSON.stringify(getPaymentResult, null, 2)}</div>
            </ResultContainer>
          )}
        </ActionCard>

        {/* Get Order Payments */}
        <ActionCard>
          <CardHeader>
            <Icon icon="mdi:receipt" className="card-icon" />
            <h2 className="card-title">Get Order Payments</h2>
          </CardHeader>
          
          <Form onSubmit={handleGetOrderPayments}>
            <FormGroup>
              <label>Order ID</label>
              <Input
                type="text"
                value={orderPaymentsId}
                onChange={(e) => setOrderPaymentsId(e.target.value)}
                placeholder="Enter order ID"
                required
              />
            </FormGroup>
            
            <Button type="submit" disabled={loading}>
              <Icon icon="mdi:format-list-bulleted" className="button-icon" />
              Get Order Payments
            </Button>
          </Form>
          
          {orderPaymentsResult && (
            <ResultContainer>
              <div className="result-title">Result:</div>
              <div className="result-content">{JSON.stringify(orderPaymentsResult, null, 2)}</div>
            </ResultContainer>
          )}
        </ActionCard>

        {/* Refund Payment */}
        <ActionCard>
          <CardHeader>
            <Icon icon="mdi:cash-refund" className="card-icon" />
            <h2 className="card-title">Refund Payment</h2>
          </CardHeader>
          
          <Form onSubmit={handleRefundPayment}>
            <FormGroup>
              <label>Payment ID</label>
              <Input
                type="text"
                value={refundPaymentId}
                onChange={(e) => setRefundPaymentId(e.target.value)}
                placeholder="Enter payment ID to refund"
                required
              />
            </FormGroup>
            
            <FormGroup>
              <label>Refund Amount</label>
              <Input
                type="number"
                step="0.01"
                value={refundAmount}
                onChange={(e) => setRefundAmount(parseFloat(e.target.value) || 0)}
                placeholder="Enter refund amount"
                min="0"
                required
              />
            </FormGroup>
            
            <FormGroup>
              <label>Refund Reason (Optional)</label>
              <Input
                type="text"
                value={refundReason}
                onChange={(e) => setRefundReason(e.target.value)}
                placeholder="Enter reason for refund"
              />
            </FormGroup>
            
            <RefundButton type="submit" disabled={loading}>
              <Icon icon="mdi:undo" className="button-icon" />
              Process Refund
            </RefundButton>
          </Form>
          
          {refundResult && (
            <ResultContainer>
              <div className="result-title">Result:</div>
              <div className="result-content">{JSON.stringify(refundResult, null, 2)}</div>
            </ResultContainer>
          )}
        </ActionCard>
      </ActionsGrid>
    </PageContainer>
  );
};

export default PaymentService;