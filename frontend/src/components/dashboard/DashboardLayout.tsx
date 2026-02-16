import { Link, Outlet, useLocation } from "react-router-dom";
import { cn } from "@/lib/utils";
import {
    LayoutDashboard,
    CalendarDays,
    Settings,
    Users
} from "lucide-react";

export default function DashboardLayout() {
    const location = useLocation();

    const navItems = [
        { name: "Канбан", href: "/", icon: LayoutDashboard },
        { name: "Календарь", href: "/calendar", icon: CalendarDays },
        { name: "Клиенты", href: "/clients", icon: Users },
        { name: "Настройки", href: "/settings", icon: Settings },
    ];

    return (
        <div className="flex h-screen bg-gray-100 dark:bg-gray-900">
            {/* Sidebar */}
            <aside className="w-64 bg-white dark:bg-gray-800 border-r border-gray-200 dark:border-gray-700">
                <div className="h-16 flex items-center justify-center border-b border-gray-200 dark:border-gray-700">
                    <span className="text-xl font-bold text-gray-800 dark:text-white">Автосервис</span>
                </div>
                <nav className="p-4 space-y-2">
                    {navItems.map((item) => {
                        const Icon = item.icon;
                        const isActive = location.pathname === item.href;
                        return (
                            <Link
                                key={item.href}
                                to={item.href}
                                className={cn(
                                    "flex items-center px-4 py-2 text-sm font-medium rounded-md transition-colors",
                                    isActive
                                        ? "bg-primary/10 text-primary"
                                        : "text-gray-600 dark:text-gray-300 hover:bg-gray-50 dark:hover:bg-gray-700"
                                )}
                            >
                                <Icon className="mr-3 h-5 w-5" />
                                {item.name}
                            </Link>
                        );
                    })}
                </nav>
            </aside>

            {/* Main Content */}
            <main className="flex-1 overflow-auto">
                <header className="h-16 bg-white dark:bg-gray-800 border-b border-gray-200 dark:border-gray-700 flex items-center justify-between px-8">
                    <h1 className="text-xl font-semibold text-gray-800 dark:text-white">
                        {navItems.find(i => i.href === location.pathname)?.name || "Панель управления"}
                    </h1>
                    <div className="flex items-center space-x-4">
                        {/* User Menu placeholder */}
                        <div className="h-8 w-8 rounded-full bg-gray-200 dark:bg-gray-600"></div>
                    </div>
                </header>
                <div className="p-8">
                    <Outlet />
                </div>
            </main>
        </div>
    );
}
