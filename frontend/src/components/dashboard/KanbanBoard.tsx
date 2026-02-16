import React, { useMemo } from 'react';
import { useAppointments, Appointment } from '@/hooks/useAppointments';
import { DndContext, DragOverlay, useDraggable, useDroppable, DragEndEvent } from '@dnd-kit/core';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { cn } from '@/lib/utils';
import { format } from 'date-fns';

const COLUMNS = [
    { id: 'new', title: 'Новая' },
    { id: 'confirmed', title: 'Подтверждена' },
    { id: 'in_progress', title: 'В работе' },
    { id: 'done', title: 'Готова' },
];

function DraggableCard({ appointment }: { appointment: Appointment }) {
    const { attributes, listeners, setNodeRef, transform } = useDraggable({
        id: appointment.id,
        data: appointment,
    });

    const style = transform ? {
        transform: `translate3d(${transform.x}px, ${transform.y}px, 0)`,
    } : undefined;

    return (
        <div ref={setNodeRef} style={style} {...listeners} {...attributes} className="mb-2 touch-none">
            <Card className="cursor-move hover:shadow-md transition-shadow">
                <CardContent className="p-3">
                    <div className="font-medium">Заказ #{appointment.id}</div>
                    <div className="text-xs text-muted-foreground">
                        {format(new Date(appointment.start_time), 'HH:mm')}
                    </div>
                </CardContent>
            </Card>
        </div>
    );
}

function DroppableColumn({ id, title, appointments }: { id: string, title: string, appointments: Appointment[] }) {
    const { setNodeRef } = useDroppable({
        id: id,
    });

    return (
        <div ref={setNodeRef} className="bg-slate-50 dark:bg-slate-800/50 p-4 rounded-lg min-h-[500px] w-full">
            <h3 className="font-semibold mb-4 text-slate-700 dark:text-slate-300">{title}</h3>
            <div className="space-y-2">
                {appointments.map((appt) => (
                    <DraggableCard key={appt.id} appointment={appt} />
                ))}
            </div>
        </div>
    );
}

import { useQueryClient } from "@tanstack/react-query";
import { useWebSocket } from "@/contexts/WebSocketContext";
import { useEffect } from "react";
import { useUpdateAppointmentStatus } from '@/hooks/useUpdateAppointmentStatus';

export default function KanbanBoard() {
    const { data: appointments = [] } = useAppointments();
    const queryClient = useQueryClient();
    const { lastMessage } = useWebSocket();
    const updateStatusMutation = useUpdateAppointmentStatus();

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
            new: [],
            confirmed: [],
            in_progress: [],
            done: [],
            cancelled: []
        };
        appointments.forEach(appt => {
            if (groups[appt.status]) {
                groups[appt.status].push(appt);
            }
        });
        return groups;
    }, [appointments]);

    const handleDragEnd = (event: DragEndEvent) => {
        const { active, over } = event;

        if (over && active.id !== over.id) {
            const newStatus = over.id as string;
            const appointmentId = active.id as number;

            // Find current appointment to check if status actually changed
            const appt = appointments.find(a => a.id === appointmentId);
            if (appt && appt.status !== newStatus) {
                console.log(`Moving ${appointmentId} to ${newStatus}`);
                updateStatusMutation.mutate({ id: appointmentId, status: newStatus });
            }
        }
    };

    return (
        <DndContext onDragEnd={handleDragEnd}>
            <div className="grid grid-cols-1 md:grid-cols-4 gap-6">
                {COLUMNS.map(col => (
                    <DroppableColumn
                        key={col.id}
                        id={col.id}
                        title={col.title}
                        appointments={groupedAppointments[col.id] || []}
                    />
                ))}
            </div>
        </DndContext>
    );
}
