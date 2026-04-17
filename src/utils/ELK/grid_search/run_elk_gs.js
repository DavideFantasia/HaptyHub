const ELK = require('elkjs');
const fs = require('fs');

const elk = new ELK();

const inputFile = process.argv[2];
const outputFile = process.argv[3];

if (!inputFile || !outputFile) {
    console.error("ERROR: Missing arguments! Usage: node run_elk_gs.js <batch_in.json> <batch_out.json>");
    process.exit(1);
}

// 1. Read the array of configurations
let inputBatch = JSON.parse(fs.readFileSync(inputFile, 'utf8'));

if (!Array.isArray(inputBatch)) {
    inputBatch = [inputBatch];
}
// --------------------------------

Promise.all(inputBatch.map(graph => elk.layout(graph)))
   .then(outputBatch => {
       // 3. Save the giant array of finished results back to Python
       fs.writeFileSync(outputFile, JSON.stringify(outputBatch, null, 2));
   })
   .catch(err => {
       console.error("ELK Batch Failed:", err);
       process.exit(1); 
   });