import { Routes, Route } from 'react-router-dom'
import DashboardLayout from '@/components/dashboard/DashboardLayout'
import KanbanPage from '@/pages/KanbanPage'
import CalendarPage from '@/pages/CalendarPage'

function App() {
    return (
        <Routes>
            <Route path="/" element={<DashboardLayout />}>
                <Route index element={<KanbanPage />} />
                <Route path="calendar" element={<CalendarPage />} />
                {/* Add more routes here */}
            </Route>
        </Routes>
    )
}

export default App
