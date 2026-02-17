import { Link, Outlet, useLocation } from "react-router-dom";
import { cn } from "@/lib/utils";
import {
    LayoutDashboard,
    CalendarDays,
    Settings,
    Users,
    LogOut
} from "lucide-react";
import { useAuth } from "@/contexts/AuthContext";

export default function DashboardLayout() {
    const location = useLocation();
    const { logout } = useAuth();

    const navItems = [
        { name: "Заказы", href: "/", icon: LayoutDashboard },
        { name: "Календарь", href: "/calendar", icon: CalendarDays },
        { name: "Клиенты", href: "/clients", icon: Users },
        { name: "Настройки", href: "/settings", icon: Settings },
    ];

    return (
        <div className="flex h-screen bg-background">
            {/* Sidebar */}
            <aside className="w-64 bg-card border-r border-border">
                <div className="h-16 flex items-center justify-center border-b border-border">
                    <span className="text-xl font-bold text-foreground tracking-tighter">AUTOSERVICE</span>
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
            <main className="flex-1 overflow-auto">
                <header className="h-16 bg-background/50 backdrop-blur-md border-b border-border sticky top-0 z-10 flex items-center justify-between px-8">
                    <h1 className="text-xl font-bold text-foreground">
                        {navItems.find(i => i.href === location.pathname)?.name || "Панель управления"}
                    </h1>
                    <div className="flex items-center space-x-4">
                        <button
                            onClick={logout}
                            className="flex items-center space-x-2 text-sm font-medium text-muted-foreground hover:text-destructive transition-colors px-3 py-2 rounded-lg hover:bg-destructive/10"
                        >
                            <span className="hidden md:inline">Выйти</span>
                            <LogOut size={18} />
                        </button>
                        <div className="h-9 w-9 rounded-full bg-gradient-to-tr from-primary to-accent shadow-inner"></div>
                    </div>
                </header>
                <div className="p-8">
                    <Outlet />
                </div>
            </main>
        </div>
    );
}
