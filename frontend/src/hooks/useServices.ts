import { useQuery } from "@tanstack/react-query";
import { api } from "@/lib/api";

export interface Service {
    id: number;
    name: string;
    duration_minutes: number;
    base_price: number;
}

export function useServices() {
    return useQuery({
        queryKey: ["services"],
        queryFn: async () => {
            const { data } = await api.get<Service[]>("/services/");
            return data;
        },
    });
}
