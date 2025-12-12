import { google } from 'googleapis';

export type QuinielaRow = {
    jornada: string;
    fecha: string;
    local: string;
    visitante: string;
    pronostico_logico: string;
    justificacion_logica: string;
    pronostico_sorpresa: string;
    justificacion_sorpresa: string;
};

export type StatsRow = {
    jornada: string;
    aciertos: string;
    total: string;
    porcentaje: string;
};

export async function getQuinielaData() {
    try {
        // Autenticación: En Vercel, configurar las vars de entorno
        // Se puede usar una Service Account o API Key si es público.
        // Aquí usamos Service Account estándar para lectura robusta.
        const creds = JSON.parse(process.env.G_SHEETS_CREDENTIALS || '{}');
        if (creds.private_key) {
            creds.private_key = creds.private_key.replace(/\\n/g, '\n');
        }

        const auth = new google.auth.GoogleAuth({
            credentials: creds,
            scopes: ['https://www.googleapis.com/auth/spreadsheets.readonly'],
        });

        const sheets = google.sheets({ version: 'v4', auth });

        // ID del Sheet (Debe estar en variable de entorno)
        const spreadsheetId = process.env.NEXT_PUBLIC_SHEET_ID;

        if (!spreadsheetId) {
            throw new Error("NEXT_PUBLIC_SHEET_ID no definido");
        }

        // Leer predicciones de la semana actual (Rango ampliado A:H)
        const responseSemana = await sheets.spreadsheets.values.get({
            spreadsheetId,
            range: 'Semana_Actual!A2:H20',
        });

        const rowsSemana = responseSemana.data.values || [];
        const predicciones: QuinielaRow[] = rowsSemana.map((row: any) => ({
            jornada: row[0],
            fecha: row[1],
            local: row[2],
            visitante: row[3],
            pronostico_logico: row[4],
            justificacion_logica: row[5],
            pronostico_sorpresa: row[6],
            justificacion_sorpresa: row[7],
        }));

        // Leer estadísticas si es necesario
        const responseHist = await sheets.spreadsheets.values.get({
            spreadsheetId,
            range: 'Historial!A2:D10', // Últimas 10 jornadas
        });

        const rowsHist = responseHist.data.values || [];
        const estadisticas: StatsRow[] = rowsHist.map((row: any) => ({
            jornada: row[0],
            aciertos: row[1],
            total: row[2],
            porcentaje: row[3],
        }));

        return { predicciones, estadisticas };

    } catch (error) {
        console.error("Error fetching sheet data:", error);
        return { predicciones: [], estadisticas: [] };
    }
}
