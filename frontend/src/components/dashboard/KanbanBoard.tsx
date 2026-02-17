import { useMemo, useState, DragEvent } from 'react';
import { useAppointments, Appointment } from '@/hooks/useAppointments';
import { Card, CardContent } from '@/components/ui/card';
import { format } from 'date-fns';
import { Edit } from 'lucide-react';
import AppointmentEditDialog from './AppointmentEditDialog';
import { useQueryClient } from "@tanstack/react-query";
import { useWebSocket } from "@/contexts/WebSocketContext";
import { useEffect } from "react";
import { useUpdateAppointmentStatus } from '@/hooks/useUpdateAppointmentStatus';

const COLUMNS = [
    { id: 'waitlist', title: 'Лист ожидания' },
    { id: 'new', title: 'Новая' },
    { id: 'confirmed', title: 'Подтверждена' },
    { id: 'in_progress', title: 'В работе' },
    { id: 'done', title: 'Готова' },
];

function DraggableCard({ appointment, onEdit, onDragStart }: {
    appointment: Appointment,
    onEdit: (appt: Appointment) => void,
    onDragStart: (e: DragEvent, appt: Appointment) => void,
}) {
    return (
        <div
            draggable
            onDragStart={(e) => onDragStart(e, appointment)}
            className="mb-2 group relative cursor-grab active:cursor-grabbing"
        >
            <Card className="hover:shadow-md transition-shadow border-l-4 border-l-primary/40">
                <CardContent className="p-3">
                    <div className="flex justify-between items-start">
                        <div className="font-medium">Заказ #{appointment.id}</div>
                        <button
                            onClick={(e) => {
                                e.stopPropagation();
                                onEdit(appointment);
                            }}
                            className="opacity-0 group-hover:opacity-100 p-1 hover:bg-accent/10 text-muted-foreground hover:text-accent rounded transition-all duration-200"
                        >
                            <Edit size={14} className="text-muted-foreground" />
                        </button>
                    </div>
                    <div className="text-xs text-muted-foreground">
                        {format(new Date(appointment.start_time), 'HH:mm')}
                    </div>
                </CardContent>
            </Card>
        </div>
    );
}

function DroppableColumn({ id, title, appointments, onEdit, onDragStart, onDrop, isOver }: {
    id: string,
    title: string,
    appointments: Appointment[],
    onEdit: (appt: Appointment) => void,
    onDragStart: (e: DragEvent, appt: Appointment) => void,
    onDrop: (e: DragEvent, columnId: string) => void,
    isOver: boolean,
}) {
    return (
        <div
            onDragOver={(e) => {
                e.preventDefault();
                e.dataTransfer.dropEffect = 'move';
            }}
            onDragEnter={(e) => e.preventDefault()}
            onDrop={(e) => onDrop(e, id)}
            className={`p-4 rounded-xl min-h-[500px] w-full transition-colors duration-200 border border-transparent ${isOver
                ? 'bg-primary/10 ring-2 ring-primary/30 border-primary/20'
                : 'bg-muted/50 hover:bg-muted/80'
                }`}
        >
            <h3 className="font-semibold mb-4 text-foreground flex items-center justify-between">
                {title}
                {appointments.length > 0 && (
                    <span className="ml-2 text-xs font-bold bg-primary/20 text-primary px-2.5 py-0.5 rounded-full">
                        {appointments.length}
                    </span>
                )}
            </h3>
            <div className="space-y-2">
                {appointments.map((appt) => (
                    <DraggableCard
                        key={appt.id}
                        appointment={appt}
                        onEdit={onEdit}
                        onDragStart={onDragStart}
                    />
                ))}
            </div>
        </div>
    );
}

export default function KanbanBoard() {
    const { data: appointments = [] } = useAppointments();
    const queryClient = useQueryClient();
    const { lastMessage } = useWebSocket();
    const updateStatusMutation = useUpdateAppointmentStatus();

    const [selectedAppointment, setSelectedAppointment] = useState<Appointment | null>(null);
    const [isEditDialogOpen, setIsEditDialogOpen] = useState(false);
    const [dragOverColumn, setDragOverColumn] = useState<string | null>(null);
    const [draggedAppointment, setDraggedAppointment] = useState<Appointment | null>(null);

    // Listen for real-time updates
    useEffect(() => {
        if (lastMessage) {
            console.log("WS Update received:", lastMessage);
            queryClient.invalidateQueries({ queryKey: ["appointments"] });
        }
    }, [lastMessage, queryClient]);

    // Group appointments by status
    const groupedAppointments = useMemo(() => {
        const groups: Record<string, Appointment[]> = {
            waitlist: [],
            new: [],
            confirmed: [],
            in_progress: [],
            done: [],
            cancelled: []
        };
        appointments.forEach(appt => {
            const status = appt.status.toLowerCase();
            if (groups[status]) {
                groups[status].push(appt);
            }
        });
        return groups;
    }, [appointments]);

    const handleDragStart = (e: DragEvent, appointment: Appointment) => {
        setDraggedAppointment(appointment);
        e.dataTransfer.setData('text/plain', String(appointment.id));
        e.dataTransfer.effectAllowed = 'move';
    };

    const handleDrop = (e: DragEvent, columnId: string) => {
        e.preventDefault();
        setDragOverColumn(null);

        if (!draggedAppointment) return;

        const newStatus = columnId.toUpperCase();
        if (draggedAppointment.status.toUpperCase() !== newStatus) {
            console.log(`Moving ${draggedAppointment.id} to ${newStatus}`);
            updateStatusMutation.mutate(
                { id: draggedAppointment.id, status: newStatus },
                {
                    onError: (error) => {
                        console.error('Failed to update status:', error);
                        alert('Не удалось обновить статус. Проверьте права доступа.');
                    }
                }
            );
        }
        setDraggedAppointment(null);
    };

    const handleEdit = (appt: Appointment) => {
        setSelectedAppointment(appt);
        setIsEditDialogOpen(true);
    };

    return (
        <>
            <div
                className="grid grid-cols-1 md:grid-cols-5 gap-6"
                onDragOver={(e) => {
                    e.preventDefault();
                    // Find which column we're over
                    const target = (e.target as HTMLElement).closest('[data-column-id]');
                    if (target) {
                        setDragOverColumn(target.getAttribute('data-column-id'));
                    }
                }}
                onDragEnd={() => {
                    setDragOverColumn(null);
                    setDraggedAppointment(null);
                }}
            >
                {COLUMNS.map(col => (
                    <div key={col.id} data-column-id={col.id}>
                        <DroppableColumn
                            id={col.id}
                            title={col.title}
                            appointments={groupedAppointments[col.id] || []}
                            onEdit={handleEdit}
                            onDragStart={handleDragStart}
                            onDrop={handleDrop}
                            isOver={dragOverColumn === col.id}
                        />
                    </div>
                ))}
            </div>

            <AppointmentEditDialog
                appointment={selectedAppointment}
                isOpen={isEditDialogOpen}
                onClose={() => setIsEditDialogOpen(false)}
            />
        </>
    );
}
