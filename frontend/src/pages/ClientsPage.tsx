
import { useQuery } from '@tanstack/react-query';
import { api } from '@/lib/api';
import { useState } from 'react';
import { Search } from 'lucide-react';

interface Client {
    id: number;
    full_name: string;
    phone: string;
    telegram_id: number;
    vehicle_info?: string;
}

export default function ClientsPage() {
    const [search, setSearch] = useState('');

    const { data: clients = [], isLoading, isError, error } = useQuery({
        queryKey: ['clients'],
        queryFn: async () => {
            const response = await api.get<Client[]>('/clients/');
            return response.data;
        }
    });

    if (isError) {
        return (
            <div className="p-4 text-red-500 bg-red-100 dark:bg-red-900/20 rounded-md">
                Error loading clients: {(error as Error).message}
            </div>
        );
    }

    const filteredClients = clients.filter(client =>
        client.full_name.toLowerCase().includes(search.toLowerCase()) ||
        client.phone.includes(search)
    );

    return (
        <div className="space-y-4">

            <div className="relative max-w-sm">
                <Search className="absolute left-3 top-2.5 h-4 w-4 text-muted-foreground" />
                <input
                    type="text"
                    placeholder="Поиск по имени или телефону..."
                    value={search}
                    onChange={(e) => setSearch(e.target.value)}
                    className="pl-9 pr-4 py-2 border border-border rounded-xl w-full bg-card text-foreground placeholder:text-muted-foreground focus:outline-none focus:ring-2 focus:ring-primary transition-all duration-200"
                />
            </div>

            <div className="border border-border rounded-xl overflow-hidden bg-card shadow-sm">
                <table className="min-w-full divide-y divide-border">
                    <thead className="bg-muted/50">
                        <tr>
                            <th className="px-6 py-4 text-left text-xs font-bold text-muted-foreground uppercase tracking-wider">ID</th>
                            <th className="px-6 py-4 text-left text-xs font-bold text-muted-foreground uppercase tracking-wider">Имя</th>
                            <th className="px-6 py-4 text-left text-xs font-bold text-muted-foreground uppercase tracking-wider">Телефон</th>
                            <th className="px-6 py-4 text-left text-xs font-bold text-muted-foreground uppercase tracking-wider">Авто</th>
                            <th className="px-6 py-4 text-left text-xs font-bold text-muted-foreground uppercase tracking-wider">Telegram ID</th>
                        </tr>
                    </thead>
                    <tbody className="divide-y divide-border bg-card">
                        {isLoading ? (
                            <tr>
                                <td colSpan={5} className="px-6 py-8 text-center text-sm text-muted-foreground">
                                    Загрузка...
                                </td>
                            </tr>
                        ) : filteredClients.length === 0 ? (
                            <tr>
                                <td colSpan={5} className="px-6 py-8 text-center text-sm text-muted-foreground">
                                    Клиенты не найдены
                                </td>
                            </tr>
                        ) : (
                            filteredClients.map((client) => (
                                <tr key={client.id} className="hover:bg-accent/5 transition-colors duration-150">
                                    <td className="px-6 py-4 whitespace-nowrap text-sm font-medium text-foreground">{client.id}</td>
                                    <td className="px-6 py-4 whitespace-nowrap text-sm text-muted-foreground">{client.full_name}</td>
                                    <td className="px-6 py-4 whitespace-nowrap text-sm text-muted-foreground">{client.phone}</td>
                                    <td className="px-6 py-4 whitespace-nowrap text-sm text-muted-foreground">{client.vehicle_info || '-'}</td>
                                    <td className="px-6 py-4 whitespace-nowrap text-sm text-muted-foreground">{client.telegram_id}</td>
                                </tr>
                            ))
                        )}
                    </tbody>
                </table>
            </div>
        </div>
    );
}
