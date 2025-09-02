import React from 'react';
import { BrowserRouter as Router, Routes, Route } from 'react-router-dom';
import { ToastContainer } from 'react-toastify';
import 'react-toastify/dist/ReactToastify.css';
import styled from 'styled-components';
import Sidebar from './components/Sidebar';
import Header from './components/Header';
import Dashboard from './pages/Dashboard';
import OrderService from './pages/OrderService';
import PaymentService from './pages/PaymentService';
import InventoryService from './pages/InventoryService';
import NotificationService from './pages/NotificationService';
import MonitoringService from './pages/MonitoringService';
import OrchestratorService from './pages/OrchestratorService';
import { ServiceProvider } from './context/ServiceContext';

const AppContainer = styled.div`
  display: flex;
  min-height: 100vh;
  background-color: #f8fafc;
`;

const MainContent = styled.div`
  flex: 1;
  display: flex;
  flex-direction: column;
  margin-left: 280px;
`;

const ContentArea = styled.div`
  flex: 1;
  padding: 24px;
  overflow-y: auto;
`;

function App() {
  return (
    <ServiceProvider>
      <Router>
        <AppContainer>
          <Sidebar />
          <MainContent>
            <Header />
            <ContentArea>
              <Routes>
                <Route path="/" element={<Dashboard />} />
                <Route path="/orders" element={<OrderService />} />
                <Route path="/payments" element={<PaymentService />} />
                <Route path="/inventory" element={<InventoryService />} />
                <Route path="/notifications" element={<NotificationService />} />
                <Route path="/monitoring" element={<MonitoringService />} />
                <Route path="/orchestrator" element={<OrchestratorService />} />
              </Routes>
            </ContentArea>
          </MainContent>
          <ToastContainer
            position="top-right"
            autoClose={5000}
            hideProgressBar={false}
            newestOnTop={false}
            closeOnClick
            rtl={false}
            pauseOnFocusLoss
            draggable
            pauseOnHover
            theme="light"
          />
        </AppContainer>
      </Router>
    </ServiceProvider>
  );
}

export default App;