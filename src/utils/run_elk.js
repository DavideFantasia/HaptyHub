const ELK = require('elkjs');
const fs = require('fs');
const elk = new ELK();

const outputFile = process.argv[2];

if (!outputFile) {
    console.error("ERROR: Missing arguments! Usage: node run_elk.js <output_file.json>");
    process.exit(1);
}

let rawData = '';

// Imposta la codifica per leggere i dati come testo
process.stdin.setEncoding('utf8');

// 1. Accumula i chunk di dati inviati da Python man mano che arrivano
process.stdin.on('data', chunk => {
    rawData += chunk;
});

// 2. Quando Python ha finito di inviare i dati e chiude il "tubo"
process.stdin.on('end', () => {
    try {
        let inputBatch = JSON.parse(rawData);

        if (!Array.isArray(inputBatch)) {
            inputBatch = [inputBatch];
        }

        // 3. Esegue ELK
        Promise.all(inputBatch.map(graph => elk.layout(graph)))
        .then(outputBatch => {
            // Salva il file di output per Python
            fs.writeFileSync(outputFile, JSON.stringify(outputBatch, null, 2));
        })
        .catch(err => {
            console.error("ELK Batch Failed:", err);
            process.exit(1);
        });

    } catch (err) {
        console.error("Error parsing JSON from stdin:", err);
        process.exit(1);
    }
});

// Gestione di sicurezza in caso di errori di connessione sul tubo
process.stdin.on('error', err => {
    console.error("Stream read error:", err);
    process.exit(1);
});