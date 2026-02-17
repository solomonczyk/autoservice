import { useState, useEffect } from 'react';
import { Appointment } from '@/hooks/useAppointments';
import { useServices } from '@/hooks/useServices';
import { useUpdateAppointment } from '@/hooks/useUpdateAppointment';
import { Button } from '@/components/ui/button';
import { X } from 'lucide-react';

interface AppointmentEditDialogProps {
    appointment: Appointment | null;
    isOpen: boolean;
    onClose: () => void;
}

export default function AppointmentEditDialog({ appointment, isOpen, onClose }: AppointmentEditDialogProps) {
    const { data: services = [] } = useServices();
    const updateMutation = useUpdateAppointment();

    const [serviceId, setServiceId] = useState<number>(0);
    const [startTime, setStartTime] = useState<string>('');

    useEffect(() => {
        if (appointment) {
            setServiceId(appointment.service_id);
            // Format for datetime-local input: YYYY-MM-DDTHH:mm
            const date = new Date(appointment.start_time);
            const formattedDate = date.toISOString().slice(0, 16);
            setStartTime(formattedDate);
        }
    }, [appointment]);

    if (!isOpen || !appointment) return null;

    const handleSave = () => {
        updateMutation.mutate({
            id: appointment.id,
            service_id: serviceId,
            start_time: new Date(startTime).toISOString(),
        }, {
            onSuccess: () => onClose(),
        });
    };

    return (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/60 backdrop-blur-sm p-4 animate-in fade-in duration-200">
            <div className="bg-card text-foreground border border-border rounded-xl shadow-2xl w-full max-w-md overflow-hidden animate-in zoom-in-95 duration-200">
                <div className="flex items-center justify-between p-4 border-b border-border bg-muted/30">
                    <h3 className="text-lg font-bold">Редактировать запись #{appointment.id}</h3>
                    <button onClick={onClose} className="p-2 hover:bg-accent/10 hover:text-accent rounded-full transition-colors">
                        <X size={20} />
                    </button>
                </div>

                <div className="p-6 space-y-4">
                    <div>
                        <label className="block text-xs font-bold uppercase text-muted-foreground mb-1.5">Услуга</label>
                        <select
                            value={serviceId}
                            onChange={(e) => setServiceId(Number(e.target.value))}
                            className="w-full p-2.5 bg-background border border-border rounded-lg text-foreground focus:ring-2 focus:ring-primary focus:outline-none transition-all"
                        >
                            {services.map(s => (
                                <option key={s.id} value={s.id}>{s.name} ({s.duration_minutes} мин)</option>
                            ))}
                        </select>
                    </div>

                    <div>
                        <label className="block text-xs font-bold uppercase text-muted-foreground mb-1.5">Дата и время</label>
                        <input
                            type="datetime-local"
                            value={startTime}
                            onChange={(e) => setStartTime(e.target.value)}
                            className="w-full p-2.5 bg-background border border-border rounded-lg text-foreground focus:ring-2 focus:ring-primary focus:outline-none transition-all"
                        />
                    </div>
                </div>

                <div className="flex justify-end gap-3 p-4 bg-muted/30 border-t border-border">
                    <Button variant="ghost" onClick={onClose} className="font-semibold">Отмена</Button>
                    <Button
                        onClick={handleSave}
                        disabled={updateMutation.isPending}
                        className="font-bold"
                    >
                        {updateMutation.isPending ? 'Сохранение...' : 'Сохранить'}
                    </Button>
                </div>
            </div>
        </div>
    );
}
