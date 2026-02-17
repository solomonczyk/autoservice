import { useMemo } from 'react';
import { useAppointments, Appointment } from '@/hooks/useAppointments';
import { DndContext, useDraggable, useDroppable, DragEndEvent, PointerSensor, MouseSensor, useSensor, useSensors, closestCorners } from '@dnd-kit/core';
import { Card, CardContent } from '@/components/ui/card';
import { format } from 'date-fns';

const COLUMNS = [
    { id: 'waitlist', title: 'Лист ожидания' },
    { id: 'new', title: 'Новая' },
    { id: 'confirmed', title: 'Подтверждена' },
    { id: 'in_progress', title: 'В работе' },
    { id: 'done', title: 'Готова' },
];

import { Edit } from 'lucide-react';
import AppointmentEditDialog from './AppointmentEditDialog';

function DraggableCard({ appointment, onEdit }: { appointment: Appointment, onEdit: (appt: Appointment) => void }) {
    const { attributes, listeners, setNodeRef, transform } = useDraggable({
        id: appointment.id,
        data: appointment,
    });

    const style = transform ? {
        transform: `translate3d(${transform.x}px, ${transform.y}px, 0)`,
    } : undefined;

    return (
        <div ref={setNodeRef} style={style} {...listeners} {...attributes} className="mb-2 touch-none group relative">
            <Card className="cursor-move hover:shadow-md transition-shadow">
                <CardContent className="p-3">
                    <div className="flex justify-between items-start">
                        <div className="font-medium">Заказ #{appointment.id}</div>
                        <button
                            onPointerDown={e => e.stopPropagation()} // Prevent drag start when clicking edit
                            onClick={(e) => {
                                e.stopPropagation();
                                onEdit(appointment);
                            }}
                            className="opacity-0 group-hover:opacity-100 p-1 hover:bg-gray-100 dark:hover:bg-gray-700 rounded transition-opacity"
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

function DroppableColumn({ id, title, appointments, onEdit }: { id: string, title: string, appointments: Appointment[], onEdit: (appt: Appointment) => void }) {
    const { setNodeRef } = useDroppable({
        id: id,
    });

    return (
        <div ref={setNodeRef} className="bg-slate-50 dark:bg-slate-800/50 p-4 rounded-lg min-h-[500px] w-full">
            <h3 className="font-semibold mb-4 text-slate-700 dark:text-slate-300">{title}</h3>
            <div className="space-y-2">
                {appointments.map((appt) => (
                    <DraggableCard key={appt.id} appointment={appt} onEdit={onEdit} />
                ))}
            </div>
        </div>
    );
}

import { useQueryClient } from "@tanstack/react-query";
import { useWebSocket } from "@/contexts/WebSocketContext";
import { useEffect, useState } from "react";
import { useUpdateAppointmentStatus } from '@/hooks/useUpdateAppointmentStatus';

export default function KanbanBoard() {
    const { data: appointments = [] } = useAppointments();
    const queryClient = useQueryClient();
    const { lastMessage } = useWebSocket();
    const updateStatusMutation = useUpdateAppointmentStatus();

    const [selectedAppointment, setSelectedAppointment] = useState<Appointment | null>(null);
    const [isEditDialogOpen, setIsEditDialogOpen] = useState(false);

    const pointerSensor = useSensor(PointerSensor, {
        activationConstraint: { distance: 5 },
    });
    const mouseSensor = useSensor(MouseSensor, {
        activationConstraint: { distance: 5 },
    });
    const sensors = useSensors(pointerSensor, mouseSensor);

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

    const handleDragEnd = (event: DragEndEvent) => {
        const { active, over } = event;

        if (over && active.id !== over.id) {
            const newStatus = (over.id as string).toUpperCase();
            const appointmentId = active.id as number;

            // Find current appointment to check if status actually changed
            const appt = appointments.find(a => a.id === appointmentId);
            if (appt && appt.status.toUpperCase() !== newStatus) {
                console.log(`Moving ${appointmentId} to ${newStatus}`);
                updateStatusMutation.mutate({ id: appointmentId, status: newStatus });
            }
        }
    };

    const handleEdit = (appt: Appointment) => {
        setSelectedAppointment(appt);
        setIsEditDialogOpen(true);
    };

    return (
        <>
            <DndContext sensors={sensors} collisionDetection={closestCorners} onDragEnd={handleDragEnd}>
                <div className="grid grid-cols-1 md:grid-cols-5 gap-6">
                    {COLUMNS.map(col => (
                        <DroppableColumn
                            key={col.id}
                            id={col.id}
                            title={col.title}
                            appointments={groupedAppointments[col.id] || []}
                            onEdit={handleEdit}
                        />
                    ))}
                </div>
            </DndContext>

            <AppointmentEditDialog
                appointment={selectedAppointment}
                isOpen={isEditDialogOpen}
                onClose={() => setIsEditDialogOpen(false)}
            />
        </>
    );
}
