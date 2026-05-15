const ELK = require('elkjs');
const fs = require('fs');
const path = require('path');

const elk = new ELK();

const tempDir = path.join(__dirname, '..', '..', 'temp');

const inputFile = path.join(tempDir, 'input_coordinates.json');
const outputFile = path.join(tempDir, 'output_coordinates.json');

if (!inputFile || !outputFile) {
    console.error("ERROR: Missing arguments! Usage: node run_elk.js <batch_in.json> <batch_out.json>");
    process.exit(1);
}

// --- NEW: Function to find and remove unused ports ---
function removeUnusedPorts(graph) {
    const usedPorts = new Set();

    // 1. Collect all ports actually used by the edges
    if (graph.edges) {
        graph.edges.forEach(edge => {
            if (edge.sourcePort) usedPorts.add(edge.sourcePort);
            if (edge.targetPort) usedPorts.add(edge.targetPort);
        });
    }

    // 2. Filter the ports array of each child node
    if (graph.children) {
        graph.children.forEach(node => {
            if (node.ports) {
                const originalCount = node.ports.length;
                // Keep only the ports that exist in the 'usedPorts' Set
                node.ports = node.ports.filter(port => usedPorts.has(port.id));
                
                // Optional: Log when a ghost port is removed
                if (node.ports.length !== originalCount) {
                    console.log(`[Sanitizer] Cleaned ${originalCount - node.ports.length} unused port(s) from node: ${node.id}`);
                }
            }
        });
    }
    
    return graph;
}
// -----------------------------------------------------

// 1. Read the array of configurations
let inputBatch = JSON.parse(fs.readFileSync(inputFile, 'utf8'));

if (!Array.isArray(inputBatch)) {
    inputBatch = [inputBatch];
}
// --------------------------------

// 2. Clean the input batch before giving it to ELK
const cleanedBatch = inputBatch.map(graph => removeUnusedPorts(graph));

// 3. Run ELK layout on the cleaned graphs
Promise.all(cleanedBatch.map(graph => elk.layout(graph)))
   .then(outputBatch => {
        // Salva il file di output per Python
       fs.writeFileSync(outputFile, JSON.stringify(outputBatch, null, 2));
       console.log("ELK Layout Complete.");
   })
   .catch(err => {
       console.error("ELK Batch Failed:", err);
       process.exit(1);
   });