import { google } from 'googleapis';

export type QuinielaRow = {
    partido: string;
    local: string;
    visitante: string;
    pronostico: string;
    razonamiento: string;
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
        const auth = new google.auth.GoogleAuth({
            credentials: JSON.parse(process.env.G_SHEETS_CREDENTIALS || '{}'),
            scopes: ['https://www.googleapis.com/auth/spreadsheets.readonly'],
        });

        const sheets = google.sheets({ version: 'v4', auth });

        // ID del Sheet (Debe estar en variable de entorno)
        const spreadsheetId = process.env.NEXT_PUBLIC_SHEET_ID;

        if (!spreadsheetId) {
            throw new Error("NEXT_PUBLIC_SHEET_ID no definido");
        }

        // Leer predicciones de la semana actual
        const responseSemana = await sheets.spreadsheets.values.get({
            spreadsheetId,
            range: 'Semana_Actual!A2:E20', // Asumiendo rango
        });

        const rowsSemana = responseSemana.data.values || [];
        const predicciones: QuinielaRow[] = rowsSemana.map((row: any) => ({
            partido: row[0],
            local: row[1],
            visitante: row[2],
            pronostico: row[3],
            razonamiento: row[4],
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
