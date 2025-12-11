import { getQuinielaData } from '@/lib/googleSheets';
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";

// Componente de Contador (Cliente) idealmente, pero aquí lo haremos simple o Server Component si es estático.
// Para interactividad real, debería ser 'use client'. Aquí simulamos Server Component con datos.

export const revalidate = 3600; // Revalidar cada hora

export default async function Home() {
    const { predicciones, estadisticas } = await getQuinielaData();

    // Calcular tiempo restante (Simplificado para render server-side)
    // Para un contador dinámico real, necesitaríamos un componente cliente.
    const nextFriday = new Date();
    nextFriday.setDate(nextFriday.getDate() + (5 + 7 - nextFriday.getDay()) % 7);
    nextFriday.setHours(14, 0, 0, 0);

    return (
        <main className="min-h-screen bg-slate-950 text-white p-4 md:p-8 font-sans">
            <div className="max-w-4xl mx-auto space-y-8">

                {/* Header */}
                <header className="text-center space-y-4">
                    <h1 className="text-4xl md:text-6xl font-bold bg-gradient-to-r from-emerald-400 to-cyan-400 bg-clip-text text-transparent">
                        Quiniela AI Master
                    </h1>
                    <p className="text-slate-400">Predicciones de fútbol impulsadas por Gemini Pro</p>
                </header>

                {/* Sección de Próxima Jornada / Contador */}
                <section className="grid md:grid-cols-2 gap-4">
                    <Card className="bg-slate-900 border-slate-800">
                        <CardHeader>
                            <CardTitle className="text-emerald-400">Próxima Jornada</CardTitle>
                        </CardHeader>
                        <CardContent>
                            <div className="text-3xl font-mono text-center py-4 text-white">
                                VIERNES 14:00
                            </div>
                            <p className="text-center text-sm text-slate-500">Cierre de apuestas estimado</p>
                        </CardContent>
                    </Card>

                    <Card className="bg-slate-900 border-slate-800">
                        <CardHeader>
                            <CardTitle className="text-blue-400">Acierto Global</CardTitle>
                        </CardHeader>
                        <CardContent>
                            <div className="text-3xl font-bold text-center py-4 text-white">
                                {estadisticas.length > 0 ? estadisticas[estadisticas.length - 1].porcentaje : "0%"}
                            </div>
                            <p className="text-center text-sm text-slate-500">Última jornada registrada</p>
                        </CardContent>
                    </Card>
                </section>

                {/* Predicciones */}
                <section>
                    <div className="flex items-center justify-between mb-4">
                        <h2 className="text-2xl font-bold text-white">Predicción Semanal</h2>
                        <Badge variant="outline" className="text-emerald-400 border-emerald-400">
                            IA Confidence: Alta
                        </Badge>
                    </div>

                    <div className="bg-slate-900 rounded-xl border border-slate-800 overflow-hidden">
                        <div className="grid grid-cols-12 bg-slate-800/50 p-4 text-sm font-semibold text-slate-300 border-b border-slate-800">
                            <div className="col-span-1 text-center">#</div>
                            <div className="col-span-5">Partido</div>
                            <div className="col-span-2 text-center">Pronóstico</div>
                            <div className="col-span-4">Razón IA</div>
                        </div>

                        {predicciones.length > 0 ? (
                            <div className="divide-y divide-slate-800/50">
                                {predicciones.map((p, idx) => (
                                    <div key={idx} className="grid grid-cols-12 p-4 items-center hover:bg-slate-800/30 transition-colors">
                                        <div className="col-span-1 text-center font-mono text-slate-500">{p.partido || idx + 1}</div>
                                        <div className="col-span-5 font-medium text-slate-200">
                                            <span className="block md:inline">{p.local}</span>
                                            <span className="hidden md:inline mx-2 text-slate-600">vs</span>
                                            <span className="block md:inline">{p.visitante}</span>
                                        </div>
                                        <div className="col-span-2 text-center">
                                            <span className="inline-block px-3 py-1 rounded bg-indigo-500/10 text-indigo-400 border border-indigo-500/20 font-bold">
                                                {p.pronostico}
                                            </span>
                                        </div>
                                        <div className="col-span-4 text-xs text-slate-400 italic">
                                            {p.razonamiento}
                                        </div>
                                    </div>
                                ))}
                            </div>
                        ) : (
                            <div className="p-8 text-center text-slate-500">
                                No hay predicciones disponibles para esta semana aún.
                            </div>
                        )}
                    </div>
                </section>

                {/* Historial Breve */}
                <section className="pt-8 opacity-70">
                    <h3 className="text-xl font-bold mb-4 text-slate-400">Últimos Resultados</h3>
                    <div className="grid gap-2">
                        {estadisticas.slice(-3).reverse().map((est, idx) => (
                            <div key={idx} className="flex justify-between items-center bg-slate-900/50 p-3 rounded border border-slate-800">
                                <span>Jornada {est.jornada}</span>
                                <span className="font-mono">{est.aciertos}/{est.total} ({est.porcentaje})</span>
                            </div>
                        ))}
                    </div>
                </section>
            </div>
        </main>
    );
}
