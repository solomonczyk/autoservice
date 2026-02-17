import { Calendar, dateFnsLocalizer } from 'react-big-calendar'
import { format } from 'date-fns'
import { parse } from 'date-fns'
import { startOfWeek } from 'date-fns'
import { getDay } from 'date-fns'
import { enUS } from 'date-fns/locale/en-US'
import { ru } from 'date-fns/locale/ru'
import 'react-big-calendar/lib/css/react-big-calendar.css'
import { useMemo, useState } from 'react'
import 'react-big-calendar/lib/css/react-big-calendar.css'
import { useAppointments } from '@/hooks/useAppointments'
import AppointmentEditDialog from './AppointmentEditDialog'
import { Appointment } from '@/hooks/useAppointments'

const locales = {
    'en-US': enUS,
    'ru': ru,
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
    const [selectedAppointment, setSelectedAppointment] = useState<Appointment | null>(null);
    const [isEditDialogOpen, setIsEditDialogOpen] = useState(false);

    const events = useMemo(() => {
        return appointments
            .filter(appt => {
                const status = appt.status.toUpperCase();
                return status !== 'WAITLIST' && status !== 'CANCELLED';
            })
            .map(appt => ({
                id: appt.id,
                title: `Заказ #${appt.id}`,
                start: new Date(appt.start_time),
                end: new Date(appt.end_time),
                resource: appt
            }))
    }, [appointments])

    const handleSelectEvent = (event: any) => {
        setSelectedAppointment(event.resource);
        setIsEditDialogOpen(true);
    };

    return (
        <div className="space-y-4">
            <div className="h-[600px] bg-card border border-border p-4 rounded-xl shadow-sm">
                <Calendar
                    localizer={localizer}
                    events={events}
                    startAccessor="start"
                    endAccessor="end"
                    style={{ height: '100%' }}
                    defaultView="week"
                    views={['month', 'week', 'day']}
                    culture="ru"
                    onSelectEvent={handleSelectEvent}
                    messages={{
                        next: "След",
                        previous: "Пред",
                        today: "Сегодня",
                        month: "Месяц",
                        week: "Неделя",
                        day: "День",
                        agenda: "Повестка",
                        date: "Дата",
                        time: "Время",
                        event: "Событие",
                        noEventsInRange: "Записей нет",
                        allDay: "Весь день",
                        showMore: (total: number) => `+ еще ${total}`
                    }}
                />
            </div>

            <AppointmentEditDialog
                appointment={selectedAppointment}
                isOpen={isEditDialogOpen}
                onClose={() => setIsEditDialogOpen(false)}
            />
        </div>
    )
}
