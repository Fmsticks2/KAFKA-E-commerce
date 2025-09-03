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
  grid-template-columns: repeat(auto-fit, minmax(350px, 1fr));
  gap: 24px;
  
  @media (max-width: 768px) {
    grid-template-columns: 1fr;
    gap: 16px;
  }
  
  @media (min-width: 1200px) {
    grid-template-columns: repeat(2, 1fr);
  }
`;

const ActionCard = styled.div`
  background: white;
  border-radius: 12px;
  padding: 24px;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.1);
  border: 1px solid #e2e8f0;
  min-height: fit-content;
  height: auto;
  
  @media (max-width: 768px) {
    padding: 16px;
  }
`;

const CardHeader = styled.div`
  display: flex;
  align-items: center;
  gap: 12px;
  margin-bottom: 20px;
  
  .card-icon {
    font-size: 24px;
    color: #3b82f6;
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
    border-color: #3b82f6;
    box-shadow: 0 0 0 3px rgba(59, 130, 246, 0.1);
  }
`;

const TextArea = styled.textarea`
  padding: 10px 12px;
  border: 1px solid #d1d5db;
  border-radius: 6px;
  font-size: 14px;
  min-height: 100px;
  resize: vertical;
  font-family: 'Inter', sans-serif;
  transition: border-color 0.2s ease;
  
  &:focus {
    outline: none;
    border-color: #3b82f6;
    box-shadow: 0 0 0 3px rgba(59, 130, 246, 0.1);
  }
`;

const Button = styled.button`
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 8px;
  padding: 12px 20px;
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
  
  .button-icon {
    font-size: 16px;
  }
`;

const ItemsContainer = styled.div`
  border: 1px solid #e5e7eb;
  border-radius: 6px;
  padding: 16px;
  background-color: #f9fafb;
`;

const ItemRow = styled.div`
  display: grid;
  grid-template-columns: 2fr 1fr 1fr auto;
  gap: 12px;
  align-items: end;
  margin-bottom: 12px;
  
  @media (max-width: 768px) {
    grid-template-columns: 1fr;
    gap: 8px;
    
    > div {
      display: flex;
      flex-direction: column;
      gap: 4px;
    }
  }
  
  &:last-child {
    margin-bottom: 0;
  }
`;

const RemoveButton = styled.button`
  padding: 8px;
  background-color: #ef4444;
  color: white;
  border: none;
  border-radius: 4px;
  cursor: pointer;
  transition: background-color 0.2s ease;
  
  &:hover {
    background-color: #dc2626;
  }
  
  .remove-icon {
    font-size: 16px;
  }
`;

const AddButton = styled.button`
  display: flex;
  align-items: center;
  gap: 6px;
  padding: 8px 12px;
  background-color: #10b981;
  color: white;
  border: none;
  border-radius: 4px;
  font-size: 14px;
  cursor: pointer;
  transition: background-color 0.2s ease;
  
  &:hover {
    background-color: #059669;
  }
  
  .add-icon {
    font-size: 14px;
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

const OrderService = () => {
  const { orderService, loading } = useServices();
  
  // Create Order State
  const [createOrderData, setCreateOrderData] = useState({
    customer_id: '',
    items: [{ product_id: '', quantity: 1, price: 0 }]
  });
  const [createOrderResult, setCreateOrderResult] = useState(null);
  
  // Get Order State
  const [getOrderId, setGetOrderId] = useState('');
  const [getOrderResult, setGetOrderResult] = useState(null);
  
  // Get Customer Orders State
  const [customerId, setCustomerId] = useState('');
  const [customerOrdersResult, setCustomerOrdersResult] = useState(null);
  
  // Validate Order State
  const [validateOrderId, setValidateOrderId] = useState('');
  const [validateOrderResult, setValidateOrderResult] = useState(null);

  const handleCreateOrder = async (e) => {
    e.preventDefault();
    
    if (!createOrderData.customer_id || createOrderData.items.some(item => !item.product_id || item.quantity <= 0 || item.price <= 0)) {
      toast.error('Please fill in all required fields');
      return;
    }
    
    const result = await orderService.createOrder(createOrderData);
    setCreateOrderResult(result);
    
    if (result.success) {
      toast.success('Order created successfully!');
      // Reset form
      setCreateOrderData({
        customer_id: '',
        items: [{ product_id: '', quantity: 1, price: 0 }]
      });
    }
  };

  const handleGetOrder = async (e) => {
    e.preventDefault();
    
    if (!getOrderId) {
      toast.error('Please enter an order ID');
      return;
    }
    
    const result = await orderService.getOrder(getOrderId);
    setGetOrderResult(result);
    
    if (result.success) {
      toast.success('Order retrieved successfully!');
    }
  };

  const handleGetCustomerOrders = async (e) => {
    e.preventDefault();
    
    if (!customerId) {
      toast.error('Please enter a customer ID');
      return;
    }
    
    const result = await orderService.getCustomerOrders(customerId);
    setCustomerOrdersResult(result);
    
    if (result.success) {
      toast.success('Customer orders retrieved successfully!');
    }
  };

  const handleValidateOrder = async (e) => {
    e.preventDefault();
    
    if (!validateOrderId) {
      toast.error('Please enter an order ID');
      return;
    }
    
    const result = await orderService.validateOrder(validateOrderId);
    setValidateOrderResult(result);
    
    if (result.success) {
      toast.success('Order validation triggered successfully!');
    }
  };

  const addItem = () => {
    setCreateOrderData(prev => ({
      ...prev,
      items: [...prev.items, { product_id: '', quantity: 1, price: 0 }]
    }));
  };

  const removeItem = (index) => {
    setCreateOrderData(prev => ({
      ...prev,
      items: prev.items.filter((_, i) => i !== index)
    }));
  };

  const updateItem = (index, field, value) => {
    setCreateOrderData(prev => ({
      ...prev,
      items: prev.items.map((item, i) => 
        i === index ? { ...item, [field]: field === 'quantity' ? parseInt(value) || 0 : field === 'price' ? parseFloat(value) || 0 : value } : item
      )
    }));
  };

  return (
    <PageContainer>
      <PageHeader>
        <h1 className="page-title">Order Service Testing</h1>
        <p className="page-description">
          Test the Order Service endpoints including creating orders, retrieving orders, and validating orders.
        </p>
      </PageHeader>

      <ActionsGrid>
        {/* Create Order */}
        <ActionCard>
          <CardHeader>
            <Icon icon="mdi:plus-circle" className="card-icon" />
            <h2 className="card-title">Create Order</h2>
          </CardHeader>
          
          <Form onSubmit={handleCreateOrder}>
            <FormGroup>
              <label>Customer ID</label>
              <Input
                type="text"
                value={createOrderData.customer_id}
                onChange={(e) => setCreateOrderData(prev => ({ ...prev, customer_id: e.target.value }))}
                placeholder="Enter customer ID"
                required
              />
            </FormGroup>
            
            <FormGroup>
              <label>Order Items</label>
              <ItemsContainer>
                {createOrderData.items.map((item, index) => (
                  <ItemRow key={index}>
                    <div>
                      <Input
                        type="text"
                        value={item.product_id}
                        onChange={(e) => updateItem(index, 'product_id', e.target.value)}
                        placeholder="Product ID"
                        required
                      />
                    </div>
                    <div>
                      <Input
                        type="number"
                        value={item.quantity}
                        onChange={(e) => updateItem(index, 'quantity', e.target.value)}
                        placeholder="Quantity"
                        min="1"
                        required
                      />
                    </div>
                    <div>
                      <Input
                        type="number"
                        step="0.01"
                        value={item.price}
                        onChange={(e) => updateItem(index, 'price', e.target.value)}
                        placeholder="Price"
                        min="0"
                        required
                      />
                    </div>
                    {createOrderData.items.length > 1 && (
                      <RemoveButton type="button" onClick={() => removeItem(index)}>
                        <Icon icon="mdi:minus" className="remove-icon" />
                      </RemoveButton>
                    )}
                  </ItemRow>
                ))}
                <AddButton type="button" onClick={addItem}>
                  <Icon icon="mdi:plus" className="add-icon" />
                  Add Item
                </AddButton>
              </ItemsContainer>
            </FormGroup>
            
            <Button type="submit" disabled={loading}>
              <Icon icon="mdi:shopping" className="button-icon" />
              Create Order
            </Button>
          </Form>
          
          {createOrderResult && (
            <ResultContainer>
              <div className="result-title">Result:</div>
              <div className="result-content">{JSON.stringify(createOrderResult, null, 2)}</div>
            </ResultContainer>
          )}
        </ActionCard>

        {/* Get Order */}
        <ActionCard>
          <CardHeader>
            <Icon icon="mdi:file-search" className="card-icon" />
            <h2 className="card-title">Get Order</h2>
          </CardHeader>
          
          <Form onSubmit={handleGetOrder}>
            <FormGroup>
              <label>Order ID</label>
              <Input
                type="text"
                value={getOrderId}
                onChange={(e) => setGetOrderId(e.target.value)}
                placeholder="Enter order ID"
                required
              />
            </FormGroup>
            
            <Button type="submit" disabled={loading}>
              <Icon icon="mdi:magnify" className="button-icon" />
              Get Order
            </Button>
          </Form>
          
          {getOrderResult && (
            <ResultContainer>
              <div className="result-title">Result:</div>
              <div className="result-content">{JSON.stringify(getOrderResult, null, 2)}</div>
            </ResultContainer>
          )}
        </ActionCard>

        {/* Get Customer Orders */}
        <ActionCard>
          <CardHeader>
            <Icon icon="mdi:account-search" className="card-icon" />
            <h2 className="card-title">Get Customer Orders</h2>
          </CardHeader>
          
          <Form onSubmit={handleGetCustomerOrders}>
            <FormGroup>
              <label>Customer ID</label>
              <Input
                type="text"
                value={customerId}
                onChange={(e) => setCustomerId(e.target.value)}
                placeholder="Enter customer ID"
                required
              />
            </FormGroup>
            
            <Button type="submit" disabled={loading}>
              <Icon icon="mdi:account-multiple" className="button-icon" />
              Get Customer Orders
            </Button>
          </Form>
          
          {customerOrdersResult && (
            <ResultContainer>
              <div className="result-title">Result:</div>
              <div className="result-content">{JSON.stringify(customerOrdersResult, null, 2)}</div>
            </ResultContainer>
          )}
        </ActionCard>

        {/* Validate Order */}
        <ActionCard>
          <CardHeader>
            <Icon icon="mdi:check-circle" className="card-icon" />
            <h2 className="card-title">Validate Order</h2>
          </CardHeader>
          
          <Form onSubmit={handleValidateOrder}>
            <FormGroup>
              <label>Order ID</label>
              <Input
                type="text"
                value={validateOrderId}
                onChange={(e) => setValidateOrderId(e.target.value)}
                placeholder="Enter order ID to validate"
                required
              />
            </FormGroup>
            
            <Button type="submit" disabled={loading}>
              <Icon icon="mdi:shield-check" className="button-icon" />
              Validate Order
            </Button>
          </Form>
          
          {validateOrderResult && (
            <ResultContainer>
              <div className="result-title">Result:</div>
              <div className="result-content">{JSON.stringify(validateOrderResult, null, 2)}</div>
            </ResultContainer>
          )}
        </ActionCard>
      </ActionsGrid>
    </PageContainer>
  );
};

export default OrderService;