import React from 'react';
import {
    Trophy,
    Calendar,
    ArrowRight,
    Activity,
    ShieldCheck,
    TrendingUp,
    Clock
} from 'lucide-react';
import { getQuinielaData } from '@/lib/googleSheets';
import { ThemeToggle } from '@/components/ThemeToggle';
import { CountdownSection } from '@/components/CountdownSection';

export const revalidate = 60; // Revalidar cada 60s

export default async function Home() {
    let data = null;

    // Fetch seguro en el servidor
    try {
        const rawData = await getQuinielaData();
        // Verificamos si hay predicciones válidas
        if (rawData && rawData.predicciones && rawData.predicciones.length > 0) {
            data = rawData.predicciones;
        }
    } catch (error) {
        console.error("Error fetching Quiniela data in server:", error);
        // Silent fail, UI will show 'Processing' state
    }

    return (
        <main className="min-h-screen bg-background text-foreground transition-colors duration-300">

            {/* Navbar */}
            <nav className="border-b border-border bg-background/80 backdrop-blur-md sticky top-0 z-50">
                <div className="max-w-6xl mx-auto px-4 h-16 flex items-center justify-between">
                    <div className="flex items-center gap-2">
                        <div className="bg-gradient-to-tr from-emerald-500 to-cyan-500 p-2 rounded-lg text-white shadow-lg shadow-emerald-500/20">
                            <Trophy size={20} strokeWidth={2.5} />
                        </div>
                        <span className="font-bold text-xl tracking-tight">
                            QUINIELA <span className="text-primary">AI</span>
                        </span>
                    </div>
                    <ThemeToggle />
                </div>
            </nav>

            {/* Hero Section */}
            <div className="relative overflow-hidden border-b border-border">
                {/* Background blobs */}
                <div className="absolute top-0 left-1/4 w-96 h-96 bg-primary/20 rounded-full blur-[128px] pointer-events-none opacity-50" />
                <div className="absolute bottom-0 right-1/4 w-96 h-96 bg-cyan-500/20 rounded-full blur-[128px] pointer-events-none opacity-50" />

                <div className="max-w-4xl mx-auto px-4 py-16 md:py-24 text-center relative z-10">
                    <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-secondary text-secondary-foreground text-sm font-medium mb-6 hover:bg-secondary/80 transition-colors cursor-default">
                        <Activity size={14} className="text-primary animate-pulse" />
                        <span>Sistema predictivo activo</span>
                    </div>

                    <h1 className="text-5xl md:text-7xl font-black mb-6 tracking-tight leading-tight">
                        Predicciones de Fútbol <br className="hidden md:block" />
                        <span className="text-transparent bg-clip-text bg-gradient-to-r from-emerald-400 via-cyan-500 to-emerald-500 bg-300% animate-gradient">
                            Inteligentes
                        </span>
                    </h1>

                    <p className="text-xl text-muted-foreground max-w-2xl mx-auto mb-10 leading-relaxed">
                        Nuestra IA analiza miles de datos históricos para generar la Quiniela perfecta.
                        Anticípate a los resultados de la próxima jornada.
                    </p>

                    <CountdownSection />
                </div>
            </div>

            {/* Current Quiniela Section */}
            <section className="max-w-5xl mx-auto px-4 py-20">
                <div className="flex items-center justify-between mb-8">
                    <div className="flex items-center gap-3">
                        <Calendar className="text-primary w-6 h-6" />
                        <h2 className="text-2xl font-bold">Quiniela de la Jornada</h2>
                    </div>
                    <div className="text-sm text-muted-foreground flex items-center gap-2">
                        <Clock size={14} /> Cierre: Viernes 21:00
                    </div>
                </div>

                {!data ? (
                    /* Empty State (Processing) */
                    <div className="bg-card border border-border rounded-3xl p-12 md:p-20 text-center shadow-xl relative overflow-hidden group hover:border-primary/50 transition-colors">
                        <div className="absolute inset-0 bg-gradient-to-b from-transparent to-primary/5 opacity-0 group-hover:opacity-100 transition-opacity" />

                        <div className="relative z-10">
                            <div className="w-20 h-20 bg-secondary rounded-full flex items-center justify-center mx-auto mb-6">
                                <TrendingUp className="w-10 h-10 text-primary" />
                            </div>
                            <h3 className="text-3xl font-bold mb-3">Generando Pronósticos</h3>
                            <p className="text-muted-foreground max-w-md mx-auto mb-8">
                                La Inteligencia Artificial está procesando los datos de la jornada actual.
                                Los resultados estarán disponibles próximamente.
                            </p>
                            <button className="px-6 py-3 bg-primary text-primary-foreground font-bold rounded-xl hover:bg-primary/90 transition-all flex items-center gap-2 mx-auto shadow-lg shadow-primary/25">
                                Notificarme cuando esté listo <ArrowRight size={18} />
                            </button>
                        </div>
                    </div>
                ) : (
                    /* Data Table */
                    <div className="bg-card border border-border rounded-3xl overflow-hidden shadow-2xl animate-in slide-in-from-bottom-5 duration-700">
                        {/* Headers */}
                        <div className="grid grid-cols-12 bg-secondary/50 p-4 font-semibold text-muted-foreground text-sm uppercase tracking-wider border-b border-border">
                            <div className="col-span-1 text-center">#</div>
                            <div className="col-span-5 md:col-span-5">Partido</div>
                            <div className="col-span-3 text-center text-emerald-500 font-bold">Lógica</div>
                            <div className="col-span-3 text-center text-amber-500 font-bold">Sorpresa</div>
                        </div>
                        {/* Rows */}
                        <div className="divide-y divide-border">
                            {data.map((row: any, i: number) => (
                                <div key={i} className="grid grid-cols-12 p-4 items-center hover:bg-secondary/30 transition-colors group">
                                    <div className="col-span-1 text-center font-mono text-muted-foreground group-hover:text-primary">{i + 1}</div>
                                    <div className="col-span-5 md:col-span-5 font-medium flex flex-col justify-center">
                                        <div className="text-base md:text-lg leading-tight">{row.local}</div>
                                        <div className="text-xs text-muted-foreground my-0.5">vs</div>
                                        <div className="text-base md:text-lg leading-tight">{row.visitante}</div>
                                        {/* Date hint if needed: <span className="text-[10px] text-muted-foreground mt-1">{row.fecha}</span> */}
                                    </div>

                                    {/* Lógica */}
                                    <div className="col-span-3 flex justify-center">
                                        <div className="flex flex-col items-center group/tooltip relative">
                                            <span className="inline-flex w-10 h-10 items-center justify-center rounded-xl bg-emerald-500/10 text-emerald-500 font-black text-lg border border-emerald-500/20 shadow-sm transition-transform group-hover:scale-110">
                                                {row.pronostico_logico}
                                            </span>
                                            {/* Tooltip simple para justificación */}
                                            {row.justificacion_logica && (
                                                <div className="absolute bottom-full mb-2 w-48 p-2 bg-popover text-popover-foreground text-xs rounded shadow-lg opacity-0 invisible group-hover/tooltip:opacity-100 group-hover/tooltip:visible transition-all z-20 pointer-events-none">
                                                    {row.justificacion_logica}
                                                </div>
                                            )}
                                        </div>
                                    </div>

                                    {/* Sorpresa */}
                                    <div className="col-span-3 flex justify-center">
                                        <div className="flex flex-col items-center group/tooltip relative">
                                            <span className="inline-flex w-10 h-10 items-center justify-center rounded-xl bg-amber-500/10 text-amber-500 font-black text-lg border border-amber-500/20 shadow-sm transition-transform group-hover:scale-110">
                                                {row.pronostico_sorpresa}
                                            </span>
                                            {/* Tooltip simple para justificación */}
                                            {row.justificacion_sorpresa && (
                                                <div className="absolute bottom-full mb-2 w-48 p-2 bg-popover text-popover-foreground text-xs rounded shadow-lg opacity-0 invisible group-hover/tooltip:opacity-100 group-hover/tooltip:visible transition-all z-20 pointer-events-none">
                                                    {row.justificacion_sorpresa}
                                                </div>
                                            )}
                                        </div>
                                    </div>
                                </div>
                            ))}
                        </div>
                    </div>
                )}
            </section>

            {/* Footer */}
            <footer className="py-8 text-center text-muted-foreground text-sm border-t border-border bg-card">
                <div className="flex items-center justify-center gap-2 mb-2">
                    <ShieldCheck size={16} className="text-primary" />
                    <span>Datos verificados y seguros</span>
                </div>
                <p>© {new Date().getFullYear()} Quiniela AI Master. Powered by Google Gemini.</p>
            </footer>
        </main>
    );
}
