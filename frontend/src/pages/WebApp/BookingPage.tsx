import { useEffect, useState, useMemo } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { api } from "@/lib/api";
import { format, addDays, isSameDay, startOfDay } from 'date-fns';
import { ru } from 'date-fns/locale';
import { Calendar, Clock, ChevronLeft, CheckCircle2 } from 'lucide-react';

declare global {
    interface Window {
        Telegram: any;
    }
}

interface Service {
    id: number;
    name: string;
    duration_minutes: number;
    base_price: number;
}

export default function BookingPage() {
    const [services, setServices] = useState<Service[]>([]);
    const [loading, setLoading] = useState(true);
    const [selectedService, setSelectedService] = useState<Service | null>(null);
    const [selectedDate, setSelectedDate] = useState<Date>(startOfDay(new Date()));
    const [availableSlots, setAvailableSlots] = useState<string[]>([]);
    const [selectedTime, setSelectedTime] = useState<string>('');
    const [slotsLoading, setSlotsLoading] = useState(false);

    const tg = window.Telegram?.WebApp;

    useEffect(() => {
        tg?.ready();
        tg?.expand();

        tg?.MainButton.setParams({
            text: 'ЗАПИСАТЬСЯ',
            color: '#2481cc'
        });

        api.get('/services/')
            .then(res => setServices(res.data))
            .catch(err => console.error("Failed to fetch services", err))
            .finally(() => setLoading(false));
    }, []);

    // Generate next 14 days
    const dates = useMemo(() => {
        return Array.from({ length: 14 }).map((_, i) => addDays(startOfDay(new Date()), i));
    }, []);

    // Fetch slots when service or date changes
    useEffect(() => {
        if (selectedService && selectedDate) {
            setSlotsLoading(true);
            setSelectedTime('');
            const dateStr = format(selectedDate, 'yyyy-MM-dd');

            api.get('/slots/available', {
                params: {
                    shop_id: 1, // Default for MVP
                    service_duration: selectedService.duration_minutes,
                    target_date: dateStr
                }
            })
                .then(res => setAvailableSlots(res.data))
                .catch(err => {
                    console.error("Failed to fetch slots", err);
                    setAvailableSlots([]);
                })
                .finally(() => setSlotsLoading(false));
        }
    }, [selectedService, selectedDate]);

    const handleSubmit = () => {
        if (!selectedService || !selectedTime) return;

        const data = {
            service_id: selectedService.id,
            date: selectedTime // Backend already returns ISO strings
        };

        if (tg) {
            tg.sendData(JSON.stringify(data));
        } else {
            console.log("WebApp Data would be sent:", data);
            alert("Запись создана! (В Telegram данные были бы отправлены боту)");
        }
    };

    useEffect(() => {
        if (selectedService && selectedTime) {
            tg?.MainButton.show();
            tg?.MainButton.onClick(handleSubmit);
        } else {
            tg?.MainButton.hide();
        }
        return () => {
            tg?.MainButton.offClick(handleSubmit);
        }
    }, [selectedService, selectedTime]);

    const handleClose = () => {
        tg?.close();
    };

    if (selectedService) {
        return (
            <div className="p-4 bg-background min-h-screen text-foreground space-y-6 animate-in fade-in duration-500">
                <div className="flex items-center gap-2 mb-2">
                    <Button variant="ghost" size="icon" onClick={() => setSelectedService(null)} className="-ml-2">
                        <ChevronLeft className="w-6 h-6" />
                    </Button>
                    <h1 className="text-xl font-bold">Детали записи</h1>
                </div>

                {/* Service Summary Card */}
                <div className="bg-primary/5 p-4 rounded-xl border border-primary/20 flex justify-between items-center transition-all">
                    <div>
                        <div className="font-bold text-lg">{selectedService.name}</div>
                        <div className="text-muted-foreground text-sm">{selectedService.duration_minutes} мин • {selectedService.base_price} ₽</div>
                    </div>
                    <CheckCircle2 className="text-primary w-6 h-6 opacity-20" />
                </div>

                {/* Date Selection */}
                <div className="space-y-3">
                    <div className="flex items-center gap-2 text-sm font-semibold opacity-70">
                        <Calendar className="w-4 h-4" />
                        ВЫБЕРИТЕ ДАТУ
                    </div>
                    <div className="flex gap-2 overflow-x-auto pb-2 no-scrollbar">
                        {dates.map((d) => {
                            const isSelected = isSameDay(d, selectedDate);
                            return (
                                <button
                                    key={d.toISOString()}
                                    onClick={() => setSelectedDate(d)}
                                    className={`flex-shrink-0 w-14 h-16 rounded-xl flex flex-col items-center justify-center transition-all ${isSelected
                                            ? 'bg-primary text-primary-foreground shadow-lg shadow-primary/20 scale-105'
                                            : 'bg-accent/40 hover:bg-accent'
                                        }`}
                                >
                                    <span className="text-[10px] uppercase font-bold opacity-60">
                                        {format(d, 'EEE', { locale: ru })}
                                    </span>
                                    <span className="text-lg font-bold">
                                        {format(d, 'd')}
                                    </span>
                                </button>
                            );
                        })}
                    </div>
                </div>

                {/* Time Selection */}
                <div className="space-y-3">
                    <div className="flex items-center gap-2 text-sm font-semibold opacity-70">
                        <Clock className="w-4 h-4" />
                        ВЫБЕРИТЕ ВРЕМЯ
                    </div>

                    {slotsLoading ? (
                        <div className="grid grid-cols-4 gap-2">
                            {[1, 2, 3, 4, 5, 6, 7, 8].map(i => (
                                <div key={i} className="h-10 bg-accent/20 animate-pulse rounded-lg" />
                            ))}
                        </div>
                    ) : availableSlots.length > 0 ? (
                        <div className="grid grid-cols-4 gap-2">
                            {availableSlots.map((slot) => {
                                const isSelected = selectedTime === slot;
                                const timeLabel = format(new Date(slot), 'HH:mm');
                                return (
                                    <button
                                        key={slot}
                                        onClick={() => setSelectedTime(slot)}
                                        className={`h-10 rounded-lg flex items-center justify-center text-sm font-medium transition-all ${isSelected
                                                ? 'bg-primary text-primary-foreground shadow-md'
                                                : 'bg-accent/40 hover:bg-accent'
                                            }`}
                                    >
                                        {timeLabel}
                                    </button>
                                );
                            })}
                        </div>
                    ) : (
                        <div className="text-center py-8 bg-accent/10 rounded-xl border border-dashed border-accent">
                            <p className="text-muted-foreground text-sm">Нет свободных слотов на эту дату</p>
                        </div>
                    )}
                </div>

                <div className="pt-4">
                    <Button
                        className="w-full h-14 text-lg font-bold shadow-xl shadow-primary/20"
                        disabled={!selectedTime}
                        onClick={handleSubmit}
                    >
                        ПОДТВЕРДИТЬ ЗАПИСЬ
                    </Button>
                </div>
            </div>
        )
    }

    return (
        <div className="p-4 max-w-md mx-auto min-h-screen bg-background text-foreground animate-in fade-in duration-500">
            <h1 className="text-2xl font-black mb-6 tracking-tight">ВЫБЕРИТЕ УСЛУГУ</h1>

            <div className="space-y-4">
                {services.map(service => (
                    <Card
                        key={service.id}
                        className="overflow-hidden border-none bg-accent/30 hover:bg-accent/50 transition-all active:scale-[0.98] cursor-pointer"
                        onClick={() => setSelectedService(service)}
                    >
                        <CardHeader className="p-4 pb-1">
                            <CardTitle className="text-lg flex justify-between items-start">
                                <span className="font-bold">{service.name}</span>
                                <span className="text-primary font-black">{service.base_price} ₽</span>
                            </CardTitle>
                        </CardHeader>
                        <CardContent className="p-4 pt-0">
                            <div className="flex items-center gap-1.5 text-muted-foreground text-sm">
                                <Clock className="w-3.5 h-3.5" />
                                {service.duration_minutes} мин.
                            </div>
                        </CardContent>
                    </Card>
                ))}
            </div>

            {loading && (
                <div className="space-y-4 pt-4">
                    {[1, 2, 3].map(i => (
                        <div key={i} className="h-24 bg-accent/20 animate-pulse rounded-xl" />
                    ))}
                </div>
            )}

            {!loading && services.length === 0 && (
                <div className="text-center py-20 opacity-50">
                    Услуги не найдены.
                </div>
            )}

            <div className="mt-12 text-center">
                <Button variant="ghost" size="sm" onClick={handleClose} className="opacity-50 hover:opacity-100">Закрыть</Button>
            </div>
        </div>
    );
}
