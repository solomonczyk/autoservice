import KanbanBoard from "@/components/dashboard/KanbanBoard";

export default function KanbanPage() {
    return (
        <div className="space-y-4">
            <div className="flex justify-between items-center">
                <h2 className="text-2xl font-bold">Kanban Board</h2>
            </div>
            <KanbanBoard />
        </div>
    )
}
