import { useState } from "react";
import { Link, Outlet, useLocation } from "react-router-dom";
import { cn } from "@/lib/utils";
import {
    LayoutDashboard,
    CalendarDays,
    Settings,
    Users,
    LogOut,
    Menu,
    X
} from "lucide-react";
import { useAuth } from "@/contexts/AuthContext";


export default function DashboardLayout() {
    const location = useLocation();
    const { logout } = useAuth();
    const [isSidebarOpen, setIsSidebarOpen] = useState(false);

    const navItems = [
        { name: "Заказы", href: "/", icon: LayoutDashboard },
        { name: "Календарь", href: "/calendar", icon: CalendarDays },
        { name: "Клиенты", href: "/clients", icon: Users },
        { name: "Настройки", href: "/settings", icon: Settings },
    ];

    const closeSidebar = () => setIsSidebarOpen(false);

    return (
        <div className="flex h-screen bg-background overflow-hidden">
            {/* Mobile Sidebar Overlay */}
            {isSidebarOpen && (
                <div
                    className="fixed inset-0 bg-background/80 backdrop-blur-sm z-40 md:hidden"
                    onClick={closeSidebar}
                />
            )}

            {/* Sidebar */}
            <aside
                className={cn(
                    "fixed inset-y-0 left-0 z-50 w-64 bg-card border-r border-border transition-transform duration-300 ease-in-out md:relative md:translate-x-0",
                    isSidebarOpen ? "translate-x-0" : "-translate-x-full"
                )}
            >
                <div className="h-16 flex items-center justify-between px-6 border-b border-border">
                    <span className="text-xl font-bold text-foreground tracking-tighter">AUTOSERVICE</span>
                    <button onClick={closeSidebar} className="md:hidden text-muted-foreground hover:text-foreground">
                        <X size={24} />
                    </button>
                </div>
                <nav className="p-4 space-y-2">
                    {navItems.map((item) => {
                        const Icon = item.icon;
                        const isActive = location.pathname === item.href;
                        return (
                            <Link
                                key={item.href}
                                to={item.href}
                                onClick={closeSidebar}
                                className={cn(
                                    "flex items-center px-4 py-3 text-sm font-medium rounded-xl transition-all duration-200",
                                    isActive
                                        ? "bg-primary text-primary-foreground shadow-lg shadow-primary/25 translate-x-1"
                                        : "text-muted-foreground hover:bg-accent/10 hover:text-accent hover:translate-x-1"
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
            <div className="flex-1 flex flex-col min-w-0 overflow-hidden">
                <header className="h-16 bg-background/50 backdrop-blur-md border-b border-border flex items-center justify-between px-4 md:px-8 z-10">
                    <div className="flex items-center gap-4">
                        <button
                            className="md:hidden text-muted-foreground hover:text-foreground"
                            onClick={() => setIsSidebarOpen(true)}
                        >
                            <Menu size={24} />
                        </button>
                        <h1 className="text-lg md:text-xl font-bold text-foreground truncate">
                            {navItems.find(i => i.href === location.pathname)?.name || "Панель управления"}
                        </h1>
                    </div>

                    <div className="flex items-center space-x-2 md:space-x-4">
                        <button
                            onClick={logout}
                            className="flex items-center space-x-2 text-sm font-medium text-muted-foreground hover:text-destructive transition-colors px-3 py-2 rounded-lg hover:bg-destructive/10"
                        >
                            <span className="hidden md:inline">Выйти</span>
                            <LogOut size={18} />
                        </button>
                        <div className="h-8 w-8 md:h-9 md:w-9 rounded-full bg-gradient-to-tr from-primary to-accent shadow-inner"></div>
                    </div>
                </header>
                <main className="flex-1 overflow-auto p-4 md:p-8">
                    <Outlet />
                </main>
            </div>
        </div>
    );
}
