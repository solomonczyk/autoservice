import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { api } from "@/lib/api";

export interface Appointment {
    id: number;
    shop_id: number;
    service_id: number;
    client_id: number;
    start_time: string;
    end_time: string;
    status: "new" | "confirmed" | "in_progress" | "done" | "cancelled";
}

export function useAppointments() {
    return useQuery({
        queryKey: ["appointments"],
        queryFn: async () => {
            const { data } = await api.get<Appointment[]>("/appointments/");
            return data;
        },
    });
}

export function useUpdateAppointmentStatus() {
    const queryClient = useQueryClient();

    return useMutation({
        mutationFn: async ({ id, status }: { id: number; status: string }) => {
            return api.patch(`/appointments/${id}/status`, { status });
        },
        onSuccess: () => {
            queryClient.invalidateQueries({ queryKey: ["appointments"] });
        },
    });
}
