import { useMutation, useQueryClient } from '@tanstack/react-query';
import { api } from '@/lib/api';

export function useUpdateAppointmentStatus() {
    const queryClient = useQueryClient();

    return useMutation({
        mutationFn: async ({ id, status }: { id: number; status: string }) => {
            const response = await api.patch(`/appointments/${id}/status`, { status });
            return response.data;
        },
        onSuccess: () => {
            // Invalidate and refetch appointments to sync UI
            queryClient.invalidateQueries({ queryKey: ['appointments'] });
        },
        onError: (error) => {
            console.error('Failed to update appointment status:', error);
        },
    });
}
