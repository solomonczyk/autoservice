import { useState } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { api } from '@/lib/api';
import { Plus, Edit2, Trash2, Save, Clock, DollarSign } from 'lucide-react';
import { useForm } from 'react-hook-form';

interface Service {
    id: number;
    name: string;
    duration_minutes: number;
    base_price: number;
}

interface ServiceFormData {
    name: string;
    duration_minutes: number;
    base_price: number;
}

export default function SettingsPage() {
    const queryClient = useQueryClient();
    const [isEditing, setIsEditing] = useState<Service | null>(null);
    const [isCreating, setIsCreating] = useState(false);

    const { data: services = [], isLoading } = useQuery({
        queryKey: ['services'],
        queryFn: async () => {
            const res = await api.get<Service[]>('/services/');
            return res.data;
        }
    });

    const createMutation = useMutation({
        mutationFn: (data: ServiceFormData) => api.post('/services/', data),
        onSuccess: () => {
            queryClient.invalidateQueries({ queryKey: ['services'] });
            setIsCreating(false);
        }
    });

    const updateMutation = useMutation({
        mutationFn: ({ id, data }: { id: number, data: ServiceFormData }) => api.put(`/services/${id}`, data),
        onSuccess: () => {
            queryClient.invalidateQueries({ queryKey: ['services'] });
            setIsEditing(null);
        }
    });

    const deleteMutation = useMutation({
        mutationFn: (id: number) => api.delete(`/services/${id}`),
        onSuccess: () => {
            queryClient.invalidateQueries({ queryKey: ['services'] });
        }
    });

    const ServiceForm = ({ initialData, onSubmit, onCancel }: { initialData?: Service, onSubmit: (data: ServiceFormData) => void, onCancel: () => void }) => {
        const { register, handleSubmit } = useForm<ServiceFormData>({
            defaultValues: initialData || { name: '', duration_minutes: 60, base_price: 1000 }
        });

        return (
            <form onSubmit={handleSubmit(onSubmit)} className="bg-card border border-border p-4 rounded-xl space-y-4 animate-in fade-in zoom-in-95 duration-200">
                <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                    <div className="space-y-2">
                        <label className="text-xs font-bold text-muted-foreground uppercase">Название услуги</label>
                        <input
                            {...register('name', { required: true })}
                            className="w-full bg-background border border-border rounded-lg px-3 py-2 text-foreground focus:ring-2 focus:ring-primary focus:outline-none"
                            placeholder="Например: Замена масла"
                        />
                    </div>
                    <div className="space-y-2">
                        <label className="text-xs font-bold text-muted-foreground uppercase">Длительность (мин)</label>
                        <div className="relative">
                            <Clock className="absolute left-3 top-2.5 h-4 w-4 text-muted-foreground" />
                            <input
                                type="number"
                                {...register('duration_minutes', { required: true, min: 15 })}
                                className="w-full bg-background border border-border rounded-lg pl-9 pr-3 py-2 text-foreground focus:ring-2 focus:ring-primary focus:outline-none placeholder:text-muted-foreground/50"
                                placeholder="60"
                            />
                        </div>
                    </div>
                    <div className="space-y-2">
                        <label className="text-xs font-bold text-muted-foreground uppercase">Цена (₽)</label>
                        <div className="relative">
                            <DollarSign className="absolute left-3 top-2.5 h-4 w-4 text-muted-foreground" />
                            <input
                                type="number"
                                {...register('base_price', { required: true, min: 0 })}
                                className="w-full bg-background border border-border rounded-lg pl-9 pr-3 py-2 text-foreground focus:ring-2 focus:ring-primary focus:outline-none placeholder:text-muted-foreground/50"
                                placeholder="1000"
                            />
                        </div>
                    </div>
                </div>
                <div className="flex justify-end gap-2 pt-2">
                    <button type="button" onClick={onCancel} className="px-4 py-2 rounded-lg hover:bg-accent/10 text-muted-foreground hover:text-foreground transition-colors font-medium text-sm">
                        Отмена
                    </button>
                    <button type="submit" className="px-4 py-2 bg-primary text-primary-foreground rounded-lg hover:bg-primary/90 transition-colors font-bold text-sm flex items-center gap-2">
                        <Save className="w-4 h-4" />
                        Сохранить
                    </button>
                </div>
            </form>
        );
    };

    return (
        <div className="space-y-6">
            <div className="flex items-center justify-between">
                <div>
                    <h2 className="text-2xl font-bold text-foreground">Управление услугами</h2>
                    <p className="text-muted-foreground text-sm">Добавляйте и редактируйте услуги автосервиса</p>
                </div>
                {!isCreating && (
                    <button
                        onClick={() => setIsCreating(true)}
                        className="flex items-center gap-2 bg-primary text-primary-foreground px-4 py-2 rounded-xl font-bold hover:bg-primary/90 transition-all shadow-lg shadow-primary/20"
                    >
                        <Plus className="w-5 h-5" />
                        Добавить услугу
                    </button>
                )}
            </div>

            {isCreating && (
                <ServiceForm
                    onSubmit={(data) => createMutation.mutate(data)}
                    onCancel={() => setIsCreating(false)}
                />
            )}

            <div className="grid gap-4">
                {isLoading ? (
                    <div className="text-center py-10 text-muted-foreground">Загрузка услуг...</div>
                ) : services.length === 0 ? (
                    <div className="text-center py-10 text-muted-foreground bg-card rounded-xl border border-dashed border-border">
                        Список услуг пуст
                    </div>
                ) : (
                    services.map(service => (
                        <div key={service.id}>
                            {isEditing?.id === service.id ? (
                                <ServiceForm
                                    initialData={service}
                                    onSubmit={(data) => updateMutation.mutate({ id: service.id, data })}
                                    onCancel={() => setIsEditing(null)}
                                />
                            ) : (
                                <div className="bg-card border border-border rounded-xl p-4 flex items-center justify-between group hover:border-primary/50 transition-all duration-200">
                                    <div className="flex items-center gap-4">
                                        <div className="bg-primary/10 p-3 rounded-lg text-primary font-bold text-lg min-w-[60px] text-center">
                                            #{service.id}
                                        </div>
                                        <div>
                                            <h3 className="font-bold text-lg text-foreground">{service.name}</h3>
                                            <div className="flex items-center gap-4 text-sm text-muted-foreground mt-1">
                                                <span className="flex items-center gap-1.5 bg-accent/5 px-2 py-0.5 rounded-md">
                                                    <Clock className="w-3.5 h-3.5" />
                                                    {service.duration_minutes} мин
                                                </span>
                                                <span className="flex items-center gap-1.5 bg-green-500/10 text-green-500 px-2 py-0.5 rounded-md font-medium">
                                                    <DollarSign className="w-3.5 h-3.5" />
                                                    {service.base_price} ₽
                                                </span>
                                            </div>
                                        </div>
                                    </div>
                                    <div className="flex items-center gap-2 opacity-0 group-hover:opacity-100 transition-opacity">
                                        <button
                                            onClick={() => setIsEditing(service)}
                                            className="p-2 hover:bg-accent/10 text-muted-foreground hover:text-primary rounded-lg transition-colors"
                                            title="Редактировать"
                                        >
                                            <Edit2 className="w-5 h-5" />
                                        </button>
                                        <button
                                            onClick={() => {
                                                if (confirm('Вы уверены, что хотите удалить эту услугу?')) {
                                                    deleteMutation.mutate(service.id);
                                                }
                                            }}
                                            className="p-2 hover:bg-destructive/10 text-muted-foreground hover:text-destructive rounded-lg transition-colors"
                                            title="Удалить"
                                        >
                                            <Trash2 className="w-5 h-5" />
                                        </button>
                                    </div>
                                </div>
                            )}
                        </div>
                    ))
                )}
            </div>
        </div>
    );
}
