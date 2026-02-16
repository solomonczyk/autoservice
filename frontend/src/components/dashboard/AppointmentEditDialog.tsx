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
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50 p-4">
            <div className="bg-white dark:bg-gray-800 rounded-lg shadow-xl w-full max-w-md overflow-hidden">
                <div className="flex items-center justify-between p-4 border-b dark:border-gray-700">
                    <h3 className="text-lg font-semibold">Редактировать запись #{appointment.id}</h3>
                    <button onClick={onClose} className="p-1 hover:bg-gray-100 dark:hover:bg-gray-700 rounded-full">
                        <X size={20} />
                    </button>
                </div>

                <div className="p-6 space-y-4">
                    <div>
                        <label className="block text-sm font-medium mb-1">Услуга</label>
                        <select
                            value={serviceId}
                            onChange={(e) => setServiceId(Number(e.target.value))}
                            className="w-full p-2 border rounded-md dark:bg-gray-700 dark:border-gray-600"
                        >
                            {services.map(s => (
                                <option key={s.id} value={s.id}>{s.name} ({s.duration_minutes} мин)</option>
                            ))}
                        </select>
                    </div>

                    <div>
                        <label className="block text-sm font-medium mb-1">Дата и время</label>
                        <input
                            type="datetime-local"
                            value={startTime}
                            onChange={(e) => setStartTime(e.target.value)}
                            className="w-full p-2 border rounded-md dark:bg-gray-700 dark:border-gray-600"
                        />
                    </div>
                </div>

                <div className="flex justify-end gap-3 p-4 bg-gray-50 dark:bg-gray-700/50">
                    <Button variant="outline" onClick={onClose}>Отмена</Button>
                    <Button
                        onClick={handleSave}
                        disabled={updateMutation.isPending}
                    >
                        {updateMutation.isPending ? 'Сохранение...' : 'Сохранить'}
                    </Button>
                </div>
            </div>
        </div>
    );
}
