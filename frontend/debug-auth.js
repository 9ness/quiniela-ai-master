const fs = require('fs');
const path = require('path');

// Mock variable loading (since we can't easily load .env.local in plain node without dotnet)
// We will try to read the file manually
function loadEnv() {
    try {
        const envPath = path.join(__dirname, '.env.local');
        if (fs.existsSync(envPath)) {
            const content = fs.readFileSync(envPath, 'utf8');
            const lines = content.split('\n');
            for (let line of lines) {
                if (line.startsWith('G_SHEETS_CREDENTIALS=')) {
                    let val = line.substring('G_SHEETS_CREDENTIALS='.length);
                    // Remove quotes if wrapped
                    if (val.startsWith("'") && val.endsWith("'")) val = val.slice(1, -1);
                    if (val.startsWith('"') && val.endsWith('"')) val = val.slice(1, -1);
                    return val;
                }
            }
        }
    } catch (e) {
        console.error("Error reading .env.local", e);
    }
    return null;
}

const jsonStr = loadEnv();

if (!jsonStr) {
    console.log("G_SHEETS_CREDENTIALS not found in .env.local");
} else {
    try {
        const creds = JSON.parse(jsonStr);
        console.log("Successfully parsed JSON.");
        console.log("Project ID:", creds.project_id);

        const key = creds.private_key;
        if (!key) {
            console.log("private_key is missing!");
        } else {
            console.log("Private Key First 30 chars:", key.substring(0, 30));
            console.log("Private Key Length:", key.length);
            console.log("Contains real newline (\\n char)?", key.includes('\n'));
            console.log("Contains literal backslash-n string?", key.includes('\\n'));

            // Simulate the fix
            const fixedKey = key.replace(/\\n/g, '\n');
            console.log("After .replace(/\\\\n/q, '\\n'):");
            console.log("Contains real newline?", fixedKey.includes('\n'));
            console.log("Contains literal backslash-n?", fixedKey.includes('\\n'));
        }
    } catch (e) {
        console.error("Error with JSON.parse:", e);
        console.log("Raw string start:", jsonStr.substring(0, 50));
    }
}
