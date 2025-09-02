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
    color: #8b5cf6;
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
    border-color: #8b5cf6;
    box-shadow: 0 0 0 3px rgba(139, 92, 246, 0.1);
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
    border-color: #8b5cf6;
    box-shadow: 0 0 0 3px rgba(139, 92, 246, 0.1);
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
    border-color: #8b5cf6;
    box-shadow: 0 0 0 3px rgba(139, 92, 246, 0.1);
  }
`;

const Button = styled.button`
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 8px;
  padding: 12px 20px;
  background-color: #8b5cf6;
  color: white;
  border: none;
  border-radius: 6px;
  font-weight: 500;
  cursor: pointer;
  transition: all 0.2s ease;
  
  &:hover {
    background-color: #7c3aed;
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
  }
`;

const NotificationService = () => {
  const { notificationService, loading } = useServices();
  
  // Send Notification State
  const [notificationData, setNotificationData] = useState({
    recipient: '',
    type: 'email',
    subject: '',
    message: '',
    template_id: '',
    data: '{}'
  });
  const [sendNotificationResult, setSendNotificationResult] = useState(null);
  
  // Get Notification State
  const [getNotificationId, setGetNotificationId] = useState('');
  const [getNotificationResult, setGetNotificationResult] = useState(null);
  
  // Get Recipient Notifications State
  const [recipientId, setRecipientId] = useState('');
  const [recipientNotificationsResult, setRecipientNotificationsResult] = useState(null);
  
  // Get Templates State
  const [getTemplatesResult, setGetTemplatesResult] = useState(null);
  
  // Create Template State
  const [templateData, setTemplateData] = useState({
    name: '',
    type: 'email',
    subject: '',
    body: '',
    variables: '[]'
  });
  const [createTemplateResult, setCreateTemplateResult] = useState(null);

  const handleSendNotification = async (e) => {
    e.preventDefault();
    
    if (!notificationData.recipient || !notificationData.message) {
      toast.error('Please fill in recipient and message');
      return;
    }
    
    let parsedData = {};
    if (notificationData.data) {
      try {
        parsedData = JSON.parse(notificationData.data);
      } catch (error) {
        toast.error('Invalid JSON format in data field');
        return;
      }
    }
    
    const payload = {
      recipient: notificationData.recipient,
      type: notificationData.type,
      subject: notificationData.subject,
      message: notificationData.message,
      ...(notificationData.template_id && { template_id: notificationData.template_id }),
      data: parsedData
    };
    
    const result = await notificationService.sendNotification(payload);
    setSendNotificationResult(result);
    
    if (result.success) {
      toast.success('Notification sent successfully!');
      // Reset form
      setNotificationData({
        recipient: '',
        type: 'email',
        subject: '',
        message: '',
        template_id: '',
        data: '{}'
      });
    }
  };

  const handleGetNotification = async (e) => {
    e.preventDefault();
    
    if (!getNotificationId) {
      toast.error('Please enter a notification ID');
      return;
    }
    
    const result = await notificationService.getNotification(getNotificationId);
    setGetNotificationResult(result);
    
    if (result.success) {
      toast.success('Notification retrieved successfully!');
    }
  };

  const handleGetRecipientNotifications = async (e) => {
    e.preventDefault();
    
    if (!recipientId) {
      toast.error('Please enter a recipient ID');
      return;
    }
    
    const result = await notificationService.getRecipientNotifications(recipientId);
    setRecipientNotificationsResult(result);
    
    if (result.success) {
      toast.success('Recipient notifications retrieved successfully!');
    }
  };

  const handleGetTemplates = async (e) => {
    e.preventDefault();
    
    const result = await notificationService.getTemplates();
    setGetTemplatesResult(result);
    
    if (result.success) {
      toast.success('Templates retrieved successfully!');
    }
  };

  const handleCreateTemplate = async (e) => {
    e.preventDefault();
    
    if (!templateData.name || !templateData.body) {
      toast.error('Please fill in template name and body');
      return;
    }
    
    let parsedVariables = [];
    if (templateData.variables) {
      try {
        parsedVariables = JSON.parse(templateData.variables);
      } catch (error) {
        toast.error('Invalid JSON format in variables field');
        return;
      }
    }
    
    const payload = {
      name: templateData.name,
      type: templateData.type,
      subject: templateData.subject,
      body: templateData.body,
      variables: parsedVariables
    };
    
    const result = await notificationService.createTemplate(payload);
    setCreateTemplateResult(result);
    
    if (result.success) {
      toast.success('Template created successfully!');
      // Reset form
      setTemplateData({
        name: '',
        type: 'email',
        subject: '',
        body: '',
        variables: '[]'
      });
    }
  };

  return (
    <PageContainer>
      <PageHeader>
        <h1 className="page-title">Notification Service Testing</h1>
        <p className="page-description">
          Test the Notification Service endpoints including sending notifications, managing templates, and retrieving notification history.
        </p>
      </PageHeader>

      <ActionsGrid>
        {/* Send Notification */}
        <ActionCard>
          <CardHeader>
            <Icon icon="mdi:send" className="card-icon" />
            <h2 className="card-title">Send Notification</h2>
          </CardHeader>
          
          <Form onSubmit={handleSendNotification}>
            <FormGroup>
              <label>Recipient</label>
              <Input
                type="text"
                value={notificationData.recipient}
                onChange={(e) => setNotificationData(prev => ({ ...prev, recipient: e.target.value }))}
                placeholder="Enter recipient (email, phone, user ID)"
                required
              />
            </FormGroup>
            
            <FormGroup>
              <label>Notification Type</label>
              <Select
                value={notificationData.type}
                onChange={(e) => setNotificationData(prev => ({ ...prev, type: e.target.value }))}
              >
                <option value="email">Email</option>
                <option value="sms">SMS</option>
                <option value="push">Push Notification</option>
                <option value="in_app">In-App</option>
              </Select>
            </FormGroup>
            
            <FormGroup>
              <label>Subject (for email)</label>
              <Input
                type="text"
                value={notificationData.subject}
                onChange={(e) => setNotificationData(prev => ({ ...prev, subject: e.target.value }))}
                placeholder="Enter notification subject"
              />
            </FormGroup>
            
            <FormGroup>
              <label>Message</label>
              <TextArea
                value={notificationData.message}
                onChange={(e) => setNotificationData(prev => ({ ...prev, message: e.target.value }))}
                placeholder="Enter notification message"
                required
              />
            </FormGroup>
            
            <FormGroup>
              <label>Template ID (Optional)</label>
              <Input
                type="text"
                value={notificationData.template_id}
                onChange={(e) => setNotificationData(prev => ({ ...prev, template_id: e.target.value }))}
                placeholder="Enter template ID if using template"
              />
            </FormGroup>
            
            <FormGroup>
              <label>Additional Data (JSON)</label>
              <TextArea
                value={notificationData.data}
                onChange={(e) => setNotificationData(prev => ({ ...prev, data: e.target.value }))}
                placeholder='{"key": "value"}'
                style={{ minHeight: '80px' }}
              />
            </FormGroup>
            
            <Button type="submit" disabled={loading}>
              <Icon icon="mdi:email-send" className="button-icon" />
              Send Notification
            </Button>
          </Form>
          
          {sendNotificationResult && (
            <ResultContainer>
              <div className="result-title">Result:</div>
              <div className="result-content">{JSON.stringify(sendNotificationResult, null, 2)}</div>
            </ResultContainer>
          )}
        </ActionCard>

        {/* Get Notification */}
        <ActionCard>
          <CardHeader>
            <Icon icon="mdi:file-search" className="card-icon" />
            <h2 className="card-title">Get Notification</h2>
          </CardHeader>
          
          <Form onSubmit={handleGetNotification}>
            <FormGroup>
              <label>Notification ID</label>
              <Input
                type="text"
                value={getNotificationId}
                onChange={(e) => setGetNotificationId(e.target.value)}
                placeholder="Enter notification ID"
                required
              />
            </FormGroup>
            
            <Button type="submit" disabled={loading}>
              <Icon icon="mdi:magnify" className="button-icon" />
              Get Notification
            </Button>
          </Form>
          
          {getNotificationResult && (
            <ResultContainer>
              <div className="result-title">Result:</div>
              <div className="result-content">{JSON.stringify(getNotificationResult, null, 2)}</div>
            </ResultContainer>
          )}
        </ActionCard>

        {/* Get Recipient Notifications */}
        <ActionCard>
          <CardHeader>
            <Icon icon="mdi:account-search" className="card-icon" />
            <h2 className="card-title">Get Recipient Notifications</h2>
          </CardHeader>
          
          <Form onSubmit={handleGetRecipientNotifications}>
            <FormGroup>
              <label>Recipient ID</label>
              <Input
                type="text"
                value={recipientId}
                onChange={(e) => setRecipientId(e.target.value)}
                placeholder="Enter recipient ID"
                required
              />
            </FormGroup>
            
            <Button type="submit" disabled={loading}>
              <Icon icon="mdi:bell-outline" className="button-icon" />
              Get Recipient Notifications
            </Button>
          </Form>
          
          {recipientNotificationsResult && (
            <ResultContainer>
              <div className="result-title">Result:</div>
              <div className="result-content">{JSON.stringify(recipientNotificationsResult, null, 2)}</div>
            </ResultContainer>
          )}
        </ActionCard>

        {/* Get Templates */}
        <ActionCard>
          <CardHeader>
            <Icon icon="mdi:file-document-multiple" className="card-icon" />
            <h2 className="card-title">Get Templates</h2>
          </CardHeader>
          
          <Form onSubmit={handleGetTemplates}>
            <Button type="submit" disabled={loading}>
              <Icon icon="mdi:format-list-bulleted" className="button-icon" />
              Get All Templates
            </Button>
          </Form>
          
          {getTemplatesResult && (
            <ResultContainer>
              <div className="result-title">Result:</div>
              <div className="result-content">{JSON.stringify(getTemplatesResult, null, 2)}</div>
            </ResultContainer>
          )}
        </ActionCard>

        {/* Create Template */}
        <ActionCard>
          <CardHeader>
            <Icon icon="mdi:file-document-plus" className="card-icon" />
            <h2 className="card-title">Create Template</h2>
          </CardHeader>
          
          <Form onSubmit={handleCreateTemplate}>
            <FormGroup>
              <label>Template Name</label>
              <Input
                type="text"
                value={templateData.name}
                onChange={(e) => setTemplateData(prev => ({ ...prev, name: e.target.value }))}
                placeholder="Enter template name"
                required
              />
            </FormGroup>
            
            <FormGroup>
              <label>Template Type</label>
              <Select
                value={templateData.type}
                onChange={(e) => setTemplateData(prev => ({ ...prev, type: e.target.value }))}
              >
                <option value="email">Email</option>
                <option value="sms">SMS</option>
                <option value="push">Push Notification</option>
                <option value="in_app">In-App</option>
              </Select>
            </FormGroup>
            
            <FormGroup>
              <label>Subject (for email templates)</label>
              <Input
                type="text"
                value={templateData.subject}
                onChange={(e) => setTemplateData(prev => ({ ...prev, subject: e.target.value }))}
                placeholder="Enter template subject"
              />
            </FormGroup>
            
            <FormGroup>
              <label>Template Body</label>
              <TextArea
                value={templateData.body}
                onChange={(e) => setTemplateData(prev => ({ ...prev, body: e.target.value }))}
                placeholder="Enter template body with variables like {{variable_name}}"
                required
                style={{ minHeight: '120px' }}
              />
            </FormGroup>
            
            <FormGroup>
              <label>Variables (JSON Array)</label>
              <TextArea
                value={templateData.variables}
                onChange={(e) => setTemplateData(prev => ({ ...prev, variables: e.target.value }))}
                placeholder='["variable1", "variable2"]'
                style={{ minHeight: '60px' }}
              />
            </FormGroup>
            
            <Button type="submit" disabled={loading}>
              <Icon icon="mdi:content-save" className="button-icon" />
              Create Template
            </Button>
          </Form>
          
          {createTemplateResult && (
            <ResultContainer>
              <div className="result-title">Result:</div>
              <div className="result-content">{JSON.stringify(createTemplateResult, null, 2)}</div>
            </ResultContainer>
          )}
        </ActionCard>
      </ActionsGrid>
    </PageContainer>
  );
};

export default NotificationService;