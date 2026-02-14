import React, { useMemo } from 'react';
import { useAppointments, Appointment } from '@/hooks/useAppointments';
import { DndContext, DragOverlay, useDraggable, useDroppable, DragEndEvent } from '@dnd-kit/core';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { cn } from '@/lib/utils';
import { format } from 'date-fns';

const COLUMNS = [
    { id: 'new', title: 'New' },
    { id: 'confirmed', title: 'Confirmed' },
    { id: 'in_progress', title: 'In Progress' },
    { id: 'done', title: 'Done' },
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
                    <div className="font-medium">Appt #{appointment.id}</div>
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

export default function KanbanBoard() {
    const { data: appointments = [] } = useAppointments();
    const queryClient = useQueryClient();
    const { lastMessage } = useWebSocket();

    // Listen for real-time updates
    useEffect(() => {
        if (lastMessage) {
            console.log("WS Update received:", lastMessage);
            // In a real app, we check if message is relevant to appointments
            // For MVP, we just refetch all appointments on any message
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
            cancelled: [] // Add cancelled if needed in board
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
            // TODO: Call update mutation
            const newStatus = over.id as string;
            const appointmentId = active.id;
            console.log(`Moved ${appointmentId} to ${newStatus}`);
            // updateStatusMutation.mutate({ id: appointmentId, status: newStatus });
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
