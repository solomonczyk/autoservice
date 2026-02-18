import { useState } from "react";
import { useAuth } from "@/contexts/AuthContext";
import { useNavigate } from "react-router-dom";
import { api } from "@/lib/api";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";

export default function LoginPage() {
    const [username, setUsername] = useState("");
    const [password, setPassword] = useState("");
    const [error, setError] = useState("");
    const { login } = useAuth();
    const navigate = useNavigate();

    const handleSubmit = async (e: React.FormEvent) => {
        e.preventDefault();
        setError("");

        try {
            const formData = new FormData();
            formData.append("username", username);
            formData.append("password", password);

            const response = await api.post("/login/access-token", formData, {
                headers: { "Content-Type": "application/x-www-form-urlencoded" }
            });

            login(response.data.access_token);
            navigate("/");
        } catch (err) {
            setError("Неверное имя пользователя или пароль");
        }
    };

    return (
        <div className="flex items-center justify-center min-h-screen bg-slate-100 dark:bg-slate-900">
            <Card className="w-[350px]">
                <CardHeader>
                    <CardTitle>Вход</CardTitle>
                </CardHeader>
                <CardContent>
                    <form onSubmit={handleSubmit} className="space-y-4">
                        <div className="space-y-2">
                            <label className="text-sm font-medium">Имя пользователя</label>
                            <input
                                className="flex h-10 w-full rounded-md border border-input bg-background px-3 py-2 text-sm ring-offset-background placeholder:text-muted-foreground/50"
                                value={username}
                                onChange={e => setUsername(e.target.value)}
                                required
                                placeholder="Например: admin"
                            />
                        </div>
                        <div className="space-y-2">
                            <label className="text-sm font-medium">Пароль</label>
                            <input
                                type="password"
                                className="flex h-10 w-full rounded-md border border-input bg-background px-3 py-2 text-sm ring-offset-background placeholder:text-muted-foreground/50"
                                value={password}
                                onChange={e => setPassword(e.target.value)}
                                required
                                placeholder="Ваш пароль"
                            />
                        </div>
                        {error && <div className="text-red-500 text-sm">{error}</div>}
                        <Button type="submit" className="w-full">Войти</Button>
                    </form>
                </CardContent>
            </Card>
        </div>
    );
}
