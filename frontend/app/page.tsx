import { getQuinielaData } from '@/lib/googleSheets';
import Countdown from '@/components/Countdown';
import { Brain, Calendar, Trophy, AlertTriangle, CheckCircle2 } from 'lucide-react';
import { Badge } from "@/components/ui/badge";

export const revalidate = 60; // Revalidar cada 60 segundos para desarrollo, ajustar en prod

export default async function Home() {
    let predicciones = [];
    let estadisticas = [];
    let error = null;

    try {
        const data = await getQuinielaData();
        predicciones = data.predicciones || [];
        estadisticas = data.estadisticas || [];
    } catch (e) {
        console.error("Error cargando datos:", e);
        error = "No se pudieron conectar los servicios de IA.";
    }

    // Calcular fecha próximo viernes 14:00
    const now = new Date();
    const nextFriday = new Date();
    nextFriday.setDate(now.getDate() + (5 + 7 - now.getDay()) % 7);
    nextFriday.setHours(14, 0, 0, 0);
    if (now > nextFriday) {
        nextFriday.setDate(nextFriday.getDate() + 7);
    }
    const targetDateISO = nextFriday.toISOString();

    // Determinar estado de la UI
    const hasData = predicciones.length > 0;
    const currentWeek = estadisticas.length > 0 ? parseInt(estadisticas[estadisticas.length - 1].jornada) + 1 : 1;

    return (
        <main className="min-h-screen bg-[#030712] text-slate-200 selection:bg-emerald-500/30">

            {/* Background Gradients */}
            <div className="fixed inset-0 z-0 pointer-events-none">
                <div className="absolute top-[-10%] left-[-10%] w-[40%] h-[40%] bg-emerald-500/10 rounded-full blur-[120px]" />
                <div className="absolute bottom-[-10%] right-[-10%] w-[40%] h-[40%] bg-indigo-500/10 rounded-full blur-[120px]" />
            </div>

            <div className="relative z-10 max-w-5xl mx-auto px-6 py-12 flex flex-col min-h-screen">

                {/* Header */}
                <header className="text-center mb-16 space-y-6">
                    <div className="inline-flex items-center justify-center p-3 bg-white/5 rounded-2xl ring-1 ring-white/10 mb-4 shadow-2xl backdrop-blur-md">
                        <Brain className="w-8 h-8 text-emerald-400 mr-3" />
                        <h1 className="text-4xl md:text-6xl font-black tracking-tight text-white">
                            <span className="bg-gradient-to-r from-white via-emerald-200 to-emerald-500 bg-clip-text text-transparent">
                                Quiniela AI
                            </span>
                        </h1>
                    </div>

                    <div className="flex items-center justify-center gap-3 text-slate-400 font-medium">
                        <Calendar className="w-4 h-4" />
                        <span className="uppercase tracking-widest text-sm">
                            {hasData ? `Jornada ${currentWeek} • Datos Activos` : "Próxima Jornada Estimada"}
                        </span>
                    </div>
                </header>

                {/* Content Area */}
                <div className="flex-grow space-y-12">

                    {/* Error Banner if any */}
                    {error && (
                        <div className="bg-red-500/10 border border-red-500/20 rounded-xl p-4 flex items-center text-red-400">
                            <AlertTriangle className="w-5 h-5 mr-3" />
                            <span>{error}</span>
                        </div>
                    )}

                    {/* MAIN VISUAL: Countdown OR Data */}
                    {!hasData ? (
                        <div className="animate-in fade-in zoom-in duration-700">
                            <div className="text-center mb-8">
                                <h2 className="text-2xl font-bold text-white mb-2">Preparando Predicciones...</h2>
                                <p className="text-slate-500">La IA está analizando los últimos datos. Vuelve pronto.</p>
                            </div>
                            <Countdown targetDate={targetDateISO} />
                        </div>
                    ) : (
                        <div className="space-y-8 animate-in slide-in-from-bottom-5 duration-500">

                            {/* Stats Summary */}
                            <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                                <div className="bg-slate-900/50 border border-slate-800 p-6 rounded-2xl backdrop-blur-sm">
                                    <div className="text-slate-500 text-sm font-medium mb-1 flex items-center gap-2">
                                        <Trophy className="w-4 h-4 text-emerald-500" /> Rendimiento
                                    </div>
                                    <div className="text-2xl font-bold text-white">
                                        {estadisticas.length > 0 ? estadisticas[estadisticas.length - 1].porcentaje : "N/A"}
                                    </div>
                                </div>
                                {/* Más stats placeholders si se quiere */}
                            </div>

                            {/* Predictions Table */}
                            <div className="bg-slate-900/40 rounded-3xl border border-white/5 overflow-hidden backdrop-blur-md shadow-2xl">
                                <div className="grid grid-cols-12 bg-white/5 p-5 text-xs font-bold text-slate-400 uppercase tracking-wider border-b border-white/5">
                                    <div className="col-span-1 text-center">#</div>
                                    <div className="col-span-11 md:col-span-5">Encuentro</div>
                                    <div className="col-span-12 md:col-span-2 text-center mt-2 md:mt-0">Pronóstico</div>
                                    <div className="col-span-12 md:col-span-4 mt-2 md:mt-0">Análisis IA</div>
                                </div>

                                <div className="divide-y divide-white/5">
                                    {predicciones.map((p, idx) => (
                                        <div key={idx} className="grid grid-cols-12 p-5 items-center hover:bg-white/[0.02] transition-colors group">
                                            <div className="col-span-1 text-center font-mono text-slate-600 group-hover:text-emerald-500 transition-colors">
                                                {p.partido}
                                            </div>

                                            <div className="col-span-11 md:col-span-5 font-medium text-slate-200 flex flex-col md:block">
                                                <span className="text-lg md:text-base">{p.local}</span>
                                                <span className="text-xs text-slate-600 md:mx-2 my-1 md:my-0 uppercase font-bold">VS</span>
                                                <span className="text-lg md:text-base">{p.visitante}</span>
                                            </div>

                                            <div className="col-span-12 md:col-span-2 text-center py-2 md:py-0">
                                                <Badge className="bg-emerald-500/10 text-emerald-400 border-emerald-500/20 hover:bg-emerald-500/20 text-md px-4 py-1">
                                                    {p.pronostico}
                                                </Badge>
                                            </div>

                                            <div className="col-span-12 md:col-span-4 text-sm text-slate-500 leading-relaxed font-light group-hover:text-slate-400 transition-colors">
                                                {p.razonamiento}
                                            </div>
                                        </div>
                                    ))}
                                </div>
                            </div>
                        </div>
                    )}

                </div>

                {/* Footer */}
                <footer className="mt-20 pt-8 border-t border-white/5 text-center">
                    <p className="text-slate-600 text-sm flex items-center justify-center gap-2">
                        Powered by <Brain className="w-4 h-4" /> Google Gemini Pro
                    </p>
                </footer>

            </div>
        </main>
    );
}
