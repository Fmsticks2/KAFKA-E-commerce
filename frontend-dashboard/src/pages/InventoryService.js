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
    color: #f59e0b;
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
    border-color: #f59e0b;
    box-shadow: 0 0 0 3px rgba(245, 158, 11, 0.1);
  }
`;

const TextArea = styled.textarea`
  padding: 10px 12px;
  border: 1px solid #d1d5db;
  border-radius: 6px;
  font-size: 14px;
  min-height: 80px;
  resize: vertical;
  font-family: 'Inter', sans-serif;
  transition: border-color 0.2s ease;
  
  &:focus {
    outline: none;
    border-color: #f59e0b;
    box-shadow: 0 0 0 3px rgba(245, 158, 11, 0.1);
  }
`;

const Button = styled.button`
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 8px;
  padding: 12px 20px;
  background-color: #f59e0b;
  color: white;
  border: none;
  border-radius: 6px;
  font-weight: 500;
  cursor: pointer;
  transition: all 0.2s ease;
  
  &:hover {
    background-color: #d97706;
  }
  
  &:disabled {
    background-color: #9ca3af;
    cursor: not-allowed;
  }
  
  .button-icon {
    font-size: 16px;
  }
`;

const DangerButton = styled(Button)`
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

const InventoryService = () => {
  const { inventoryService, loading } = useServices();
  
  // Get All Inventory State
  const [getAllInventoryResult, setGetAllInventoryResult] = useState(null);
  
  // Get Product Inventory State
  const [getProductId, setGetProductId] = useState('');
  const [getProductResult, setGetProductResult] = useState(null);
  
  // Update Product Inventory State
  const [updateProductData, setUpdateProductData] = useState({
    product_id: '',
    quantity: 0,
    price: 0,
    description: ''
  });
  const [updateProductResult, setUpdateProductResult] = useState(null);
  
  // Create Reservation State
  const [reservationData, setReservationData] = useState({
    product_id: '',
    quantity: 1,
    customer_id: '',
    order_id: ''
  });
  const [createReservationResult, setCreateReservationResult] = useState(null);
  
  // Release Reservation State
  const [releaseReservationId, setReleaseReservationId] = useState('');
  const [releaseReservationResult, setReleaseReservationResult] = useState(null);

  const handleGetAllInventory = async (e) => {
    e.preventDefault();
    
    const result = await inventoryService.getAllInventory();
    setGetAllInventoryResult(result);
    
    if (result.success) {
      toast.success('Inventory retrieved successfully!');
    }
  };

  const handleGetProduct = async (e) => {
    e.preventDefault();
    
    if (!getProductId) {
      toast.error('Please enter a product ID');
      return;
    }
    
    const result = await inventoryService.getProduct(getProductId);
    setGetProductResult(result);
    
    if (result.success) {
      toast.success('Product inventory retrieved successfully!');
    }
  };

  const handleUpdateProduct = async (e) => {
    e.preventDefault();
    
    if (!updateProductData.product_id || updateProductData.quantity < 0 || updateProductData.price < 0) {
      toast.error('Please fill in all required fields with valid values');
      return;
    }
    
    const result = await inventoryService.updateProduct(updateProductData.product_id, {
      quantity: updateProductData.quantity,
      price: updateProductData.price,
      description: updateProductData.description
    });
    setUpdateProductResult(result);
    
    if (result.success) {
      toast.success('Product inventory updated successfully!');
      // Reset form
      setUpdateProductData({
        product_id: '',
        quantity: 0,
        price: 0,
        description: ''
      });
    }
  };

  const handleCreateReservation = async (e) => {
    e.preventDefault();
    
    if (!reservationData.product_id || !reservationData.customer_id || reservationData.quantity <= 0) {
      toast.error('Please fill in all required fields');
      return;
    }
    
    const result = await inventoryService.createReservation(reservationData);
    setCreateReservationResult(result);
    
    if (result.success) {
      toast.success('Reservation created successfully!');
      // Reset form
      setReservationData({
        product_id: '',
        quantity: 1,
        customer_id: '',
        order_id: ''
      });
    }
  };

  const handleReleaseReservation = async (e) => {
    e.preventDefault();
    
    if (!releaseReservationId) {
      toast.error('Please enter a reservation ID');
      return;
    }
    
    const result = await inventoryService.releaseReservation(releaseReservationId);
    setReleaseReservationResult(result);
    
    if (result.success) {
      toast.success('Reservation released successfully!');
      setReleaseReservationId('');
    }
  };

  return (
    <PageContainer>
      <PageHeader>
        <h1 className="page-title">Inventory Service Testing</h1>
        <p className="page-description">
          Test the Inventory Service endpoints including inventory management, stock checking, and reservation handling.
        </p>
      </PageHeader>

      <ActionsGrid>
        {/* Get All Inventory */}
        <ActionCard>
          <CardHeader>
            <Icon icon="mdi:warehouse" className="card-icon" />
            <h2 className="card-title">Get All Inventory</h2>
          </CardHeader>
          
          <Form onSubmit={handleGetAllInventory}>
            <Button type="submit" disabled={loading}>
              <Icon icon="mdi:format-list-bulleted" className="button-icon" />
              Get All Inventory
            </Button>
          </Form>
          
          {getAllInventoryResult && (
            <ResultContainer>
              <div className="result-title">Result:</div>
              <div className="result-content">{JSON.stringify(getAllInventoryResult, null, 2)}</div>
            </ResultContainer>
          )}
        </ActionCard>

        {/* Get Product Inventory */}
        <ActionCard>
          <CardHeader>
            <Icon icon="mdi:package-variant" className="card-icon" />
            <h2 className="card-title">Get Product Inventory</h2>
          </CardHeader>
          
          <Form onSubmit={handleGetProduct}>
            <FormGroup>
              <label>Product ID</label>
              <Input
                type="text"
                value={getProductId}
                onChange={(e) => setGetProductId(e.target.value)}
                placeholder="Enter product ID"
                required
              />
            </FormGroup>
            
            <Button type="submit" disabled={loading}>
              <Icon icon="mdi:magnify" className="button-icon" />
              Get Product
            </Button>
          </Form>
          
          {getProductResult && (
            <ResultContainer>
              <div className="result-title">Result:</div>
              <div className="result-content">{JSON.stringify(getProductResult, null, 2)}</div>
            </ResultContainer>
          )}
        </ActionCard>

        {/* Update Product Inventory */}
        <ActionCard>
          <CardHeader>
            <Icon icon="mdi:pencil" className="card-icon" />
            <h2 className="card-title">Update Product Inventory</h2>
          </CardHeader>
          
          <Form onSubmit={handleUpdateProduct}>
            <FormGroup>
              <label>Product ID</label>
              <Input
                type="text"
                value={updateProductData.product_id}
                onChange={(e) => setUpdateProductData(prev => ({ ...prev, product_id: e.target.value }))}
                placeholder="Enter product ID"
                required
              />
            </FormGroup>
            
            <FormGroup>
              <label>Quantity</label>
              <Input
                type="number"
                value={updateProductData.quantity}
                onChange={(e) => setUpdateProductData(prev => ({ ...prev, quantity: parseInt(e.target.value) || 0 }))}
                placeholder="Enter quantity"
                min="0"
                required
              />
            </FormGroup>
            
            <FormGroup>
              <label>Price</label>
              <Input
                type="number"
                step="0.01"
                value={updateProductData.price}
                onChange={(e) => setUpdateProductData(prev => ({ ...prev, price: parseFloat(e.target.value) || 0 }))}
                placeholder="Enter price"
                min="0"
                required
              />
            </FormGroup>
            
            <FormGroup>
              <label>Description (Optional)</label>
              <TextArea
                value={updateProductData.description}
                onChange={(e) => setUpdateProductData(prev => ({ ...prev, description: e.target.value }))}
                placeholder="Enter product description"
              />
            </FormGroup>
            
            <Button type="submit" disabled={loading}>
              <Icon icon="mdi:content-save" className="button-icon" />
              Update Product
            </Button>
          </Form>
          
          {updateProductResult && (
            <ResultContainer>
              <div className="result-title">Result:</div>
              <div className="result-content">{JSON.stringify(updateProductResult, null, 2)}</div>
            </ResultContainer>
          )}
        </ActionCard>

        {/* Create Reservation */}
        <ActionCard>
          <CardHeader>
            <Icon icon="mdi:bookmark-plus" className="card-icon" />
            <h2 className="card-title">Create Reservation</h2>
          </CardHeader>
          
          <Form onSubmit={handleCreateReservation}>
            <FormGroup>
              <label>Product ID</label>
              <Input
                type="text"
                value={reservationData.product_id}
                onChange={(e) => setReservationData(prev => ({ ...prev, product_id: e.target.value }))}
                placeholder="Enter product ID"
                required
              />
            </FormGroup>
            
            <FormGroup>
              <label>Quantity</label>
              <Input
                type="number"
                value={reservationData.quantity}
                onChange={(e) => setReservationData(prev => ({ ...prev, quantity: parseInt(e.target.value) || 1 }))}
                placeholder="Enter quantity to reserve"
                min="1"
                required
              />
            </FormGroup>
            
            <FormGroup>
              <label>Customer ID</label>
              <Input
                type="text"
                value={reservationData.customer_id}
                onChange={(e) => setReservationData(prev => ({ ...prev, customer_id: e.target.value }))}
                placeholder="Enter customer ID"
                required
              />
            </FormGroup>
            
            <FormGroup>
              <label>Order ID (Optional)</label>
              <Input
                type="text"
                value={reservationData.order_id}
                onChange={(e) => setReservationData(prev => ({ ...prev, order_id: e.target.value }))}
                placeholder="Enter order ID"
              />
            </FormGroup>
            
            <Button type="submit" disabled={loading}>
              <Icon icon="mdi:bookmark" className="button-icon" />
              Create Reservation
            </Button>
          </Form>
          
          {createReservationResult && (
            <ResultContainer>
              <div className="result-title">Result:</div>
              <div className="result-content">{JSON.stringify(createReservationResult, null, 2)}</div>
            </ResultContainer>
          )}
        </ActionCard>

        {/* Release Reservation */}
        <ActionCard>
          <CardHeader>
            <Icon icon="mdi:bookmark-remove" className="card-icon" />
            <h2 className="card-title">Release Reservation</h2>
          </CardHeader>
          
          <Form onSubmit={handleReleaseReservation}>
            <FormGroup>
              <label>Reservation ID</label>
              <Input
                type="text"
                value={releaseReservationId}
                onChange={(e) => setReleaseReservationId(e.target.value)}
                placeholder="Enter reservation ID to release"
                required
              />
            </FormGroup>
            
            <DangerButton type="submit" disabled={loading}>
              <Icon icon="mdi:delete" className="button-icon" />
              Release Reservation
            </DangerButton>
          </Form>
          
          {releaseReservationResult && (
            <ResultContainer>
              <div className="result-title">Result:</div>
              <div className="result-content">{JSON.stringify(releaseReservationResult, null, 2)}</div>
            </ResultContainer>
          )}
        </ActionCard>
      </ActionsGrid>
    </PageContainer>
  );
};

export default InventoryService;