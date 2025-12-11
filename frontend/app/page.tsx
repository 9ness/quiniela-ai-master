import React from 'react';
import { Calendar, TrendingUp, ShieldCheck } from 'lucide-react';
// IMPORTANTE: Ruta relativa corregida
import { getQuinielaData } from '../lib/googleSheets';

export default async function Home() {
    // Intentamos obtener datos, si falla (por falta de credenciales en build) usamos null
    let data = null;
    try {
        data = await getQuinielaData();
    } catch (e) {
        console.log("Modo sin datos activado");
    }

    return (
        <div className="min-h-screen bg-slate-950 text-white font-sans">
            <header className="border-b border-slate-800 bg-slate-900/50 sticky top-0 z-10 p-4">
                <div className="max-w-4xl mx-auto flex items-center gap-2">
                    <div className="p-2 bg-emerald-600 rounded-lg">
                        <TrendingUp size={20} />
                    </div>
                    <h1 className="text-xl font-bold bg-clip-text text-transparent bg-gradient-to-r from-emerald-400 to-cyan-500">
                        Quiniela AI
                    </h1>
                </div>
            </header>

            <main className="max-w-4xl mx-auto px-4 py-12 text-center">
                {!data ? (
                    <div className="bg-slate-900 border border-slate-800 p-8 rounded-2xl max-w-md mx-auto mt-10">
                        <Calendar className="w-16 h-16 text-emerald-400 mx-auto mb-4" />
                        <h2 className="text-2xl font-bold mb-2">Próxima Quiniela</h2>
                        <p className="text-slate-400 mb-6">La IA está analizando los partidos. Resultados el viernes.</p>
                        <div className="text-3xl font-mono font-bold text-white bg-slate-950 p-4 rounded-xl border border-slate-800">
                            PRÓXIMAMENTE
                        </div>
                    </div>
                ) : (
                    <div className="text-emerald-400 p-4 border border-emerald-900 bg-emerald-950/30 rounded-lg">
                        ¡Datos cargados correctamente!
                    </div>
                )}

                <p className="text-slate-600 mt-12 flex justify-center gap-2 items-center text-sm">
                    <ShieldCheck size={14} /> Powered by Gemini Pro
                </p>
            </main>
        </div>
    );
}
