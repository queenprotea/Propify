import { Routes, Route } from 'react-router-dom'
import Layout from './components/Layout'
import ProtectedRoute from './components/ProtectedRoute'

import Home from './pages/buyer/Home'
import PropertyDetail from './pages/buyer/PropertyDetail'
import Profile from './pages/buyer/Profile'
import MyVisits from './pages/buyer/MyVisits'
import MyContracts from './pages/buyer/MyContracts'
import MyRequests from './pages/buyer/MyRequests'

import Login from './pages/auth/Login'
import Register from './pages/auth/Register'
import VerifyEmail from './pages/auth/VerifyEmail'

import Dashboard from './pages/admin/Dashboard'
import PropertiesAdmin from './pages/admin/PropertiesAdmin'
import PropertyForm from './pages/admin/PropertyForm'
import UsersAdmin from './pages/admin/UsersAdmin'
import RegisterAdmin from './pages/admin/RegisterAdmin'
import ContractsAdmin from './pages/admin/ContractsAdmin'
import RequestsAdmin from './pages/admin/RequestsAdmin'
import RentsAdmin from './pages/admin/RentsAdmin'
import SalesAdmin from './pages/admin/SalesAdmin'
import AuditAdmin from './pages/admin/AuditAdmin'
import CatalogsAdmin from './pages/admin/CatalogsAdmin'
import PaymentsAdmin from './pages/admin/PaymentsAdmin'
import VisitsAdmin from './pages/admin/VisitsAdmin'
import ContactsAdmin from './pages/admin/ContactsAdmin'

import NotFound from './pages/NotFound'

export default function App() {
  return (
    <Layout>
      <Routes>
        {/* Públicas */}
        <Route path="/" element={<Home />} />
        <Route path="/inmueble/:id" element={<PropertyDetail />} />
        <Route path="/login" element={<Login />} />
        <Route path="/registro" element={<Register />} />
        <Route path="/verificar-correo" element={<VerifyEmail />} />

        {/* Usuario autenticado */}
        <Route path="/perfil" element={<ProtectedRoute><Profile /></ProtectedRoute>} />
        <Route path="/mis-visitas" element={<ProtectedRoute><MyVisits /></ProtectedRoute>} />
        <Route path="/mis-contratos" element={<ProtectedRoute><MyContracts /></ProtectedRoute>} />
        <Route path="/mis-solicitudes" element={<ProtectedRoute><MyRequests /></ProtectedRoute>} />

        {/* Administrador */}
        <Route path="/admin" element={<ProtectedRoute requireAdmin><Dashboard /></ProtectedRoute>} />
        <Route path="/admin/inmuebles" element={<ProtectedRoute requireAdmin><PropertiesAdmin /></ProtectedRoute>} />
        <Route path="/admin/inmuebles/nuevo" element={<ProtectedRoute requireAdmin><PropertyForm /></ProtectedRoute>} />
        <Route path="/admin/inmuebles/:id/editar" element={<ProtectedRoute requireAdmin><PropertyForm /></ProtectedRoute>} />
        <Route path="/admin/usuarios" element={<ProtectedRoute requireAdmin><UsersAdmin /></ProtectedRoute>} />
        <Route path="/admin/usuarios/nuevo-admin" element={<ProtectedRoute requireAdmin><RegisterAdmin /></ProtectedRoute>} />
        <Route path="/admin/solicitudes" element={<ProtectedRoute requireAdmin><RequestsAdmin /></ProtectedRoute>} />
        <Route path="/admin/contratos" element={<ProtectedRoute requireAdmin><ContractsAdmin /></ProtectedRoute>} />
        <Route path="/admin/rentas" element={<ProtectedRoute requireAdmin><RentsAdmin /></ProtectedRoute>} />
        <Route path="/admin/ventas" element={<ProtectedRoute requireAdmin><SalesAdmin /></ProtectedRoute>} />
        <Route path="/admin/auditoria" element={<ProtectedRoute requireAdmin><AuditAdmin /></ProtectedRoute>} />
        <Route path="/admin/catalogos" element={<ProtectedRoute requireAdmin><CatalogsAdmin /></ProtectedRoute>} />
        <Route path="/admin/pagos" element={<ProtectedRoute requireAdmin><PaymentsAdmin /></ProtectedRoute>} />
        <Route path="/admin/visitas" element={<ProtectedRoute requireAdmin><VisitsAdmin /></ProtectedRoute>} />
        <Route path="/admin/contactos" element={<ProtectedRoute requireAdmin><ContactsAdmin /></ProtectedRoute>} />

        <Route path="*" element={<NotFound />} />
      </Routes>
    </Layout>
  )
}
