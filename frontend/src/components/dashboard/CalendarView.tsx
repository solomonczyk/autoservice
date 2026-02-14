import { Calendar, dateFnsLocalizer } from 'react-big-calendar'
import format from 'date-fns/format'
import parse from 'date-fns/parse'
import startOfWeek from 'date-fns/startOfWeek'
import getDay from 'date-fns/getDay'
import enUS from 'date-fns/locale/en-US'
import 'react-big-calendar/lib/css/react-big-calendar.css'
import { useAppointments } from '@/hooks/useAppointments'
import { useMemo } from 'react'

const locales = {
    'en-US': enUS,
}

const localizer = dateFnsLocalizer({
    format,
    parse,
    startOfWeek,
    getDay,
    locales,
})

export default function CalendarView() {
    const { data: appointments = [] } = useAppointments()

    const events = useMemo(() => {
        return appointments.map(appt => ({
            id: appt.id,
            title: `Service #${appt.service_id}`, // In real app, fetch service name
            start: new Date(appt.start_time),
            end: new Date(appt.end_time),
            resource: appt
        }))
    }, [appointments])

    return (
        <div className="h-[600px] bg-white p-4 rounded-lg shadow-sm">
            <Calendar
                localizer={localizer}
                events={events}
                startAccessor="start"
                endAccessor="end"
                style={{ height: '100%' }}
                defaultView="week"
                views={['month', 'week', 'day']}
            />
        </div>
    )
}
